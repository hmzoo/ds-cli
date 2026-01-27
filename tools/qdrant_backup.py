"""
Gestionnaire de backups pour Qdrant Memory
Permet de sauvegarder et restaurer la mémoire de l'agent
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from qdrant_client import QdrantClient


def backup_qdrant(
    qdrant_url: str = None,
    collection_name: str = None,
    backup_dir: str = "./backups"
) -> Dict:
    """
    Sauvegarde une collection Qdrant en JSON
    
    Args:
        qdrant_url: URL du serveur Qdrant
        collection_name: Nom de la collection
        backup_dir: Répertoire de sauvegarde
        
    Returns:
        Dict avec succès, chemin du backup, statistiques
    """
    qdrant_url = qdrant_url or os.getenv("QDRANT_ENDPOINT", "http://172.16.20.90:6333")
    collection_name = collection_name or os.getenv("QDRANT_COLLECTION_NAME", "deepseek_collection")
    
    try:
        # Créer le répertoire de backup
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Connexion Qdrant
        client = QdrantClient(url=qdrant_url)
        
        # Récupérer tous les points
        all_points = []
        offset = None
        
        while True:
            result = client.scroll(
                collection_name=collection_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )
            
            points, next_offset = result
            
            if not points:
                break
                
            for point in points:
                all_points.append({
                    "id": str(point.id),
                    "vector": point.vector,
                    "payload": point.payload
                })
            
            if next_offset is None:
                break
            offset = next_offset
        
        # Créer le fichier de backup avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"qdrant_backup_{collection_name}_{timestamp}.json"
        
        # Sauvegarder
        backup_data = {
            "metadata": {
                "collection_name": collection_name,
                "timestamp": datetime.now().isoformat(),
                "qdrant_url": qdrant_url,
                "total_points": len(all_points)
            },
            "points": all_points
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        # Statistiques par type
        stats = {}
        for point in all_points:
            point_type = point['payload'].get('type', 'unknown')
            stats[point_type] = stats.get(point_type, 0) + 1
        
        return {
            "success": True,
            "backup_file": str(backup_file),
            "total_points": len(all_points),
            "file_size": backup_file.stat().st_size,
            "statistics": stats,
            "timestamp": timestamp
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def restore_qdrant(
    backup_file: str,
    qdrant_url: str = None,
    collection_name: str = None,
    clear_existing: bool = False
) -> Dict:
    """
    Restaure une collection Qdrant depuis un backup
    
    Args:
        backup_file: Chemin du fichier de backup
        qdrant_url: URL du serveur Qdrant
        collection_name: Nom de la collection (None = utiliser celle du backup)
        clear_existing: Effacer la collection avant restauration
        
    Returns:
        Dict avec succès et statistiques
    """
    qdrant_url = qdrant_url or os.getenv("QDRANT_ENDPOINT", "http://172.16.20.90:6333")
    
    try:
        # Charger le backup
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        metadata = backup_data['metadata']
        points = backup_data['points']
        
        # Utiliser le nom de collection du backup si non spécifié
        target_collection = collection_name or metadata['collection_name']
        
        # Connexion Qdrant
        client = QdrantClient(url=qdrant_url)
        
        # Vérifier que la collection existe
        try:
            client.get_collection(target_collection)
        except Exception:
            return {
                "success": False,
                "error": f"Collection {target_collection} n'existe pas"
            }
        
        # Effacer si demandé
        if clear_existing:
            # Supprimer tous les points
            client.delete(
                collection_name=target_collection,
                points_selector={"filter": {}}  # Match all
            )
        
        # Restaurer les points par batch
        from qdrant_client.models import PointStruct
        batch_size = 100
        restored = 0
        
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            point_structs = []
            
            for point in batch:
                point_structs.append(PointStruct(
                    id=point['id'],
                    vector=point['vector'],
                    payload=point['payload']
                ))
            
            client.upsert(
                collection_name=target_collection,
                points=point_structs
            )
            restored += len(point_structs)
        
        return {
            "success": True,
            "collection": target_collection,
            "points_restored": restored,
            "backup_timestamp": metadata['timestamp'],
            "cleared_existing": clear_existing
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def list_backups(backup_dir: str = "./backups") -> List[Dict]:
    """
    Liste tous les backups disponibles
    
    Args:
        backup_dir: Répertoire des backups
        
    Returns:
        Liste des backups avec métadonnées
    """
    backup_path = Path(backup_dir)
    
    if not backup_path.exists():
        return []
    
    backups = []
    for file in backup_path.glob("qdrant_backup_*.json"):
        try:
            # Lire les métadonnées
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get('metadata', {})
            backups.append({
                "file": str(file),
                "filename": file.name,
                "size": file.stat().st_size,
                "timestamp": metadata.get('timestamp'),
                "collection": metadata.get('collection_name'),
                "total_points": metadata.get('total_points', 0),
                "created": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })
        except Exception:
            continue
    
    # Trier par date (plus récent d'abord)
    backups.sort(key=lambda x: x['created'], reverse=True)
    
    return backups


def get_backup_stats(backup_file: str) -> Dict:
    """
    Obtient les statistiques d'un backup
    
    Args:
        backup_file: Chemin du fichier de backup
        
    Returns:
        Statistiques détaillées
    """
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        points = data.get('points', [])
        
        # Analyser les types
        type_counts = {}
        category_counts = {}
        
        for point in points:
            payload = point.get('payload', {})
            
            # Type
            point_type = payload.get('type', 'unknown')
            type_counts[point_type] = type_counts.get(point_type, 0) + 1
            
            # Catégorie (pour les faits)
            if point_type == 'fact':
                category = payload.get('category', 'general')
                category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "success": True,
            "metadata": data.get('metadata', {}),
            "total_points": len(points),
            "types": type_counts,
            "categories": category_counts
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
