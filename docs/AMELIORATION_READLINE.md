# Amélioration de l'édition de texte dans le prompt

## Problème identifié

Le prompt utilisait `input()` de base qui ne gère pas correctement :
- L'édition de texte avec les flèches ← →
- La navigation dans l'historique avec ↑ ↓
- Les raccourcis clavier standard (Ctrl+A, Ctrl+E, etc.)

Les caractères de contrôle s'affichaient au lieu d'être interprétés.

## Solution implémentée

### 1. Support de readline

Ajout du module `readline` (natif sous Linux/macOS) :

```python
import readline

# Configuration de l'historique
HISTORY_FILE = os.path.expanduser('~/.deepseek_agent_history')
if os.path.exists(HISTORY_FILE):
    readline.read_history_file(HISTORY_FILE)
readline.set_history_length(1000)
```

### 2. Fonctionnalités disponibles

**Navigation dans le texte :**
- `←` / `→` : Déplacer le curseur caractère par caractère
- `Ctrl+A` : Aller au début de la ligne
- `Ctrl+E` : Aller à la fin de la ligne

**Édition :**
- `Ctrl+U` : Effacer toute la ligne
- `Ctrl+K` : Effacer du curseur jusqu'à la fin
- `Ctrl+W` : Effacer le mot précédent
- `Backspace` / `Delete` : Effacer caractère par caractère

**Historique :**
- `↑` : Commande précédente
- `↓` : Commande suivante
- Historique persistant entre les sessions (1000 commandes max)

### 3. Sauvegarde automatique

L'historique est sauvegardé automatiquement :
- À la sortie normale (`/quit`)
- Sur Ctrl+C (KeyboardInterrupt)
- Sur Ctrl+D (EOFError)

### 4. Compatibilité

- **Linux/macOS** : readline est natif, aucune dépendance supplémentaire
- **Windows** : readline n'est pas disponible, fallback sur `input()` standard

Pour Windows, installer : `pip install pyreadline3`

## Fichier d'historique

Emplacement : `~/.deepseek_agent_history`

Format : texte simple, une commande par ligne

Pour effacer l'historique :
```bash
rm ~/.deepseek_agent_history
```

## Test

```bash
./run.sh
```

Testez :
1. Tapez un texte long
2. Utilisez ← → pour vous déplacer
3. Utilisez Ctrl+A et Ctrl+E
4. Tapez une commande et quittez
5. Relancez et utilisez ↑ pour retrouver votre historique

## Documentation utilisateur

Les raccourcis sont documentés dans `/help` :
```
⌨️  Édition de texte:
  ← →    - Déplacer le curseur
  ↑ ↓    - Naviguer dans l'historique
  Ctrl+A - Début de ligne
  Ctrl+E - Fin de ligne
  Ctrl+U - Effacer la ligne
  Ctrl+K - Effacer jusqu'à la fin
```

## Impact

- ✅ Édition de texte fluide
- ✅ Correction de fautes facilitée
- ✅ Navigation dans l'historique
- ✅ Aucune dépendance supplémentaire (Linux/macOS)
- ✅ Historique persistant entre les sessions
