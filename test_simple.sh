#!/bin/bash
# Test simple de mémoire contextuelle

echo "Test de la mémoire contextuelle"
echo "================================"
echo ""
echo "Instructions: Je vais soumettre plusieurs commandes liées."
echo "L'agent doit se souvenir du contexte entre chaque commande."
echo ""

# Supprimer l'ancien fichier de test s'il existe
rm -f calculator.py

# Activer l'environnement virtuel et lancer l'application
source venv/bin/activate
CUDA_VISIBLE_DEVICES=0 python -u main.py <<EOF
crée un fichier calculator.py avec une fonction add qui additionne deux nombres
ajoute aussi une fonction subtract
maintenant ajoute multiply et divide
affiche moi le contenu du fichier calculator.py
/quit
EOF

echo ""
echo "================================"
echo "Vérification du résultat"
echo "================================"

if [ -f "calculator.py" ]; then
    echo "✅ Fichier créé"
    echo ""
    echo "Contenu:"
    cat calculator.py
    echo ""
    
    # Vérifier les fonctions
    for func in add subtract multiply divide; do
        if grep -q "def $func" calculator.py; then
            echo "✅ Fonction $func présente"
        else
            echo "❌ Fonction $func manquante"
        fi
    done
else
    echo "❌ Fichier calculator.py non créé"
fi
