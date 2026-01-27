"""Outils pour Git - gestion de version"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any


def git_status(repository_path: str = ".") -> Dict[str, Any]:
    """
    Affiche le statut Git du dépôt
    
    Args:
        repository_path: Chemin vers le dépôt (défaut: répertoire courant)
        
    Returns:
        Dict contenant les fichiers modifiés, ajoutés, supprimés
    """
    try:
        repo_path = Path(repository_path).resolve()
        
        # Vérifier si c'est un dépôt Git
        if not (repo_path / ".git").exists():
            return {"error": f"Pas de dépôt Git trouvé dans {repo_path}"}
        
        # Exécuter git status --porcelain
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {"error": f"Erreur git status: {result.stderr}"}
        
        # Parser la sortie
        modified = []
        added = []
        deleted = []
        untracked = []
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
                
            status = line[:2]
            filename = line[3:]
            
            if status == ' M' or status == 'M ':
                modified.append(filename)
            elif status == 'A ' or status == 'AM':
                added.append(filename)
            elif status == ' D' or status == 'D ':
                deleted.append(filename)
            elif status == '??':
                untracked.append(filename)
            elif status == 'MM':
                modified.append(filename)
        
        # Branche courante
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
        
        return {
            "branch": branch,
            "modified": modified,
            "added": added,
            "deleted": deleted,
            "untracked": untracked,
            "total_changes": len(modified) + len(added) + len(deleted) + len(untracked),
            "clean": len(modified) + len(added) + len(deleted) + len(untracked) == 0
        }
        
    except subprocess.TimeoutExpired:
        return {"error": "Timeout lors de l'exécution de git status"}
    except Exception as e:
        return {"error": f"Erreur: {str(e)}"}


def git_diff(file_path: str = "", repository_path: str = ".", staged: bool = False) -> Dict[str, Any]:
    """
    Affiche les différences Git
    
    Args:
        file_path: Fichier spécifique (vide = tous les fichiers)
        repository_path: Chemin vers le dépôt
        staged: True pour diff --staged, False pour diff working tree
        
    Returns:
        Dict contenant le diff
    """
    try:
        repo_path = Path(repository_path).resolve()
        
        if not (repo_path / ".git").exists():
            return {"error": f"Pas de dépôt Git trouvé dans {repo_path}"}
        
        # Commande git diff
        cmd = ["git", "diff"]
        if staged:
            cmd.append("--staged")
        if file_path:
            cmd.append(file_path)
        
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return {"error": f"Erreur git diff: {result.stderr}"}
        
        diff_output = result.stdout
        
        # Compter les changements
        lines_added = diff_output.count('\n+') - diff_output.count('\n+++')
        lines_removed = diff_output.count('\n-') - diff_output.count('\n---')
        
        return {
            "diff": diff_output,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "has_changes": len(diff_output.strip()) > 0,
            "staged": staged,
            "file": file_path if file_path else "all files"
        }
        
    except subprocess.TimeoutExpired:
        return {"error": "Timeout lors de l'exécution de git diff"}
    except Exception as e:
        return {"error": f"Erreur: {str(e)}"}


def git_commit(message: str, repository_path: str = ".", add_all: bool = False) -> Dict[str, Any]:
    """
    Crée un commit Git
    
    Args:
        message: Message du commit
        repository_path: Chemin vers le dépôt
        add_all: Si True, fait git add . avant le commit
        
    Returns:
        Dict avec le résultat du commit
    """
    try:
        repo_path = Path(repository_path).resolve()
        
        if not (repo_path / ".git").exists():
            return {"error": f"Pas de dépôt Git trouvé dans {repo_path}"}
        
        if not message or not message.strip():
            return {"error": "Message de commit vide"}
        
        # git add . si demandé
        if add_all:
            add_result = subprocess.run(
                ["git", "add", "."],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if add_result.returncode != 0:
                return {"error": f"Erreur git add: {add_result.stderr}"}
        
        # git commit
        commit_result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if commit_result.returncode != 0:
            # Vérifier si c'est juste "rien à commiter"
            if "nothing to commit" in commit_result.stdout or "nothing added to commit" in commit_result.stdout:
                return {
                    "success": False,
                    "message": "Rien à commiter (working tree clean)",
                    "output": commit_result.stdout
                }
            return {"error": f"Erreur git commit: {commit_result.stderr}"}
        
        # Parser la sortie pour obtenir le hash
        output = commit_result.stdout
        commit_hash = None
        files_changed = 0
        
        for line in output.split('\n'):
            if line.startswith('['):
                # Ex: [main 1a2b3c4] message
                parts = line.split()
                if len(parts) >= 2:
                    commit_hash = parts[1].rstrip(']')
            elif 'file' in line and 'changed' in line:
                # Ex: 3 files changed, 15 insertions(+), 2 deletions(-)
                try:
                    files_changed = int(line.split()[0])
                except ValueError:
                    pass
        
        return {
            "success": True,
            "message": message,
            "commit_hash": commit_hash,
            "files_changed": files_changed,
            "output": output,
            "added_all": add_all
        }
        
    except subprocess.TimeoutExpired:
        return {"error": "Timeout lors de l'exécution de git commit"}
    except Exception as e:
        return {"error": f"Erreur: {str(e)}"}


def git_log(max_count: int = 10, repository_path: str = ".") -> Dict[str, Any]:
    """
    Affiche l'historique Git
    
    Args:
        max_count: Nombre maximum de commits à afficher
        repository_path: Chemin vers le dépôt
        
    Returns:
        Dict contenant la liste des commits
    """
    try:
        repo_path = Path(repository_path).resolve()
        
        if not (repo_path / ".git").exists():
            return {"error": f"Pas de dépôt Git trouvé dans {repo_path}"}
        
        # git log avec format personnalisé
        result = subprocess.run(
            ["git", "log", f"--max-count={max_count}", "--pretty=format:%H|%an|%ae|%ad|%s", "--date=short"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {"error": f"Erreur git log: {result.stderr}"}
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
                
            parts = line.split('|')
            if len(parts) == 5:
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "email": parts[2],
                    "date": parts[3],
                    "message": parts[4]
                })
        
        return {
            "commits": commits,
            "count": len(commits)
        }
        
    except subprocess.TimeoutExpired:
        return {"error": "Timeout lors de l'exécution de git log"}
    except Exception as e:
        return {"error": f"Erreur: {str(e)}"}


def git_branch_list(repository_path: str = ".") -> Dict[str, Any]:
    """
    Liste les branches Git
    
    Args:
        repository_path: Chemin vers le dépôt
        
    Returns:
        Dict contenant la liste des branches
    """
    try:
        repo_path = Path(repository_path).resolve()
        
        if not (repo_path / ".git").exists():
            return {"error": f"Pas de dépôt Git trouvé dans {repo_path}"}
        
        # git branch -a (toutes les branches)
        result = subprocess.run(
            ["git", "branch", "-a"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {"error": f"Erreur git branch: {result.stderr}"}
        
        branches = []
        current_branch = None
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
                
            line = line.strip()
            is_current = line.startswith('*')
            
            branch_name = line.lstrip('* ')
            
            if is_current:
                current_branch = branch_name
            
            branches.append({
                "name": branch_name,
                "current": is_current,
                "remote": branch_name.startswith('remotes/')
            })
        
        return {
            "branches": branches,
            "current_branch": current_branch,
            "count": len(branches)
        }
        
    except subprocess.TimeoutExpired:
        return {"error": "Timeout lors de l'exécution de git branch"}
    except Exception as e:
        return {"error": f"Erreur: {str(e)}"}
