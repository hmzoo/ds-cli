"""
Outils web pour l'agent DeepSeek
- Recherche web avec Tavily API
- Récupération de contenu de pages web
"""

import os
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import re


def search_web(query: str, max_results: int = 5, include_raw_content: bool = False) -> Dict:
    """
    Recherche sur le web avec Tavily API
    
    Args:
        query: Requête de recherche
        max_results: Nombre max de résultats (1-10, défaut: 5)
        include_raw_content: Inclure le contenu brut (augmente tokens)
        
    Returns:
        Dict avec résultats de recherche
        
    Exemple:
        results = search_web("Python FastAPI tutorial", max_results=3)
    """
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key:
        return {
            "error": "TAVILY_API_KEY non trouvée dans l'environnement",
            "results": []
        }
    
    # Limiter max_results pour éviter trop de tokens
    max_results = min(max_results, 10)
    
    try:
        url = "https://api.tavily.com/search"
        
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "include_raw_content": include_raw_content,
            "include_answer": True,  # Résumé direct de Tavily
            "search_depth": "basic"  # basic ou advanced
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Formater les résultats de manière compacte (économie tokens)
        formatted_results = []
        for result in data.get('results', []):
            formatted_results.append({
                "title": result.get('title', ''),
                "url": result.get('url', ''),
                "snippet": result.get('content', '')[:300],  # Limiter à 300 chars
                "score": result.get('score', 0)
            })
        
        return {
            "success": True,
            "query": query,
            "answer": data.get('answer', ''),  # Résumé par Tavily
            "results": formatted_results,
            "total": len(formatted_results)
        }
        
    except requests.exceptions.Timeout:
        return {
            "error": "Timeout: La recherche a pris trop de temps",
            "results": []
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Erreur de requête: {str(e)}",
            "results": []
        }
    except Exception as e:
        return {
            "error": f"Erreur inattendue: {str(e)}",
            "results": []
        }


def fetch_webpage(url: str, max_length: int = 5000) -> Dict:
    """
    Récupère et extrait le contenu d'une page web
    
    Args:
        url: URL de la page à récupérer
        max_length: Longueur max du contenu (défaut: 5000 chars = ~1250 tokens)
        
    Returns:
        Dict avec title, content, url, etc.
        
    Exemple:
        content = fetch_webpage("https://example.com")
    """
    if not url or not url.startswith(('http://', 'https://')):
        return {
            "error": "URL invalide (doit commencer par http:// ou https://)",
            "url": url
        }
    
    try:
        # Headers pour simuler un navigateur
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parser le HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraire le titre
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "Sans titre"
        
        # Nettoyer le HTML (supprimer scripts, styles, etc.)
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Extraire le texte
        text = soup.get_text()
        
        # Nettoyer le texte (espaces multiples, lignes vides)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = '\n'.join(lines)
        
        # Limiter la longueur (IMPORTANT pour tokens)
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length] + "\n...(contenu tronqué)"
        
        return {
            "success": True,
            "url": url,
            "title": title_text,
            "content": clean_text,
            "length": len(clean_text),
            "status_code": response.status_code
        }
        
    except requests.exceptions.Timeout:
        return {
            "error": "Timeout: La page a pris trop de temps à répondre",
            "url": url
        }
    except requests.exceptions.HTTPError as e:
        return {
            "error": f"Erreur HTTP {e.response.status_code}: {e.response.reason}",
            "url": url
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Erreur de connexion: {str(e)}",
            "url": url
        }
    except Exception as e:
        return {
            "error": f"Erreur lors du parsing: {str(e)}",
            "url": url
        }


def extract_links(url: str, filter_pattern: Optional[str] = None) -> Dict:
    """
    Extrait tous les liens d'une page web
    
    Args:
        url: URL de la page
        filter_pattern: Pattern regex pour filtrer les liens (optionnel)
        
    Returns:
        Dict avec liste des liens trouvés
        
    Exemple:
        links = extract_links("https://example.com", filter_pattern=".*\\.pdf$")
    """
    if not url or not url.startswith(('http://', 'https://')):
        return {
            "error": "URL invalide",
            "url": url
        }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraire tous les liens
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text().strip()
            
            # Convertir liens relatifs en absolus
            if href.startswith('/'):
                from urllib.parse import urljoin
                href = urljoin(url, href)
            
            # Filtrer si pattern fourni
            if filter_pattern:
                if not re.search(filter_pattern, href):
                    continue
            
            # Éviter doublons
            if href not in [l['url'] for l in links]:
                links.append({
                    "url": href,
                    "text": text[:100]  # Limiter texte
                })
        
        return {
            "success": True,
            "source_url": url,
            "links": links[:50],  # Limiter à 50 liens max (tokens)
            "total": len(links)
        }
        
    except Exception as e:
        return {
            "error": f"Erreur: {str(e)}",
            "url": url
        }


def summarize_webpage(url: str) -> Dict:
    """
    Récupère une page et retourne un résumé compact
    OPTIMISÉ pour tokens (max ~500 chars)
    
    Args:
        url: URL de la page
        
    Returns:
        Dict avec résumé très compact
    """
    result = fetch_webpage(url, max_length=2000)
    
    if not result.get('success'):
        return result
    
    # Prendre juste les premiers 500 chars du contenu
    content = result.get('content', '')
    summary = content[:500]
    
    if len(content) > 500:
        summary += "..."
    
    return {
        "success": True,
        "url": url,
        "title": result.get('title', ''),
        "summary": summary,
        "full_length": result.get('length', 0)
    }


# Installation des dépendances si nécessaire
def check_dependencies() -> Dict:
    """Vérifie que les dépendances sont installées"""
    missing = []
    
    try:
        import bs4
    except ImportError:
        missing.append("beautifulsoup4")
    
    try:
        import requests
    except ImportError:
        missing.append("requests")
    
    if missing:
        return {
            "success": False,
            "missing": missing,
            "install_command": f"pip install {' '.join(missing)}"
        }
    
    return {
        "success": True,
        "message": "Toutes les dépendances sont installées"
    }
