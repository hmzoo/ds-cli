#!/usr/bin/env python3
"""
Test de la mémoire contextuelle de l'agent
Vérifie que l'agent garde l'objectif en mémoire sur plusieurs itérations
"""

import subprocess
import time
import sys

def test_context_memory():
    """Test la mémoire contextuelle avec un projet simple"""
    
    print("="*60)
    print("TEST DE LA MÉMOIRE CONTEXTUELLE")
    print("="*60)
    print()
    
    # Séquence de commandes pour tester la mémoire
    test_sequence = [
        ("crée un fichier calculator.py avec une fonction add et subtract", 
         "Objectif initial: créer calculateur"),
        
        ("ajoute aussi une fonction multiply",
         "Itération 2: ajout fonction (doit se souvenir du fichier calculator.py)"),
        
        ("maintenant ajoute une fonction divide avec gestion de division par zéro",
         "Itération 3: ajout fonction avec contrainte"),
        
        ("est-ce que toutes les fonctions sont bien dans le même fichier?",
         "Itération 4: vérification (doit se rappeler qu'on travaille sur calculator.py)"),
        
        ("affiche moi le contenu complet du fichier",
         "Itération 5: lecture (doit savoir quel fichier sans que je le nomme)"),
    ]
    
    print("📝 Scénario de test:")
    for i, (cmd, desc) in enumerate(test_sequence, 1):
        print(f"  {i}. {desc}")
        print(f"     → \"{cmd}\"")
    print()
    
    # Préparer les commandes pour stdin
    commands_input = "\n".join([cmd for cmd, _ in test_sequence])
    commands_input += "\n/quit\n"
    
    print("🚀 Lancement du test...")
    print("="*60)
    print()
    
    # Lancer l'application avec les commandes
    process = subprocess.Popen(
        ['./run-gpu.sh'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd='/home/mrpink/perso/ds-cli'
    )
    
    try:
        # Envoyer les commandes et récupérer la sortie
        output, _ = process.communicate(input=commands_input, timeout=300)
        
        print(output)
        print()
        print("="*60)
        print("✅ Test terminé")
        print("="*60)
        print()
        
        # Vérifier si le fichier a été créé
        import os
        calc_path = '/home/mrpink/perso/ds-cli/calculator.py'
        if os.path.exists(calc_path):
            print("✅ Fichier calculator.py créé")
            with open(calc_path, 'r') as f:
                content = f.read()
            
            # Vérifier la présence des fonctions
            functions = ['add', 'subtract', 'multiply', 'divide']
            found_functions = []
            missing_functions = []
            
            for func in functions:
                if f'def {func}' in content:
                    found_functions.append(func)
                else:
                    missing_functions.append(func)
            
            print(f"✅ Fonctions trouvées: {', '.join(found_functions)}")
            if missing_functions:
                print(f"⚠️  Fonctions manquantes: {', '.join(missing_functions)}")
            
            # Vérifier la gestion de division par zéro
            if 'ZeroDivisionError' in content or 'division' in content.lower():
                print("✅ Gestion de la division par zéro présente")
            else:
                print("⚠️  Gestion de la division par zéro non détectée")
            
            print()
            print("📄 Contenu du fichier:")
            print("-"*60)
            print(content)
            print("-"*60)
        else:
            print("❌ Fichier calculator.py non créé")
        
        return process.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout: le test a pris trop de temps")
        process.kill()
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_context_memory()
    sys.exit(0 if success else 1)
