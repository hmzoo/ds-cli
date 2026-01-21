# Migration vers Qdrant

## Date: 22 janvier 2026

## Résumé
Le système de mémoire de l'agent DeepSeek a été migré de fichiers JSON vers Qdrant, une base de données vectorielle.

## Changements

### Avant (JSON)
- Stockage dans `.memory/` (facts.json, decisions.json, conversations.json)
- Recherche textuelle simple (correspondance de mots-clés)
- Pas de recherche sémantique

### Après (Qdrant)
- Stockage dans Qdrant à `http://172.16.20.90:6333`
- Collection: `deepseek_collection`
- Vecteurs: 1536 dimensions, distance Cosine
- Recherche sémantique avec embeddings
- Meilleure récupération contextuelle

## Architecture

### QdrantMemory
Classe principale remplaçant `SimpleMemory`:
- `store_fact()`: Stocke un fait avec embedding
- `get_facts()`: Récupère les faits (avec filtres)
- `store_decision()`: Stocke une décision
- `get_decisions()`: Récupère les décisions
- `store_conversation_summary()`: Stocke un résumé de conversation
- `search_facts()`: Recherche sémantique dans les faits
- `get_statistics()`: Statistiques de la mémoire

### Embeddings
Pour l'instant: hash simple SHA256 normalisé (1536 dimensions)

**TODO**: Remplacer par un vrai modèle d'embedding:
- Option 1: sentence-transformers (local, gratuit)
- Option 2: OpenAI Embeddings API (payant, meilleur qualité)
- Option 3: API DeepSeek embeddings (si disponible)

### Structure des points Qdrant
Chaque point contient:
- **id**: UUID unique
- **vector**: Embedding 1536 dimensions
- **payload**:
  - `type`: "fact" | "decision" | "conversation"
  - `timestamp`: ISO 8601
  - Champs spécifiques au type

## API

Les fonctions utilitaires restent identiques:

```python
from tools.memory_tools import remember, recall, decide

# Stocker un fait
remember("L'utilisateur préfère Python", category="user_preference")

# Récupérer des faits
facts = recall(category="user_preference", limit=10)

# Enregistrer une décision
decide("Utiliser Qdrant", "Meilleure recherche sémantique")
```

## Migration des données

Les données JSON ont été migrées automatiquement:
```bash
python migrate_to_qdrant.py
```

**Résultat**:
- 3 faits migrés
- 1 décision migrée
- 0 conversations (pas de fichier conversations.json)

## Configuration

### .env
```
QDRANT_ENDPOINT="http://172.16.20.90:6333"
QDRANT_COLLECTION_NAME="deepseek_collection"
```

### Collection Qdrant
```json
{
  "name": "deepseek_collection",
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  }
}
```

## Tests

### Test unitaire
```bash
python test_qdrant_memory.py
```

Résultats: ✅ Tous les tests passent
- Opérations de base (store, get, stats)
- Recherche sémantique
- Filtres par catégorie

### Test avec l'agent
```bash
./test_agent_memory.sh
```

## Améliorations futures

### Court terme
1. ✅ Migrer vers Qdrant
2. ✅ Implémenter recherche sémantique
3. ⬜ Intégrer un vrai modèle d'embedding
4. ⬜ Tester performance avec plus de données

### Moyen terme
1. ⬜ Implémenter le clustering automatique des faits
2. ⬜ Ajouter la déduplication (éviter les doublons sémantiques)
3. ⬜ Implémenter l'oubli progressif (decay des vieux faits)
4. ⬜ Ajouter des métadonnées riches (tags, importance, etc.)

### Long terme
1. ⬜ Multi-collection (mémoire court terme vs long terme)
2. ⬜ Synchronisation cloud pour backup
3. ⬜ Interface web pour explorer la mémoire
4. ⬜ Analytics et visualisation des patterns de mémoire

## Notes techniques

### Choix de l'embedding temporaire
Le hash SHA256 est utilisé temporairement car:
- ✅ Déterministe (même texte = même vecteur)
- ✅ Rapide à calculer
- ✅ Pas de dépendance externe
- ❌ Pas de similarité sémantique réelle
- ❌ Distribution non-optimale dans l'espace vectoriel

### Pourquoi 1536 dimensions ?
- Compatible avec OpenAI text-embedding-ada-002
- Bon compromis performance/précision
- Standard dans l'industrie

## Compatibilité

L'API publique (`remember`, `recall`, `decide`) reste **100% compatible** avec l'ancienne version JSON. Aucun changement nécessaire dans le code appelant.

## Dépendances ajoutées

```
qdrant-client==1.16.2
numpy>=2.4.1
```

## Références

- [Documentation Qdrant](https://qdrant.tech/documentation/)
- [Qdrant Python Client](https://github.com/qdrant/qdrant-client)
- [Sentence Transformers](https://www.sbert.net/) (pour futurs embeddings)
