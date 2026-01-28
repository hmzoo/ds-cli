# Changelog

All notable changes to the DS-CLI project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Mémoire des conversations** (28/01/2026)
  - Sauvegarde automatique de la conversation à la sortie (/quit, Ctrl+C)
  - Chargement automatique de la dernière conversation au démarrage
  - Commande `/last` pour afficher la dernière conversation
  - Extraction automatique des sujets et actions réussies
  - Stockage dans Qdrant avec indexation sémantique
  - Documentation complète dans [CONVERSATION_MEMORY.md](docs/CONVERSATION_MEMORY.md)
- **Détection de boucles infinies** (28/01/2026)
  - Détection automatique des appels d'outils répétés (max 3 fois)
  - Message d'erreur explicite avec suggestion d'alternative
  - Compteur de boucles dans les statistiques
  - Empêche l'agent de répéter indéfiniment une commande qui échoue
- **Correction du bug de tagging** (28/01/2026)
  - Protection anti-re-tagging pour éviter [CONTEXT] [CONTEXT] [CONTEXT]...
  - Vérification si le message est déjà taggé avant d'ajouter un nouveau tag
  - Retrait de patterns ambigus (context, info, detail) des context_patterns
- **Métriques de performance du contexte** (22/01/2026)
  - Compteurs: compressions, doublons éliminés, filtrages par importance
  - Tokens économisés calculés automatiquement
  - Répartition CRITICAL/IMPORTANT/CONTEXT en %
  - Affichage détaillé dans /stats
  - Suivi de l'efficacité des optimisations
- **Compression du contexte** (22/01/2026)
  - Élimination automatique des répétitions (hash-based deduplication)
  - Compression des longues sorties d'outils (>5000 chars → 3000 chars)
  - Économie estimée: 15-30% des messages, 500-1500 tokens par conversation
- **Système de tags d'importance** (22/01/2026)
  - Tags automatiques: [CRITICAL], [IMPORTANT], [CONTEXT]
  - Filtrage intelligent basé sur l'importance
  - Priorité CRITICAL > IMPORTANT > CONTEXT lors de la troncature
  - Patterns reconnus: erreurs, actions, préférences
- **readline support**: Édition de texte avec les flèches et historique des commandes (22/01/2026)
  - Navigation dans le texte (← → Ctrl+A Ctrl+E)
  - Historique persistant (↑ ↓) dans ~/.deepseek_agent_history
  - Raccourcis d'édition (Ctrl+U Ctrl+K Ctrl+W)
  - Documentation des raccourcis dans /help
- Initial project structure and documentation
- Core CLI framework with Click
- Basic tool implementations (file, shell, memory, web)
- Vector memory system with Qdrant integration
- Configuration management system
- Plugin architecture
- Comprehensive test suite
- Development tools and pre-commit hooks
- Documentation framework

### Changed
- **_truncate_history()**: Intégration compression + filtrage avant troncature classique (22/01/2026)
- **add_message()**: Tagging automatique de tous les messages user/assistant (22/01/2026)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- **Prompt dysfonctionnel**: Les flèches n'affichent plus de caractères de contrôle (22/01/2026)
- **Répétitions contexte**: Messages dupliqués éliminés automatiquement (22/01/2026)
- **Contexte surchargé**: Messages peu importants filtrés intelligemment (22/01/2026)
- N/A (initial release)

### Security
- N/A (initial release)

## [0.1.0] - 2024-01-01

### Added
- Initial release of DS-CLI
- Basic CLI interface with subcommands
- File operations (read, write, list, search)
- Shell command execution with sandboxing
- Memory system with Qdrant vector database
- Web search and content extraction
- DeepSeek API integration
- Configuration via YAML/JSON/TOML
- Plugin system for extensibility
- Logging and monitoring
- Test framework with pytest
- Documentation with Sphinx

