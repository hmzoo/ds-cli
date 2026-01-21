# 📚 Documentation - DeepSeek Dev Agent

## Journal de Développement

### 2026-01-21 - Intégration des Outils Web 🌐

**Objectif**: Ajouter des capacités de recherche web et récupération de contenu

**Fichiers créés/modifiés**:
- `tools/web_tools.py` - Nouveaux outils web (294 lignes)
- `tools/__init__.py` - Export des 4 nouveaux outils
- `main.py` - Intégration des outils web dans ToolExecutor
- `tools/file_tools.py` - Amélioration write_file + append_file

**Fonctionnalités implémentées**:
- ✅ **search_web()** - Recherche web avec Tavily API (max 5 résultats)
- ✅ **fetch_webpage()** - Récupération contenu HTML (max 5000 chars)
- ✅ **extract_links()** - Extraction liens d'une page (max 50)
- ✅ **summarize_webpage()** - Résumé ultra-compact (500 chars)
- ✅ **append_file()** - Ajout de contenu à un fichier existant
- ✅ Validation taille pour write_file (max 50KB)

**Outils Web disponibles** (14 outils total):
1. `search_web` - Recherche avec Tavily (snippets 300 chars, answer summary)
2. `fetch_webpage` - Parse HTML avec BeautifulSoup (~1250 tokens max)
3. `extract_links` - Récupère href avec filtrage regex optionnel
4. `summarize_webpage` - Version ultra-compacte de fetch_webpage

**Optimisations Token**:
- Limite stricte: 5000 chars/page (~1250 tokens)
- Snippets recherche: 300 chars max
- Max résultats: 5 pour search_web, 50 pour extract_links
- Format compact (semicolon-separated)
- Timeout 10s sur toutes les requêtes HTTP

**Tests effectués**:
- ✅ `search_web("mantes religieuses")` - 5 résultats pertinents (scores 0.63-0.93)
- ✅ `fetch_webpage("https://ladivulgation.fr/")` - 1016 chars récupérés (~254 tokens)
- ✅ `summarize_webpage()` - Résumé 500 chars validé
- ✅ Dépendances validées (beautifulsoup4 v4.14.3)
- ✅ Tavily API opérationnelle avec clé TAVILY_API_KEY

**Performance**:
- Consommation: ~526 tokens pour 5 résultats web
- Respect des limites token (user priority)
- Temps réponse: <2s pour recherche web
- HTML parsing: nettoyage scripts/nav/footer automatique

**Décisions techniques**:
1. Tavily API pour recherche (meilleure pertinence vs Google)
2. BeautifulSoup4 pour parsing HTML (léger et efficace)
3. Limites strictes pour contrôle coûts
4. Format compact pour économie tokens
5. Gestion erreurs complète (timeouts, HTTP errors)

---

### 2026-01-19 - Implémentation du Function Calling ✨

**Objectif**: Permettre à l'agent d'utiliser ses outils automatiquement

**Fichiers créés/modifiés**:
- `tools/shell_tools.py` - Outils d'exécution de commandes shell
- `tools/api_tools.py` - Abstraction de l'API DeepSeek
- `tools/memory_tools.py` - Système de mémoire simple (JSON)
- `main.py` - Système complet de function calling
- `tools/__init__.py` - Export de tous les outils

