# Tests unitaires pour ds-cli

Ce répertoire contient les tests unitaires pour les différents modules du projet.

## Structure

- `conftest.py` - Configuration pytest
- `test_file_tools.py` - Tests des outils de fichiers
- `test_qdrant_backup.py` - Tests des outils de backup Qdrant

## Lancer les tests

```bash
# Tous les tests
pytest

# Tests spécifiques
pytest tests/test_file_tools.py

# Avec couverture
pytest --cov=tools tests/

# Mode verbose
pytest -v
```

## Prérequis

- pytest
- pytest-cov (optionnel, pour la couverture)
- Qdrant actif pour les tests de backup
