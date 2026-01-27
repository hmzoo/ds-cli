"""
Outils de mémoire pour l'agent DeepSeek avec Qdrant
Utilise Qdrant pour la mémoire vectorielle sémantique
"""

import os
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer


class QdrantMemory:
    """Système de mémoire vectorielle basé sur Qdrant avec embeddings sémantiques"""
    
    def __init__(self, 
                 qdrant_url: Optional[str] = None,
                 collection_name: Optional[str] = None,
                 model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialise le système de mémoire Qdrant
        
        Args:
            qdrant_url: URL du serveur Qdrant
            collection_name: Nom de la collection
            model_name: Modèle sentence-transformers à utiliser
        """
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_ENDPOINT", "http://172.16.20.90:6333")
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION_NAME", "deepseek_collection")
        
        # Client Qdrant
        self.client = QdrantClient(url=self.qdrant_url)
        
        # Modèle d'embeddings sémantiques
        print(f"🔄 Chargement du modèle {model_name}...")
        # Détecter le device disponible (CUDA si disponible, sinon CPU)
        # Utiliser une approche robuste pour éviter les blocages CUDA dans WSL
        device = 'cpu'  # Par défaut
        try:
            import torch
            # Vérifier si CUDA_VISIBLE_DEVICES est défini (meilleure approche pour WSL)
            cuda_devices = os.getenv('CUDA_VISIBLE_DEVICES')
            if cuda_devices is not None and cuda_devices != '':
                # Tenter d'utiliser CUDA seulement si explicitement demandé
                if torch.cuda.is_available():
                    device = 'cuda'
                    print(f"🚀 GPU: {torch.cuda.get_device_name(0)}")
            else:
                # En WSL, utiliser CPU par défaut pour éviter les problèmes d'initialisation CUDA
                print(f"💡 Astuce: Définir CUDA_VISIBLE_DEVICES=0 pour utiliser le GPU")
        except Exception as e:
            print(f"⚠️  CUDA non disponible: {e}")
        
        print(f"🎯 Device: {device}")
        self.model = SentenceTransformer(model_name, device=device)
        print(f"✅ Modèle chargé ({self.model.get_sentence_embedding_dimension()} dimensions)")
        
        # Vérifier que la collection existe
        try:
            self.client.get_collection(self.collection_name)
        except Exception as e:
            raise RuntimeError(f"Collection {self.collection_name} n'existe pas: {e}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Génère un embedding sémantique pour le texte
        
        Args:
            text: Texte à embedder
            
        Returns:
            Vecteur d'embedding (384 dimensions avec all-MiniLM-L6-v2)
        """
        # Utiliser sentence-transformers pour un vrai embedding sémantique
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def store_fact(self, fact: str, category: str = "general", metadata: Optional[Dict] = None) -> Dict:
        """
        Stocke un fait en mémoire
        
        Args:
            fact: Le fait à stocker
            category: Catégorie du fait
            metadata: Métadonnées supplémentaires
            
        Returns:
            Le fait stocké avec son ID et timestamp
        """
        point_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Générer l'embedding
        vector = self._generate_embedding(fact)
        
        # Préparer le payload
        payload = {
            "type": "fact",
            "fact": fact,
            "category": category,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }
        
        # Insérer dans Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )]
        )
        
        return {
            "id": point_id,
            "fact": fact,
            "category": category,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }
    
    def get_facts(self, category: Optional[str] = None, limit: Optional[int] = 10) -> List[Dict]:
        """
        Récupère les faits stockés
        
        Args:
            category: Filtrer par catégorie
            limit: Limiter le nombre de résultats
            
        Returns:
            Liste des faits
        """
        # Construire le filtre
        filter_conditions = [
            FieldCondition(key="type", match=MatchValue(value="fact"))
        ]
        
        if category:
            filter_conditions.append(
                FieldCondition(key="category", match=MatchValue(value=category))
            )
        
        # Rechercher avec scroll (pas besoin de vecteur de requête)
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(must=filter_conditions),
            limit=limit or 100,
            with_payload=True,
            with_vectors=False
        )
        
        facts = []
        for point in results[0]:  # results est un tuple (points, next_page_offset)
            payload = point.payload
            facts.append({
                "id": str(point.id),
                "fact": payload.get("fact", ""),
                "category": payload.get("category", ""),
                "timestamp": payload.get("timestamp", ""),
                "metadata": payload.get("metadata", {})
            })
        
        return facts
    
    def store_decision(self, decision: str, reasoning: str, context: Optional[str] = None) -> Dict:
        """
        Stocke une décision importante
        
        Args:
            decision: La décision prise
            reasoning: Raisonnement derrière la décision
            context: Contexte de la décision
            
        Returns:
            La décision stockée
        """
        point_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Générer l'embedding basé sur la décision + raisonnement
        text_for_embedding = f"{decision} {reasoning}"
        vector = self._generate_embedding(text_for_embedding)
        
        # Préparer le payload
        payload = {
            "type": "decision",
            "decision": decision,
            "reasoning": reasoning,
            "context": context,
            "timestamp": timestamp
        }
        
        # Insérer dans Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )]
        )
        
        return {
            "id": point_id,
            "decision": decision,
            "reasoning": reasoning,
            "context": context,
            "timestamp": timestamp
        }
    
    def get_decisions(self, limit: Optional[int] = 10) -> List[Dict]:
        """
        Récupère les décisions stockées
        
        Args:
            limit: Limiter le nombre de résultats
            
        Returns:
            Liste des décisions
        """
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(must=[
                FieldCondition(key="type", match=MatchValue(value="decision"))
            ]),
            limit=limit or 100,
            with_payload=True,
            with_vectors=False
        )
        
        decisions = []
        for point in results[0]:
            payload = point.payload
            decisions.append({
                "id": str(point.id),
                "decision": payload.get("decision", ""),
                "reasoning": payload.get("reasoning", ""),
                "context": payload.get("context"),
                "timestamp": payload.get("timestamp", "")
            })
        
        return decisions
    
    def store_conversation_summary(self, summary: str, topics: List[str], outcomes: List[str]) -> Dict:
        """
        Stocke un résumé de conversation
        
        Args:
            summary: Résumé de la conversation
            topics: Sujets abordés
            outcomes: Résultats/actions
            
        Returns:
            Le résumé stocké
        """
        point_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Générer l'embedding
        vector = self._generate_embedding(summary)
        
        # Préparer le payload
        payload = {
            "type": "conversation",
            "summary": summary,
            "topics": topics,
            "outcomes": outcomes,
            "timestamp": timestamp
        }
        
        # Insérer dans Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )]
        )
        
        return {
            "id": point_id,
            "summary": summary,
            "topics": topics,
            "outcomes": outcomes,
            "timestamp": timestamp
        }
    
    def search_facts(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Recherche sémantique dans les faits
        
        Args:
            query: Requête de recherche
            limit: Nombre de résultats
            
        Returns:
            Faits correspondants avec score de similarité
        """
        # Générer l'embedding de la requête
        query_vector = self._generate_embedding(query)
        
        # Recherche vectorielle avec query_points
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=Filter(must=[
                FieldCondition(key="type", match=MatchValue(value="fact"))
            ]),
            limit=limit,
            with_payload=True
        )
        
        facts = []
        for result in results.points:
            payload = result.payload
            facts.append({
                "id": str(result.id),
                "fact": payload.get("fact", ""),
                "category": payload.get("category", ""),
                "timestamp": payload.get("timestamp", ""),
                "metadata": payload.get("metadata", {}),
                "score": result.score
            })
        
        return facts
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Obtient des statistiques sur la mémoire
        
        Returns:
            Dictionnaire avec les stats
        """
        collection_info = self.client.get_collection(self.collection_name)
        
        # Compter par type
        facts_count = len(self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(must=[FieldCondition(key="type", match=MatchValue(value="fact"))]),
            limit=10000
        )[0])
        
        decisions_count = len(self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(must=[FieldCondition(key="type", match=MatchValue(value="decision"))]),
            limit=10000
        )[0])
        
        conversations_count = len(self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(must=[FieldCondition(key="type", match=MatchValue(value="conversation"))]),
            limit=10000
        )[0])
        
        return {
            "total_points": collection_info.points_count,
            "total_facts": facts_count,
            "total_decisions": decisions_count,
            "total_conversations": conversations_count
        }
    
    def clear_all(self):
        """Efface toute la mémoire (ATTENTION !)"""
        # Supprimer tous les points de la collection
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(must=[])  # Match all
        )


