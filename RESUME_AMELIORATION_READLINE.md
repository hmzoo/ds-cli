# Résumé des améliorations - 22 janvier 2026

## Problème résolu

**Symptôme** : Le prompt avait des dysfonctionnements quand on voulait corriger du texte avec les flèches ← →

Les caractères de contrôle ANSI s'affichaient au lieu d'être interprétés :
```
👤 Vous: du texte^[[D^[[D^[[C
```

## Solution

Ajout du support `readline` pour une édition de texte professionnelle.

## Modifications apportées

### 1. main.py
- Import et configuration de `readline`
- Chargement automatique de l'historique au démarrage
- Sauvegarde automatique à la sortie (quit, Ctrl+C, Ctrl+D)
- Limite d'historique : 1000 commandes

### 2. Documentation
- Ajout des raccourcis dans `/help`
- Création de `docs/AMELIORATION_READLINE.md`
- Mise à jour du `CHANGELOG.md`

### 3. Test
- Script `test_readline.py` pour validation

## Fonctionnalités

### Navigation
- `←` `→` : Déplacer le curseur caractère par caractère
- `Ctrl+A` : Début de ligne
- `Ctrl+E` : Fin de ligne

### Édition
- `Ctrl+U` : Effacer la ligne complète
- `Ctrl+K` : Effacer du curseur à la fin
- `Ctrl+W` : Effacer le mot précédent
- `Backspace` / `Delete` : Effacer un caractère

### Historique
- `↑` : Commande précédente
- `↓` : Commande suivante
- Persistance entre sessions dans `~/.deepseek_agent_history`
- 1000 commandes maximum

## Compatibilité

- ✅ **Linux** : readline natif (aucune dépendance)
- ✅ **macOS** : readline natif (aucune dépendance)
- ⚠️ **Windows** : nécessite `pip install pyreadline3`

Sans readline, fallback sur `input()` standard.

## Test

```bash
# Lancer l'agent
./run.sh

# Tester l'édition
👤 Vous: du texte à corriger
# Utiliser ← → pour se déplacer
# Utiliser ↑ pour historique

# Test dédié
python3 test_readline.py
```

## Impact

- 🎯 **Problème résolu** : Édition fluide avec les flèches
- ✨ **Expérience améliorée** : Navigation dans l'historique
- 📝 **Historique persistant** : Retrouver les anciennes commandes
- 🚀 **Aucune dépendance** : Sur Linux/macOS
- 📚 **Documentation** : Raccourcis dans /help

## Prochaines étapes

Pour tester en production :
```bash
./run.sh
```

Testez particulièrement :
1. Édition avec les flèches
2. Navigation dans l'historique
3. Correction de fautes de frappe
4. Persistance de l'historique après redémarrage
