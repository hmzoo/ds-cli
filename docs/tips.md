# 💡 Conseils d'utilisation - DeepSeek Agent

## 🎯 Bonnes pratiques

### 1. Soyez spécifique mais naturel
```
✅ Bon: "Lis le fichier README.md et résume-le en 3 points"
❌ Éviter: "Fichier README"
```

### 2. L'agent comprend le contexte
```
✅ "Liste les fichiers Python, puis compte les lignes dans chacun"
→ L'agent chaînera automatiquement les outils
```

### 3. Laissez l'agent choisir ses outils
```
✅ "Combien de lignes de code dans le projet ?"
→ L'agent décidera d'utiliser find + wc -l
```

### 4. Utilisez la mémoire pour personnaliser
```
"Souviens-toi que je préfère TypeScript à JavaScript"
→ Lors de futures requêtes, l'agent s'en souviendra
```

## 🚀 Cas d'usage avancés

### Analyse de projet
```
"Analyse la structure du projet et dis-moi quels fichiers sont les plus complexes"
```
L'agent va:
1. Lister les fichiers
2. Compter les lignes
3. Analyser la structure
4. Donner des recommandations

### Recherche de bugs
```
"Lis main.py et vérifie s'il y a des erreurs potentielles"
```
L'agent va:
1. Lire le fichier
2. Analyser le code
3. Signaler les problèmes
4. Proposer des corrections

### Documentation automatique
```
"Crée un fichier ARCHITECTURE.md qui décrit la structure du projet"
```
L'agent va:
1. Explorer le projet
2. Analyser les dépendances
3. Générer la documentation
4. Créer le fichier

### Refactoring assisté
```
"Lis tools/file_tools.py et suggère des améliorations"
```
L'agent va:
1. Lire le code
2. Identifier les patterns
3. Proposer des améliorations
4. Expliquer le raisonnement

## ⚡ Commandes utiles

### Exploration
```
"Montre-moi la structure du dossier tools/"
"Quels fichiers ont plus de 200 lignes ?"
"Liste tous les fichiers .md du projet"
```

### Analyse
```
"Compare file_tools.py et shell_tools.py"
"Quel fichier utilise le plus de mémoire ?"
"Y a-t-il des imports inutilisés ?"
```

### Création
```
"Crée un fichier TODO.md avec 5 idées d'amélioration"
"Génère un .gitignore adapté à ce projet Python"
"Écris un script de backup pour les fichiers importants"
```

### Maintenance
```
"Vérifie si toutes les dépendances sont à jour"
"Liste les fichiers modifiés récemment (git)"
"Nettoie les fichiers __pycache__"
```

## 🔍 Debugging

### Voir les outils disponibles
```
/tools
```

### Vérifier les stats
```
/stats
```
Affiche:
- Nombre de messages
- État de la mémoire
- Utilisation des outils

### Réinitialiser la conversation
```
/clear
```
Efface l'historique (mais pas la mémoire persistante)

## 🎨 Astuces de productivité

### 1. Chaîner plusieurs tâches
```
"D'abord lis le README, puis crée un fichier SUMMARY.md avec un résumé"
```

### 2. Utiliser la mémoire comme pense-bête
```
"Souviens-toi que ce projet utilise Python 3.14"
"Note que le port par défaut est 8000"
```

### 3. Demander des explications
```
"Explique-moi ce que fait la fonction _extract_tool_calls dans main.py"
```

### 4. Comparaisons et diffs
```
"Compare les fichiers api_tools.py et shell_tools.py, quelle est la différence ?"
```

### 5. Génération de rapports
```
"Crée un rapport.md avec les statistiques du projet"
```

## ⚠️ Limitations actuelles

### Pas de modification directe de fichiers
L'agent peut créer de nouveaux fichiers mais ne modifie pas directement les existants.
**Workaround**: Demandez-lui de créer une nouvelle version.

### Pas d'accès réseau (sauf API)
L'agent ne peut pas faire de requêtes HTTP arbitraires.
**Workaround**: Utilisez `curl` via execute_command.

### Limite de 10 itérations
Pour les tâches très complexes, l'agent peut s'arrêter.
**Workaround**: Décomposez en plusieurs requêtes.

### Mémoire simple (pas de recherche sémantique)
La recherche dans la mémoire est textuelle, pas vectorielle.
**Futur**: Intégration Qdrant prévue.

## 🎓 Exemples complets

### Exemple 1: Audit de code
```bash
👤: Fais un audit complet du fichier main.py

🤖: [L'agent va]:
1. Lire le fichier
2. Compter les lignes
3. Vérifier les imports
4. Analyser la complexité
5. Générer un rapport détaillé
```

### Exemple 2: Setup projet
```bash
👤: Crée un fichier setup.py pour ce projet

🤖: [L'agent va]:
1. Lire requirements.txt
2. Analyser la structure
3. Générer un setup.py adapté
4. Expliquer comment l'utiliser
```

### Exemple 3: Documentation
```bash
👤: Documente toutes les fonctions de tools/memory_tools.py

🤖: [L'agent va]:
1. Lire le fichier
2. Extraire les fonctions
3. Analyser les signatures
4. Générer la documentation
5. La sauvegarder dans docs/
```

## 🌟 Best Practices

1. **Commencez simple** - Testez avec des requêtes basiques
2. **Soyez patient** - Les tâches complexes prennent du temps
3. **Utilisez la mémoire** - Enregistrez vos préférences
4. **Vérifiez les résultats** - L'agent peut faire des erreurs
5. **Itérez** - Affinez vos requêtes selon les résultats
6. **Lisez CHANGELOG.md** - Restez à jour sur les améliorations

## 📞 Besoin d'aide ?

- Consultez [docs/examples.md](docs/examples.md) pour plus d'exemples
- Lisez [docs/development.md](docs/development.md) pour contribuer
- Utilisez `/help` dans le chat pour voir les commandes
