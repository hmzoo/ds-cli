# 🧪 Exemples d'utilisation de l'agent

## Exemple 1: Lister les fichiers Python

```
👤 Vous: Liste tous les fichiers Python dans le dossier tools

🤖 Agent: Je vais chercher les fichiers Python dans le dossier tools.

<tool>
{
  "name": "list_files",
  "parameters": {
    "directory": "tools",
    "pattern": "*.py"
  }
}
</tool>

🔧 Exécution: list_files({"directory": "tools", "pattern": "*.py"})
✓ ["tools/__init__.py", "tools/file_tools.py", "tools/shell_tools.py", ...]

🤖 Agent: J'ai trouvé 4 fichiers Python dans le dossier tools:
- __init__.py
- file_tools.py
- shell_tools.py
- api_tools.py
- memory_tools.py
```

## Exemple 2: Vérifier le système

```
👤 Vous: Quelles sont les infos de mon système?

🤖 Agent: <tool>
{
  "name": "get_system_info",
  "parameters": {}
}
</tool>

🔧 Exécution: get_system_info({})
✓ {"os": "Linux", "kernel": "5.15.0", ...}

🤖 Agent: Voici les informations de votre système:
- OS: Linux
- Kernel: 5.15.0
- Architecture: x86_64
- Python: 3.11.5
```

## Exemple 3: Utiliser la mémoire

```
👤 Vous: Souviens-toi que je préfère Python pour les scripts

🤖 Agent: <tool>
{
  "name": "remember",
  "parameters": {
    "fact": "L'utilisateur préfère Python pour les scripts",
    "category": "preferences"
  }
}
</tool>

🔧 Exécution: remember(...)
✓ {"id": 1, "fact": "...", "timestamp": "2026-01-19..."}

🤖 Agent: C'est noté ! Je me souviendrai de votre préférence pour Python.
```

## Exemple 4: Lire et analyser un fichier

```
👤 Vous: Lis le fichier README.md et dis-moi ce qu'il contient

🤖 Agent: <tool>
{
  "name": "read_file",
  "parameters": {
    "file_path": "README.md"
  }
}
</tool>

🔧 Exécution: read_file({"file_path": "README.md"})
✓ "# 🤖 DeepSeek Dev Agent - CLI\n\nAgent de développement..."

🤖 Agent: Le README.md contient:
- Titre: DeepSeek Dev Agent - CLI
- Sections: Installation, Utilisation, Fonctionnalités...
- Instructions de lancement avec ./run.sh
- Liste de 10 outils disponibles
```

## Exemple 5: Exécuter plusieurs commandes

```
👤 Vous: Vérifie si git est installé et quelle version

🤖 Agent: <tool>
{
  "name": "check_command_exists",
  "parameters": {
    "command": "git"
  }
}
</tool>

🔧 Exécution: check_command_exists({"command": "git"})
✓ True

🤖 Agent: Git est installé. Maintenant je vérifie la version:

<tool>
{
  "name": "execute_command",
  "parameters": {
    "command": "git --version"
  }
}
</tool>

🔧 Exécution: execute_command({"command": "git --version"})
✓ Succès
git version 2.34.1

🤖 Agent: Git est installé, version 2.34.1
```

## Commandes spéciales

- `/tools` - Liste tous les outils disponibles
- `/stats` - Affiche les statistiques (messages, mémoire)
- `/clear` - Efface l'historique
- `/help` - Affiche l'aide
- `/quit` - Quitte le chat

## Tips

1. **L'agent est autonome** - Il décide quels outils utiliser
2. **Plusieurs outils** - Il peut chaîner plusieurs appels
3. **Mémoire persistante** - Les faits sont sauvegardés dans `.memory/`
4. **Boucle intelligente** - L'agent analyse les résultats avant de répondre
