# 💾 Mémoire des Conversations

## Vue d'ensemble

L'agent sauvegarde automatiquement chaque conversation dans la base Qdrant. Cela permet de :
- Retrouver le contexte des sessions précédentes
- Suivre l'historique des actions effectuées
- Rechercher des informations dans les anciennes conversations

## Fonctionnalités

### Sauvegarde automatique

La conversation est **automatiquement sauvegardée** lorsque vous quittez l'agent :
- Avec `/quit` ou `/q`
- Avec Ctrl+C
- Avec Ctrl+D

**Informations sauvegardées** :
- Résumé de la conversation
- Date et heure
- Sujets abordés (5 max)
- Actions réussies (5 max)

### Chargement au démarrage

Au lancement de l'agent, le **résumé de la dernière conversation** s'affiche automatiquement :

```
📜 Dernière conversation:
  Conversation du 2026-01-28 15:30: Correction du bug de boucle infinie dans l'agent
  Sujets: regarde pourquoi l, agent se mets, en boucle
  Actions: Ajout de la détection de boucles, Correction du tagging répétitif
```

### Commande `/last`

Affiche à tout moment le résumé de la dernière conversation :

```bash
/last
```

## Format de stockage

Les conversations sont stockées dans Qdrant avec :

```python
{
    "type": "conversation",
    "summary": "Conversation du 2026-01-28 15:30: ...",
    "topics": ["sujet 1", "sujet 2", ...],
    "outcomes": ["action 1", "action 2", ...],
    "timestamp": "2026-01-28T15:30:45.123456"
}
```

## Recherche dans l'historique

Les conversations sont indexées sémantiquement, vous pouvez :

1. **Utiliser l'outil `search_facts`** pour rechercher dans toutes les données (y compris conversations)
2. **Demander à l'agent** : "Qu'est-ce qu'on a fait la dernière fois ?"

## Architecture technique

### Implémentation

- **Classe** : `DeepSeekAgent`
- **Méthodes** :
  - `save_conversation()` : Sauvegarde la session actuelle
  - `load_last_conversation()` : Charge le résumé de la dernière session

### Extraction automatique

L'agent extrait automatiquement :

**Sujets** : Premiers mots des messages utilisateur (jusqu'à 5 mots)

**Actions réussies** : Messages contenant "succès" ou "créé"

**Résumé** : Demande initiale + timestamp

## Exemple d'utilisation

```bash
# Session 1
$ ./run.sh
📜 Dernière conversation:
  Conversation du 2026-01-28 14:00: Création d'un module de tests
  Sujets: créer des tests
  Actions: Tests créés avec succès

👤 Vous: corrige le bug dans main.py
🤖 Agent: [fait les corrections...]

👤 Vous: /quit
💾 Sauvegarde de la conversation...
✅ Conversation sauvegardée
👋 Au revoir !

# Session 2 (plus tard)
$ ./run.sh
📜 Dernière conversation:
  Conversation du 2026-01-28 15:00: corrige le bug dans main.py
  Sujets: corrige le bug
  Actions: Bug corrigé avec succès

👤 Vous: qu'est-ce qu'on a fait la dernière fois ?
🤖 Agent: La dernière fois, nous avons corrigé un bug dans main.py...
```

## Commandes liées

- `/last` - Afficher la dernière conversation
- `/backup` - Sauvegarder toute la mémoire Qdrant (incluant conversations)
- `/backups` - Lister les sauvegardes disponibles
- `/restore <file>` - Restaurer depuis un backup

## Voir aussi

- [memory_tools.py](../tools/memory_tools.py) - Implémentation de la mémoire
- [qdrant_backup.py](../tools/qdrant_backup.py) - Système de backup
- [IMPLEMENTATION_CONTEXTE.md](IMPLEMENTATION_CONTEXTE.md) - Gestion du contexte
