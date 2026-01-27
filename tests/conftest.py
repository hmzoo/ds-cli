"""
Configuration pytest pour les tests
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer les modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configurer les variables d'environnement pour les tests
os.environ.setdefault('QDRANT_ENDPOINT', 'http://172.16.20.90:6333')
os.environ.setdefault('QDRANT_COLLECTION_NAME', 'deepseek_collection')
