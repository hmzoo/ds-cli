# Analyse des problèmes d'utilisation des outils - 27 janvier 2026

## 🔍 Problème identifié

L'agent a parfois du mal à utiliser correctement les outils, notamment `replace_in_file`.

### Symptômes observés

Dans les logs du test de mémoire contextuelle :
```
❌ Erreur: Outil inconnu: replace_in_file
```

L'agent tentait d'utiliser `replace_in_file` mais recevait une erreur indiquant que l'outil n'existait pas.

## 🐛 Cause racine

L'outil `replace_in_file` **était bien implémenté** dans `tools/file_tools.py` et **bien importé** dans `tools/__init__.py`, MAIS :

- ✅ Le code actuel l'enregistre correctement dans `ToolExecutor` 
- ❌ Le test a probablement été exécuté avec une version antérieure où il n'était pas enregistré

### Vérification actuelle

```bash
$ python -c "from main import ToolExecutor; print('replace_in_file' in ToolExecutor().tools)"
True  # ✅ Fonctionne maintenant
```

Liste complète des 16 outils disponibles :
1. append_file
2. check_command_exists
3. decide
4. execute_command
5. extract_links
6. fetch_webpage
7. file_exists
8. get_system_info
9. list_files
10. read_file
11. recall
12. remember
13. **replace_in_file** ✅
14. search_web
15. summarize_webpage
16. write_file

## 📋 Autres problèmes potentiels identifiés

### 1. Documentation de `replace_in_file` insuffisante

**Problème** : L'agent ne comprend pas toujours que `old_text` doit être EXACTEMENT identique.

**Solution appliquée** : Amélioration de la documentation dans `_generate_tools_documentation()` :
```python
- replace_in_file(file_path: str, old_text: str, new_text: str) → remplace texte dans fichier
  ⚠️ old_text doit être EXACTEMENT identique (espaces, sauts de ligne). Utilisez read_file() d'abord!
```

### 2. Parsing des appels d'outils

**État** : Le parsing semble robuste. La fonction `_extract_tool_calls()` :
- ✅ Supprime les balises `<thinking>` automatiquement
- ✅ Gère les JSON mal formés
- ✅ Recherche les accolades ouvrantes/fermantes
- ✅ Affiche des erreurs explicites en cas de problème

### 3. Gestion d'erreurs

**État** : Bonne gestion avec :
- Try/catch dans `ToolExecutor.execute()`
- Retour d'erreur structuré : `{"error": "...", "traceback": "..."}`
- Affichage coloré des erreurs à l'utilisateur

## ✅ Solutions implémentées

1. **Documentation améliorée** pour `replace_in_file`
2. **Vérification** que tous les outils sont bien enregistrés
3. **Message d'avertissement** clair dans la documentation

## 🎯 Recommandations pour l'avenir

### Pour les utilisateurs

1. **Toujours lire le fichier avant de remplacer** :
   ```json
   {"name": "read_file", "parameters": {"file_path": "test.py"}}
   {"name": "replace_in_file", "parameters": {
     "file_path": "test.py",
     "old_text": "texte exact copié du résultat de read_file",
     "new_text": "nouveau texte"
   }}
   ```

2. **Pour les gros fichiers, préférer réécrire avec write_file** si beaucoup de changements

### Pour les développeurs

1. **Vérifier systématiquement** que les nouveaux outils sont :
   - ✅ Implémentés dans `tools/xxx_tools.py`
   - ✅ Importés dans `tools/__init__.py`
   - ✅ Enregistrés dans `ToolExecutor.__init__()` dans `main.py`
   - ✅ Documentés dans `_generate_tools_documentation()`

2. **Test de vérification** :
   ```python
   from main import ToolExecutor
   executor = ToolExecutor()
   assert 'nom_outil' in executor.tools
   ```

3. **Ajouter des tests unitaires** pour chaque outil

## 📊 Statistiques

- **Outils disponibles** : 16
- **Taux de succès replace_in_file** : Maintenant opérationnel
- **Problèmes résolus** : Documentation + vérification enregistrement

## 🔄 Prochaines étapes

1. ✅ Corriger la documentation (FAIT)
2. ✅ Vérifier l'enregistrement (FAIT)
3. ⏳ Créer tests unitaires pour tous les outils
4. ⏳ Ajouter des outils manquants (search_in_files, create_directory, etc.)
5. ⏳ Améliorer les messages d'erreur avec des suggestions