# Instance globale
_memory = None

def get_memory() -> QdrantMemory:
    """Obtient l'instance de mémoire (singleton)"""
    global _memory
    if _memory is None:
        _memory = QdrantMemory()
    return _memory


# Fonctions utilitaires
def remember(fact: str, category: str = "general") -> Dict:
    """
    Stocke un fait en mémoire avec déduplication automatique
    
    Args:
        fact: Fait à mémoriser
        category: Catégorie
        
    Returns:
        Dict avec id du fait (nouveau ou existant)
    """
    memory = get_memory()
    
    # DÉDUPLICATION: Chercher des faits très similaires
    similar = memory.search_facts(fact, limit=3)
    
    # Si un fait quasi-identique existe (score > 0.9), ne pas dupliquer
    if similar and similar[0].get('score', 0) > 0.9:
        print(f"⚠️  Fait similaire déjà en mémoire (score: {similar[0]['score']:.2f})")
        return {
            "id": similar[0]['id'],
            "fact": similar[0]['fact'],
            "category": similar[0]['category'],
            "status": "deduplicated"
        }
    
    # Sinon stocker normalement
    return memory.store_fact(fact, category)


def recall(category: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """Récupère des faits de la mémoire par catégorie"""
    return get_memory().get_facts(category, limit)


def search_facts(query: str, limit: int = 5) -> List[Dict]:
    """Recherche sémantique dans les faits mémorisés"""
    return get_memory().search_facts(query, limit)


def decide(decision: str, reasoning: str) -> Dict:
    """Enregistre une décision"""
    return get_memory().store_decision(decision, reasoning)

