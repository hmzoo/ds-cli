# 🚀 Guide de Développement - DeepSeek Agent

## Architecture

```
ds-cli/
├── main.py                    # Point d'entrée avec function calling
├── tools/                     # Outils de l'agent
│   ├── __init__.py           # Exports
│   ├── file_tools.py         # Manipulation fichiers
│   ├── shell_tools.py        # Exécution commandes
│   ├── api_tools.py          # Abstraction API DeepSeek
│   └── memory_tools.py       # Mémoire JSON
├── .memory/                   # Données de mémoire (JSON)
├── SYSTEM.md                  # Instructions système
└── docs/                      # Documentation

```

## Comment fonctionne le Function Calling

### 1. L'agent reçoit une requête

L'utilisateur pose une question qui nécessite l'utilisation d'outils.

### 2. L'agent génère des appels d'outils

Dans sa réponse, l'agent inclut des balises `<tool>`:

```xml
<tool>
{
  "name": "execute_command",
  "parameters": {
    "command": "ls -la"
  }
}
</tool>
```

### 3. Le système détecte et exécute

`main.py` utilise une regex pour extraire les appels:
```python
pattern = r'<tool>\s*(\{.*?\})\s*</tool>'
matches = re.findall(pattern, text, re.DOTALL)
```

### 4. Les résultats sont renvoyés à l'agent

Les résultats sont ajoutés à l'historique comme message "user":
```python
results_text = "## Résultats des outils:\n\n..."
self.add_message("user", results_text)
```

### 5. L'agent analyse et répond

L'agent reçoit les résultats et peut:
- Appeler d'autres outils
- Fournir une réponse finale

## Ajouter un nouvel outil

### 1. Créer la fonction dans tools/

```python
# tools/mon_outil.py
def mon_outil(param1: str, param2: int = 10) -> dict:
    """
    Description de l'outil
    
    Args:
        param1: Description du paramètre
        param2: Autre paramètre (optionnel)
        
    Returns:
        Résultat sous forme de dict
    """
    # Implémentation
    return {"result": "OK"}
```

### 2. Exporter dans tools/__init__.py

```python
from .mon_outil import mon_outil

__all__ = [
    # ... autres outils
    'mon_outil'
]
```

### 3. Enregistrer dans ToolExecutor (main.py)

```python
class ToolExecutor:
    def __init__(self):
        self.tools = {
            # ... autres outils
            'mon_outil': mon_outil,
        }
```

### 4. Documenter dans SYSTEM.md

Ajouter dans la section des outils:
```markdown
- `mon_outil(param1, param2=10)` - Description de l'outil
```

## Débogage

### Activer les logs détaillés

Ajouter dans main.py:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Voir les appels d'outils

Les appels sont affichés avec:
```python
print(f"🔧 Exécution: {tool_name}({params})")
```

### Tester un outil individuellement

```python
python3 -c "
from tools import execute_command
result = execute_command('ls -la')
print(result)
"
```

## Tests

### Test unitaire d'un outil

```python
# test_tools.py
import pytest
from tools import read_file

def test_read_file():
    result = read_file('README.md')
    assert 'DeepSeek' in result
```

### Test d'intégration

```bash
# Test via stdin
echo "liste les fichiers" | python3 main.py
```

## Bonnes Pratiques

### 1. Outils idempotents
Les outils doivent pouvoir être appelés plusieurs fois sans effets de bord.

### 2. Gestion d'erreurs
Toujours retourner un dict avec `{"error": "..."}` en cas d'erreur.

### 3. Timeouts
Utiliser des timeouts pour les commandes shell:
```python
execute_command("long_command", timeout=60)
```

### 4. Validation des entrées
Valider les paramètres avant exécution:
```python
if not os.path.exists(file_path):
    return {"error": "File not found"}
```

### 5. Documentation
Documenter chaque outil avec docstring complète.

## Sécurité

### Commandes shell

Utiliser une whitelist de commandes sûres:
```python
SAFE_COMMANDS = {'ls', 'cat', 'pwd', ...}
```

### Validation des chemins

Éviter les path traversal:
```python
path = Path(file_path).resolve()
if not str(path).startswith(str(base_dir)):
    raise ValueError("Invalid path")
```

### Pas de shell=True

Éviter `shell=True` sauf si nécessaire:
```python
subprocess.run(['ls', '-la'])  # ✓ Bon
subprocess.run('ls -la', shell=True)  # ✗ Dangereux
```

## Optimisations futures

1. **Cache des résultats** - Éviter appels répétés
2. **Parallélisation** - Exécuter plusieurs outils simultanément
3. **Streaming des résultats** - Afficher les résultats au fur et à mesure
4. **Qdrant** - Remplacer la mémoire JSON par Qdrant
5. **Embeddings** - Recherche sémantique dans la mémoire
