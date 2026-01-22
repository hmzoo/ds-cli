#!/usr/bin/env python3
"""Test simple de l'édition readline"""

import sys
import os

# Test si readline est disponible
try:
    import readline
    print("✅ readline est disponible")
    print(f"📝 Historique: ~/.deepseek_agent_history")
    
    # Test de l'historique
    history_file = os.path.expanduser('~/.deepseek_agent_history')
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            lines = f.readlines()
        print(f"📊 Historique: {len(lines)} commandes sauvegardées")
        if lines:
            print(f"📝 Dernière commande: {lines[-1].strip()}")
    else:
        print("ℹ️  Pas d'historique trouvé")
        
    print("\n✨ Test interactif:")
    print("Tapez du texte et utilisez les flèches pour tester l'édition")
    print("Ctrl+C pour quitter\n")
    
    try:
        while True:
            text = input("Test> ").strip()
            if text:
                print(f"Vous avez tapé: {text}")
                if text.lower() in ['quit', 'exit', 'q']:
                    break
    except KeyboardInterrupt:
        print("\n👋 Au revoir!")
        
except ImportError:
    print("❌ readline n'est pas disponible")
    print("Sur Windows, installez: pip install pyreadline3")
    sys.exit(1)