**Fonctionnalités implémentées**:
- ✅ **Function Calling complet** - L'agent peut appeler ses outils
- ✅ Détection automatique des appels via balises `<tool>`
- ✅ Exécution sécurisée des outils
- ✅ Boucle agent-outils-agent (jusqu'à 5 itérations)
- ✅ Affichage coloré des exécutions d'outils
- ✅ 10 outils disponibles (files, shell, memory)
- ✅ Commande `/tools` pour lister les outils

**Outils disponibles**:
1. `read_file` - Lecture de fichiers
2. `write_file` - Écriture de fichiers
3. `list_files` - Liste fichiers avec pattern
4. `file_exists` - Vérification existence
5. `execute_command` - Exécution commandes shell
6. `check_command_exists` - Vérification commande
7. `get_system_info` - Infos système
8. `remember` - Mémoriser un fait
9. `recall` - Rappeler des faits
10. `decide` - Enregistrer une décision

**Architecture Function Calling**:
```
User Input → Agent → <tool>JSON</tool> → ToolExecutor
                ↑                              ↓
                └────── Tool Results ──────────┘
```

**Tests effectués**:
- ✅ Listing de fichiers avec `execute_command`
- ✅ Détection et parsing des appels d'outils
- ✅ Boucle agent-outils fonctionne
- ✅ Affichage des résultats formaté

**Décisions techniques**:
1. Format `<tool>{JSON}</tool>` pour les appels
2. Regex pour extraction des tool calls
3. Boucle limitée à 5 itérations max
4. Mémoire simple en JSON (pas Qdrant pour l'instant)
5. Whitelist de commandes shell sûres

---

### 2026-01-19 - Initialisation du projet

**Objectif**: Créer un agent de développement interactif avec DeepSeek

**Fichiers créés**:
- `main.py` - Interface chat CLI interactive avec streaming
- `run.sh` - Script de lancement
- `requirements.txt` - Dépendances Python
- `tools/file_tools.py` - Premiers outils de manipulation de fichiers
- `tools/__init__.py` - Package tools

**Fonctionnalités implémentées**:
- ✅ Chat interactif en ligne de commande
- ✅ Streaming des réponses en temps réel
- ✅ Chargement des instructions depuis SYSTEM.md
- ✅ Historique de conversation
- ✅ Commandes: /clear, /stats, /help, /quit
- ✅ Interface colorée avec codes ANSI
- ✅ Gestion d'erreurs robuste

**Configuration**:
- Environnement virtuel Python (venv/)
- API DeepSeek via DEEPSEEK_API_KEY
- Modèle: deepseek-chat

**Décisions techniques**:
1. Utilisation de `requests` pour l'API (simple et efficace)
2. Streaming SSE pour réponses en temps réel
3. Structure modulaire avec dossier tools/ pour futures extensions
4. Instructions système externalisées dans SYSTEM.md

**Prochaines étapes**:
- [x] Implémenter tools/shell_tools.py pour exécution de commandes
- [x] Ajouter tools/memory_tools.py (version simple avec JSON)
- [x] Créer tools/api_tools.py pour abstraire l'API DeepSeek
- [x] Permettre à l'agent d'appeler ses outils (Function Calling)
- [ ] Tests automatisés
- [ ] Intégration Qdrant pour mémoire vectorielle

**Tests effectués**:
- ✅ Connexion API DeepSeek fonctionnelle
- ✅ Chat interactif testé avec succès
- ✅ Commandes spéciales fonctionnelles
- ✅ Streaming fluide

---

## Structure Actuelle

```
ds-cli/
├── main.py              # ⭐ Point d'entrée - Chat CLI
├── SYSTEM.md            # Instructions système agent
├── README.md            # Documentation utilisateur
├── run.sh               # Script de lancement
├── requirements.txt     # Dépendances
├── venv/                # Environnement virtuel
├── tools/               # Outils de l'agent
│   ├── __init__.py
│   └── file_tools.py    # ⚙️ Outils fichiers (partiels)
└── docs/
    └── index.md         # 📚 Cette documentation
```

## Liens Utiles

- [README principal](../README.md)
- [Instructions système](../SYSTEM.md)
- [Code source main.py](../main.py)

## Notes de Développement

### API DeepSeek
- Endpoint: `https://api.deepseek.com/v1/chat/completions`
- Compatible avec API OpenAI
- Supporte le streaming SSE
- Format: `data: {...}\ndata: [DONE]`

### Performance
- Latence streaming: ~50-200ms premier token
- Interface fluide grâce au flush() Python
- Utilisation mémoire minimale

### Améliorations Futures
1. Cache des réponses fréquentes
2. Mode debug avec verbosité
3. Export conversations en JSON/MD
4. Multi-sessions avec sauvegarde
5. Intégration terminal avec rich/prompt_toolkit

---

### 2026-01-21 - Système de Tests Automatisés ✅

**Objectif**: Implémenter un système de tests robuste pour garantir la qualité du code

**Fichiers créés/modifiés**:
- `tests/__init__.py` - Package Python pour les tests
- `tests/test_test_runner.py` - Tests pour le runner de tests
- `tests/test_file_tools.py` - Tests pour les outils de fichiers
- `tests/test_shell_tools.py` - Tests pour les outils shell
- `tests/test_memory_tools.py` - Tests pour les outils de mémoire
- `tests/test_api_tools.py` - Tests pour les outils API
- `tests/fixtures/` - Données de test
- `tests/README.md` - Documentation complète du système de tests (249 lignes)
- `.github/workflows/tests.yml` - Intégration continue GitHub Actions (110 lignes)
- `run_tests.py` - Script principal d'exécution des tests

**Fonctionnalités implémentées**:
- ✅ **Système de tests complet** avec pytest
- ✅ **Script d'exécution** `run_tests.py` avec multiples options
- ✅ **Intégration Continue** GitHub Actions
- ✅ **Tests unitaires** pour chaque module
- ✅ **Tests d'intégration** entre composants
- ✅ **Rapports multiples** (texte, JSON, Markdown, HTML)
- ✅ **Couverture de code** avec pytest-cov
- ✅ **Timeouts** pour éviter les blocages
- ✅ **Fixtures** réutilisables

**Architecture du système de tests**:
```
run_tests.py (script principal)
    ↓
pytest (framework)
    ↓
├── test_file_tools.py
├── test_shell_tools.py
├── test_memory_tools.py
├── test_api_tools.py
└── test_test_runner.py
```

**Options du script `run_tests.py`**:
- `--coverage` : Génère un rapport de couverture
- `--verbose` : Mode verbeux
- `--format` : Format de sortie (text/json/markdown)
- `--output` : Fichier de sortie
- `--timeout` : Timeout par test (défaut: 300s)

**Tests effectués**:
- ✅ Exécution complète du script `run_tests.py`
- ✅ Tests unitaires pour chaque module
- ✅ Tests d'intégration entre outils
- ✅ Validation des fixtures
- ✅ Génération de rapports
- ✅ Intégration GitHub Actions simulée

**Performance**:
- Temps d'exécution total : < 30 secondes
- Couverture de code : > 80% (objectif)
- Tests parallélisables
- Faible consommation mémoire

**Décisions techniques**:
1. **pytest** comme framework principal (plus flexible que unittest)
2. **pytest-cov** pour la couverture de code
3. **pytest-timeout** pour éviter les blocages
4. **pytest-html** pour les rapports HTML
5. **GitHub Actions** pour l'intégration continue
6. **Structure modulaire** avec fixtures réutilisables
7. **Script wrapper** `run_tests.py` pour une expérience utilisateur uniforme

**Bonnes pratiques implémentées**:
1. Tests indépendants et isolés
2. Nettoyage automatique des ressources temporaires
3. Messages d'erreur clairs et informatifs
4. Documentation complète de chaque test
5. Marqueurs pour organiser les tests (slow, integration, unit)

**Intégration Continue (GitHub Actions)**:
- Exécution automatique sur push/pull request
- Tests sur Python 3.9, 3.10, 3.11
- Génération de rapports HTML
- Upload des artefacts de test
- Vérification automatique des résultats
- Linting avec flake8, black, isort, mypy

**Prochaines étapes pour les tests**:
- [ ] Ajouter des tests pour les outils web
- [ ] Implémenter des tests de performance
- [ ] Ajouter des tests end-to-end
- [ ] Intégrer avec Codecov
- [ ] Ajouter des tests de sécurité

**Impact sur le projet**:
- ✅ **Qualité améliorée** : Détection précoce des bugs
- ✅ **Maintenance facilitée** : Refactoring sécurisé
- ✅ **Documentation vivante** : Tests comme documentation
- ✅ **Intégration continue** : Déploiement fiable
- ✅ **Confiance accrue** : Code testé = code fiable

**Liens**:
- [Documentation complète des tests](../tests/README.md)
- [Configuration GitHub Actions](../.github/workflows/tests.yml)
- [Script principal des tests](../run_tests.py)
