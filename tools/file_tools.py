"""
Outils d'accès et manipulation de fichiers pour l'agent DeepSeek
"""

from pathlib import Path
from typing import List, Optional


def read_file(file_path: str, start_line: int = None, end_line: int = None) -> str:
    """
    Lit le contenu d'un fichier (partiellement ou en entier)
    
    Args:
        file_path: Chemin du fichier à lire
        start_line: Ligne de début (1-indexed, optionnel)
        end_line: Ligne de fin incluse (1-indexed, optionnel)
        
    Returns:
        Contenu du fichier (ou extrait si start_line/end_line spécifiés)
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {file_path}")
    
    content = path.read_text(encoding='utf-8')
    
    # Si pas de ligne spécifiée, retourner tout le contenu
    if start_line is None and end_line is None:
        return content
    
    # Sinon, extraire les lignes demandées
    lines = content.splitlines(keepends=True)
    total_lines = len(lines)
    
    # Gérer les indices (1-indexed → 0-indexed)
    start_idx = (start_line - 1) if start_line else 0
    end_idx = end_line if end_line else total_lines
    
    # Vérifications
    if start_idx < 0 or start_idx >= total_lines:
        raise ValueError(f"start_line {start_line} hors limites (1-{total_lines})")
    if end_idx < start_idx or end_idx > total_lines:
        raise ValueError(f"end_line {end_line} invalide (doit être entre {start_line} et {total_lines})")
    
    return ''.join(lines[start_idx:end_idx])


def write_file(file_path: str, content: str, max_size: int = 50000) -> dict:
    """
    Écrit du contenu dans un fichier
    
    Args:
        file_path: Chemin du fichier
        content: Contenu à écrire
        max_size: Taille max en caractères (défaut 50KB)
        
    Returns:
        Dict avec success, message, size
    """
    content_size = len(content)
    
    # Avertissement si contenu très volumineux
    if content_size > max_size:
        return {
            'success': False,
            'error': f'Contenu trop volumineux ({content_size} chars > {max_size})',
            'suggestion': 'Utiliser append_file() ou exécuter: echo "..." > file',
            'size': content_size
        }
    
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    
    return {
        'success': True,
        'file': str(path),
        'size': content_size,
        'lines': content.count('\n') + 1
    }


def append_file(file_path: str, content: str) -> dict:
    """
    Ajoute du contenu à la fin d'un fichier (ou le crée)
    
    Args:
        file_path: Chemin du fichier
        content: Contenu à ajouter
        
    Returns:
        Dict avec success et info
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Lire contenu existant si fichier existe
    original_size = path.stat().st_size if path.exists() else 0
    
    with path.open('a', encoding='utf-8') as f:
        f.write(content)
    
    new_size = path.stat().st_size
    
    return {
        'success': True,
        'file': str(path),
        'original_size': original_size,
        'added': len(content),
        'new_size': new_size
    }


def list_files(directory: str, pattern: str = "*", max_results: int = 100) -> dict:
    """
    Liste les fichiers dans un répertoire (LIMITÉ pour éviter overflow)
    
    Args:
        directory: Chemin du répertoire
        pattern: Pattern de filtrage (ex: "*.py")
        max_results: Nombre max de résultats (défaut 100)
        
    Returns:
        Dict avec liste des fichiers + info truncation
    """
    path = Path(directory)
    if not path.exists():
        raise FileNotFoundError(f"Répertoire non trouvé: {directory}")
    
    # Dossiers à ignorer (critiques pour éviter overflow)
    IGNORED_DIRS = {
        'venv', '.venv', 'env', '.env',  # Environnements virtuels
        'node_modules', '.git', '.svn',   # Dépendances et VCS
        '__pycache__', '.pytest_cache',   # Cache Python
        'build', 'dist', '.eggs',         # Build artifacts
        '.tox', '.mypy_cache', '.ruff_cache'  # Outils dev
    }
    
    # Collecter jusqu'à max_results + 1 pour détecter truncation
    files = []
    ignored_count = 0
    
    for f in path.rglob(pattern):
        # Vérifier si le chemin contient un dossier ignoré
        if any(ignored_dir in f.parts for ignored_dir in IGNORED_DIRS):
            ignored_count += 1
            continue
            
        if f.is_file():
            files.append(str(f))
            if len(files) > max_results:
                break
    
    truncated = len(files) > max_results
    if truncated:
        files = files[:max_results]
    
    message = f'{len(files)} fichiers trouvés'
    if ignored_count > 0:
        message += f' ({ignored_count} ignorés: venv, cache, etc.)'
    if truncated:
        message += ' (liste tronquée)'
    
    return {
        'files': files,
        'count': len(files),
        'ignored': ignored_count,
        'truncated': truncated,
        'message': message
    }


def file_exists(file_path: str) -> bool:
    """
    Vérifie si un fichier existe
    
    Args:
        file_path: Chemin du fichier
        
    Returns:
        True si le fichier existe
    """
    return Path(file_path).exists()


def replace_in_file(file_path: str, old_text: str, new_text: str) -> dict:
    """
    Remplace du texte dans un fichier (modification ciblée sans réécrire tout le fichier)
    
    Args:
        file_path: Chemin du fichier
        old_text: Texte à remplacer (doit être exact)
        new_text: Nouveau texte
        
    Returns:
        Dict avec success, message, replacements count
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {file_path}")
    
    # Lire le contenu
    content = path.read_text(encoding='utf-8')
    
    # Vérifier que old_text existe
    if old_text not in content:
        return {
            'success': False,
            'error': f'Texte à remplacer non trouvé dans {file_path}',
            'hint': 'Vérifiez que old_text correspond exactement (espaces, sauts de ligne, etc.)'
        }
    
    # Compter les occurrences
    count = content.count(old_text)
    
    # Remplacer
    new_content = content.replace(old_text, new_text)
    
    # Écrire
    path.write_text(new_content, encoding='utf-8')
    
    return {
        'success': True,
        'file': str(path),
        'replacements': count,
        'old_length': len(old_text),
        'new_length': len(new_text),
        'message': f'{count} remplacement(s) effectué(s)'
    }


# À implémenter:
# - search_in_files()
# - create_directory()
# - delete_file()
# - copy_file()
# - move_file()
# - get_file_info()
# ✅ append_file() - Implémenté
