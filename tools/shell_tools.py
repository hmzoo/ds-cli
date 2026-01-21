"""
Outils d'exécution de commandes shell pour l'agent DeepSeek
"""

import subprocess
import shlex
from typing import Dict, Optional, List


def execute_command(
    command: str,
    timeout: int = 30,
    check: bool = False,
    shell: bool = False
) -> Dict[str, any]:
    """
    Exécute une commande shell et retourne le résultat
    
    Args:
        command: Commande à exécuter
        timeout: Timeout en secondes (défaut: 30)
        check: Lever une exception si returncode != 0
        shell: Utiliser shell=True (DANGER: seulement si nécessaire)
        
    Returns:
        Dictionnaire avec stdout, stderr, returncode, success
    """
    try:
        # Parser la commande si shell=False
        if not shell:
            cmd_parts = shlex.split(command)
        else:
            cmd_parts = command
        
        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
            shell=shell
        )
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": command
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Timeout après {timeout} secondes",
            "command": command,
            "error": "timeout"
        }
    except FileNotFoundError as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Commande non trouvée: {str(e)}",
            "command": command,
            "error": "not_found"
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "command": command,
            "error": "exception"
        }


def check_command_exists(command: str) -> bool:
    """
    Vérifie si une commande existe dans le PATH
    
    Args:
        command: Nom de la commande
        
    Returns:
        True si la commande existe
    """
    result = execute_command(f"which {command}", timeout=5)
    return result["success"]


def get_environment_variable(var_name: str) -> Optional[str]:
    """
    Récupère une variable d'environnement
    
    Args:
        var_name: Nom de la variable
        
    Returns:
        Valeur de la variable ou None
    """
    import os
    return os.getenv(var_name)


def list_processes(filter_pattern: Optional[str] = None) -> List[Dict]:
    """
    Liste les processus en cours
    
    Args:
        filter_pattern: Pattern pour filtrer (ex: "python")
        
    Returns:
        Liste de dictionnaires avec info sur les processus
    """
    if filter_pattern:
        cmd = f"ps aux | grep {filter_pattern} | grep -v grep"
    else:
        cmd = "ps aux"
    
    result = execute_command(cmd, shell=True)
    
    if not result["success"]:
        return []
    
    processes = []
    lines = result["stdout"].strip().split('\n')
    
    # Skip header
    for line in lines[1:]:
        if line.strip():
            processes.append({"line": line})
    
    return processes


def get_system_info() -> Dict[str, str]:
    """
    Récupère des informations système
    
    Returns:
        Dictionnaire avec infos système
    """
    info = {}
    
    # OS
    result = execute_command("uname -s")
    if result["success"]:
        info["os"] = result["stdout"].strip()
    
    # Kernel
    result = execute_command("uname -r")
    if result["success"]:
        info["kernel"] = result["stdout"].strip()
    
    # Architecture
    result = execute_command("uname -m")
    if result["success"]:
        info["arch"] = result["stdout"].strip()
    
    # Hostname
    result = execute_command("hostname")
    if result["success"]:
        info["hostname"] = result["stdout"].strip()
    
    # Python version
    result = execute_command("python3 --version")
    if result["success"]:
        info["python"] = result["stdout"].strip()
    
    # Working directory
    import os
    info["cwd"] = os.getcwd()
    
    return info


# Liste des commandes sûres (whitelist)
SAFE_COMMANDS = {
    'ls', 'cat', 'head', 'tail', 'grep', 'find', 'wc', 'pwd',
    'which', 'whoami', 'date', 'echo', 'ps', 'df', 'du',
    'python3', 'pip3', 'git', 'tree', 'file', 'stat'
}


def is_safe_command(command: str) -> bool:
    """
    Vérifie si une commande est dans la whitelist des commandes sûres
    
    Args:
        command: Commande à vérifier
        
    Returns:
        True si la commande est considérée comme sûre
    """
    cmd_parts = shlex.split(command)
    if not cmd_parts:
        return False
    
    base_cmd = cmd_parts[0].split('/')[-1]  # Enlever le path
    return base_cmd in SAFE_COMMANDS