### Features
- **CLI Commands**:
  - `ds-cli init`: Initialize configuration
  - `ds-cli start`: Start development session
  - `ds-cli develop`: Agent-assisted development
  - `ds-cli file`: File operations
  - `ds-cli shell`: Shell commands
  - `ds-cli memory`: Memory operations
  - `ds-cli web`: Web operations
  - `ds-cli config`: Configuration management
  - `ds-cli plugin`: Plugin management

- **Memory System**:
  - Vector storage with Qdrant
  - Context-aware retrieval
  - Semantic search
  - Metadata filtering

- **Development Tools**:
  - Code analysis
  - Auto-documentation
  - Test generation
  - Security scanning

### Dependencies
- Core: click, rich, pyyaml, toml, requests
- Memory: qdrant-client, sentence-transformers
- Web: beautifulsoup4, lxml, tavily-python
- Development: pytest, black, isort, flake8, mypy, ruff
- Documentation: sphinx, sphinx-rtd-theme

### Installation
```bash
pip install ds-cli
```

### Configuration
Create `~/.config/ds-cli/config.yaml`:
```yaml
api:
  deepseek:
    api_key: ${DEEPSEEK_API_KEY}
    model: deepseek-chat

memory:
  qdrant:
    host: localhost
    port: 6333
```

## [0.2.0] - Planned

### Planned Features
- **Advanced Memory**:
  - Multi-collection support
  - Time-based filtering
  - Relevance scoring
  - Memory pruning

- **Enhanced Tools**:
  - Git integration
  - Docker operations
  - Database interactions
  - API testing

- **UI Improvements**:
  - Interactive mode
  - Progress bars
  - Rich tables
  - Syntax highlighting

- **Performance**:
  - Async operations
  - Caching system
  - Batch processing
  - Memory optimization

- **Security**:
  - API key encryption
  - Audit logging
  - Permission system
  - Input validation

### Breaking Changes
- Configuration format updates
- API endpoint changes
- Command restructuring

## [0.3.0] - Planned

### Planned Features
- **Cloud Integration**:
  - AWS/GCP/Azure support
  - Kubernetes operations
  - Cloud storage
  - Serverless functions

- **Collaboration**:
  - Multi-user support
  - Team workspaces
  - Shared memory
  - Collaboration tools

- **AI Enhancements**:
  - Multiple model support
  - Fine-tuning tools
  - Prompt engineering
  - Model evaluation

- **Monitoring**:
  - Metrics dashboard
  - Performance tracking
  - Usage analytics
  - Health checks

## Upgrade Guide

### From 0.1.0 to 0.2.0
1. Backup your configuration files
2. Update package: `pip install --upgrade ds-cli`
3. Migrate configuration using: `ds-cli config migrate`
4. Update any custom plugins

### Configuration Migration
Old format:
```yaml
api_key: your_key
model: deepseek-chat
```

New format:
```yaml
api:
  deepseek:
    api_key: your_key
    model: deepseek-chat
```

## Deprecation Notices

### Version 0.1.0
No deprecations in initial release.

### Version 0.2.0
- Old configuration format will be deprecated
- Some CLI commands may be renamed
- Certain API endpoints may change

## Security Updates

### Version 0.1.0
- Initial security implementation
- API key management
- Input sanitization
- Safe shell execution

### Version 0.2.0
- Enhanced encryption
- Audit trail
- Permission model
- Vulnerability scanning

## Known Issues

### Version 0.1.0
1. Memory system requires Qdrant running locally
2. Web search depends on Tavily API
3. Large file operations may be slow
4. Limited error recovery

### Workarounds
1. Use Docker for Qdrant: `docker run -p 6333:6333 qdrant/qdrant`
2. Set `TAVILY_API_KEY` environment variable
3. Process files in chunks
4. Implement manual error handling

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- GitHub Issues: https://github.com/your-username/ds-cli/issues
- Documentation: https://github.com/your-username/ds-cli/docs
- Discussions: https://github.com/your-username/ds-cli/discussions

---

*This changelog is automatically generated from commit messages and pull requests.*
