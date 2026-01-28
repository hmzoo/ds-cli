#!/usr/bin/env python3
"""
DeepSeek Dev Agent - Chat CLI interactif avec function calling
Agent de développement autonome avec accès aux outils
"""

import os
import sys
import json
import re
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any
import traceback
from datetime import datetime

# Support pour l'édition de ligne avec les flèches
try:
    import readline
    # Activer l'historique des commandes
    HISTORY_FILE = os.path.expanduser('~/.deepseek_agent_history')
    if os.path.exists(HISTORY_FILE):
        readline.read_history_file(HISTORY_FILE)
    # Limiter l'historique à 1000 commandes
    readline.set_history_length(1000)
    
    # Configuration pour améliorer les performances
    readline.parse_and_bind('tab: complete')
    readline.parse_and_bind('set editing-mode emacs')
    readline.parse_and_bind('set show-all-if-ambiguous on')
    readline.parse_and_bind('set completion-ignore-case on')
    
except ImportError:
    # readline n'est pas disponible (Windows sans pyreadline3)
    readline = None
    HISTORY_FILE = None

# Importer les outils
sys.path.insert(0, str(Path(__file__).parent))
from tools import (
    read_file, write_file, list_files, file_exists, append_file, replace_in_file,
    execute_command, check_command_exists, get_system_info,
    remember, recall, search_facts, decide, get_memory,
    search_web, fetch_webpage, extract_links, summarize_webpage,
    backup_qdrant, restore_qdrant, list_backups, get_backup_stats,
    git_status, git_diff, git_commit, git_log, git_branch_list
)
from qdrant_client.models import Filter, FieldCondition, MatchValue


class Colors:
    """Codes couleurs ANSI pour le terminal"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


class ToolExecutor:
    """Exécuteur d'outils pour l'agent"""
    
    def __init__(self):
        self.tools = {
            # File tools
            'read_file': read_file,
            'write_file': write_file,
            'list_files': list_files,
            'file_exists': file_exists,
            'append_file': append_file,
            'replace_in_file': replace_in_file,
            
            # Shell tools
            'execute_command': execute_command,
            'check_command_exists': check_command_exists,
            'get_system_info': get_system_info,
            
            # Memory tools
            'remember': remember,
            'recall': recall,
            'search_facts': search_facts,
            'decide': decide,
            
            # Web tools
            'search_web': search_web,
            'fetch_webpage': fetch_webpage,
            'extract_links': extract_links,
            'summarize_webpage': summarize_webpage,
            
            # Qdrant backup tools
            'backup_qdrant': backup_qdrant,
            'restore_qdrant': restore_qdrant,
            'list_backups': list_backups,
            'get_backup_stats': get_backup_stats,
            
            # Git tools
            'git_status': git_status,
            'git_diff': git_diff,
            'git_commit': git_commit,
            'git_log': git_log,
            'git_branch_list': git_branch_list,
        }
    
    def execute(self, tool_name: str, **kwargs) -> Any:
        """
        Exécute un outil avec les paramètres donnés
        
        Args:
            tool_name: Nom de l'outil
            **kwargs: Paramètres de l'outil
            
        Returns:
            Résultat de l'outil
        """
        if tool_name not in self.tools:
            return {"error": f"Outil inconnu: {tool_name}"}
        
        try:
            result = self.tools[tool_name](**kwargs)
            return result
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}
    
    def list_available_tools(self) -> List[str]:
        """Liste les outils disponibles"""
        return list(self.tools.keys())


class DeepSeekAgent:
    """Agent de développement basé sur DeepSeek avec function calling"""
    
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("❌ DEEPSEEK_API_KEY non trouvée dans l'environnement")
        
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"
        self.conversation_history: List[Dict] = []
        self.initial_request = None  # Sauvegarde permanente de la demande initiale
        self.conversation_summary = None  # Résumé progressif de la conversation
        self.last_summary_iteration = 0  # Dernière itération où le résumé a été mis à jour
        self.max_history_messages = 15  # Augmenté: Max 15 messages pour meilleur contexte
        self.max_context_tokens = 80000  # Augmenté: 80K tokens max (marge 39%)
        self.max_retries = 3  # Nombre max de tentatives auto-correction
        self.system_prompt = self._load_system_prompt()
        self.tool_executor = ToolExecutor()
        self.memory = get_memory()  # Accès direct à la mémoire
        
        # NOUVEAU: Détection de boucles
        self.tool_call_history = []  # Historique des appels d'outils récents
        self.max_identical_calls = 3  # Max d'appels identiques consécutifs
        
        # Statistiques de tokens (estimation conservative)
        self.token_stats = {
            'total_input': 0,
            'total_output': 0,
            'memory_tokens': 0,
            'memory_queries': 0,
            'history_truncations': 0,
            'auto_corrections': 0,
            'api_errors': 0,
            # NOUVEAU: Métriques de contexte
            'compressions': 0,
            'duplicates_removed': 0,
            'importance_filtered': 0,
            'avg_context_tokens': [],  # Liste pour calculer moyenne
            'critical_messages': 0,
            'important_messages': 0,
            'context_messages': 0,
            'max_context_tokens_reached': 0,
            'loop_detections': 0  # Nombre de boucles détectées
        }
    
    def save_conversation(self) -> bool:
        """Sauvegarde la conversation courante dans la mémoire"""
        try:
            if len(self.conversation_history) < 2:
                return False  # Pas assez de messages à sauvegarder
            
            # Extraire les sujets et actions de la conversation
            topics = []
            outcomes = []
            
            for msg in self.conversation_history:
                if msg['role'] == 'user':
                    # Extraire les premiers mots comme sujets
                    content = msg['content'].replace('[CRITICAL]', '').replace('[IMPORTANT]', '').replace('[CONTEXT]', '').strip()
                    words = content.split()[:5]
                    topic = ' '.join(words)
                    if topic and topic not in topics:
                        topics.append(topic)
                elif 'succès' in msg['content'].lower() or 'créé' in msg['content'].lower():
                    # Extraire les actions réussies
                    lines = msg['content'].split('\n')
                    for line in lines[:3]:
                        if line.strip():
                            outcomes.append(line.strip()[:100])
            
            # Limiter la taille
            topics = topics[:5]
            outcomes = outcomes[:5]
            
            # Créer un résumé
            summary = f"Conversation du {datetime.now().strftime('%Y-%m-%d %H:%M')}: "
            if self.initial_request:
                summary += self.initial_request[:200]
            else:
                summary += "Session interactive"
            
            # Sauvegarder dans Qdrant
            self.memory.store_conversation_summary(
                summary=summary,
                topics=topics,
                outcomes=outcomes
            )
            return True
        except Exception as e:
            print(f"{Colors.DIM}⚠️  Erreur sauvegarde conversation: {e}{Colors.RESET}")
            return False
    
    def load_last_conversation(self) -> Optional[str]:
        """Charge le résumé de la dernière conversation"""
        try:
            # Rechercher toutes les conversations (sans order_by qui nécessite un index)
            results = self.memory.client.scroll(
                collection_name=self.memory.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="type", match=MatchValue(value="conversation"))]
                ),
                limit=100,  # Récupérer jusqu'à 100 conversations
                with_payload=True
            )
            
            if results and len(results[0]) > 0:
                # Trier côté client par timestamp (ISO format se trie alphabétiquement)
                conversations = results[0]
                if conversations:
                    # Trier par timestamp décroissant
                    sorted_convs = sorted(
                        conversations,
                        key=lambda x: x.payload.get('timestamp', ''),
                        reverse=True
                    )
                    last_conv = sorted_convs[0].payload
                    summary = f"📜 Dernière conversation:\n"
                    summary += f"  {last_conv.get('summary', 'N/A')}\n"
                    if last_conv.get('topics'):
                        summary += f"  Sujets: {', '.join(last_conv['topics'][:3])}\n"
                    if last_conv.get('outcomes'):
                        summary += f"  Actions: {', '.join(last_conv['outcomes'][:2])}"
                    return summary
        except Exception as e:
            print(f"{Colors.DIM}⚠️  Erreur chargement conversation: {e}{Colors.RESET}")
        return None
        
    def _load_system_prompt(self) -> str:
        """Charge les instructions système depuis SYSTEM.md"""
        system_file = Path(__file__).parent / "SYSTEM.md"
        
        if system_file.exists():
            content = system_file.read_text(encoding='utf-8')
            # Ajouter les instructions pour les outils
            tools_doc = self._generate_tools_documentation()
            return content + "\n\n" + tools_doc
        else:
            return "Vous êtes un assistant de développement intelligent."
    
    def _generate_tools_documentation(self) -> str:
        """Génère la documentation des outils disponibles (version compacte)"""
        tools_doc = """
## 🔧 OUTILS

Syntaxe: <tool>{"name": "outil", "parameters": {...}}</tool>

**Fichiers:**
- read_file(file_path: str, start_line: int = None, end_line: int = None) → lit fichier (entier ou lignes X-Y)
- write_file(file_path: str, content: str) → écrit fichier (max 50KB)
- append_file(file_path: str, content: str) → ajoute au fichier
- replace_in_file(file_path: str, old_text: str, new_text: str) → remplace texte dans fichier
  ⚠️ old_text doit être EXACTEMENT identique (espaces, sauts de ligne). Utilisez read_file() d'abord!
- list_files(directory: str, pattern: str = "*", max_results: int = 100) → liste fichiers
- file_exists(file_path: str) → vérifie existence

**Shell:**
- execute_command(command: str, shell: bool = False) → exécute commande
- check_command_exists(command: str) → vérifie si commande existe
- get_system_info() → infos système

**Mémoire:**
- remember(fact: str, category: str = "general") → mémorise un fait
- recall(category: str = None, limit: int = 10) → récupère faits par catégorie
- search_facts(query: str, limit: int = 5) → recherche sémantique dans les faits
- decide(decision: str, reasoning: str) → enregistre une décision

**Web:**
- search_web(query: str, max_results: int = 5) → recherche Tavily
- fetch_webpage(url: str) → contenu page web
- extract_links(url: str) → extrait liens
- summarize_webpage(url: str) → résumé page

**Backup Qdrant:**
- backup_qdrant(backup_dir: str = "./backups") → sauvegarde la mémoire Qdrant
- restore_qdrant(backup_file: str, clear_existing: bool = False) → restaure depuis backup
- list_backups(backup_dir: str = "./backups") → liste les backups disponibles
- get_backup_stats(backup_file: str) → statistiques d'un backup

**Git:**
- git_status(repository_path: str = ".") → statut du dépôt Git
- git_diff(file_path: str = "", repository_path: str = ".", staged: bool = False) → différences Git
- git_commit(message: str, repository_path: str = ".", add_all: bool = False) → créer un commit
- git_log(max_count: int = 10, repository_path: str = ".") → historique des commits
- git_branch_list(repository_path: str = ".") → liste des branches

Exemples:
<tool>{"name": "list_files", "parameters": {"directory": ".", "pattern": "*.py"}}</tool>
<tool>{"name": "read_file", "parameters": {"file_path": "main.py", "start_line": 1, "end_line": 500}}</tool>
<tool>{"name": "replace_in_file", "parameters": {"file_path": "test.py", "old_text": "ancien", "new_text": "nouveau"}}</tool>

Notes:
- JSON valide uniquement dans <tool>
- Pas de <thinking> dans <tool>
- list_files est TOUJOURS récursif, pas de paramètre recursive
- Pour longs fichiers: LISEZ JUSQU'À 1000 LIGNES à la fois (ex: 1-500, 501-1000)
- NE PAS lire par petites sections (10-50 lignes), c'est inefficace
- Pour modifications: utilisez replace_in_file() au lieu de réécrire avec write_file()
"""
        return tools_doc
    
    def add_message(self, role: str, content: str):
        """Ajoute un message à l'historique"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def _compress_context(self):
        """Compression du contexte: élimination des répétitions et regroupement d'informations similaires"""
        if len(self.conversation_history) < 4:
            return  # Pas assez de messages pour compresser
        
        compressed_history = []
        seen_contents = set()
        
        for msg in self.conversation_history:
            content = msg.get('content', '')
            # Hash du contenu pour détecter les doublons exacts
            content_hash = hash(content[:1000])  # Hash des 1000 premiers chars
            
            # Vérifier si c'est une répétition exacte
            if content_hash in seen_contents and msg['role'] != 'system':
                continue  # Ignorer les doublons
            
            seen_contents.add(content_hash)
            
            # Compresser les longues sorties d'outils similaires
            if len(content) > 5000 and '[TOOL RESULT]' in content:
                # Garder seulement un résumé si plusieurs résultats similaires
                content = content[:3000] + "\n... [COMPRESSÉ POUR ÉVITER RÉPÉTITION]"
                msg = msg.copy()
                msg['content'] = content
            
            compressed_history.append(msg)
        
        removed = len(self.conversation_history) - len(compressed_history)
        if removed > 0:
            self.conversation_history = compressed_history
            self.token_stats['compressions'] += 1
            self.token_stats['duplicates_removed'] += removed
            print(f"{Colors.DIM}🗜️  Compression: {removed} répétitions éliminées{Colors.RESET}")
    
    def _tag_message_importance(self, message: str, role: str) -> tuple:
        """Tag un message selon son importance: CRITICAL, IMPORTANT, CONTEXT"""
        # CRITIQUE: Ne pas re-tagger un message déjà taggé (éviter [CONTEXT] [CONTEXT] ...)
        if message.startswith('[CRITICAL]') or message.startswith('[IMPORTANT]') or message.startswith('[CONTEXT]'):
            # Message déjà taggé, retourner tel quel
            if message.startswith('[CRITICAL]'):
                return 'CRITICAL', message
            elif message.startswith('[IMPORTANT]'):
                return 'IMPORTANT', message
            else:
                return 'CONTEXT', message
        
        # Messages système = toujours CRITICAL
        if role == 'system':
            return 'CRITICAL', message
        
        # Patterns critiques
        critical_patterns = [
            'erreur', 'error', 'critique', 'critical', 'urgent',
            'échec', 'failed', 'impossible', 'bloquer', 'blocked'
        ]
        
        # Patterns importants
        important_patterns = [
            'implémente', 'implement', 'crée', 'create', 'modifie', 'modify',
            'corrige', 'fix', 'ajoute', 'add', 'améliore', 'improve',
            'objectif', 'goal', 'tâche', 'task'
        ]
        
        # Patterns contexte (RETIRÉS: context, info, detail pour éviter faux positifs avec les tags eux-mêmes)
        context_patterns = [
            'préfère', 'prefer', 'aime', 'like', 'historique', 'history'
        ]
        
        message_lower = message.lower()
        
        # Premier message utilisateur = toujours CRITICAL (demande initiale)
        if role == 'user' and self.initial_request and message == self.initial_request:
            return 'CRITICAL', f"[CRITICAL] {message}"
        
        # Vérifier les patterns
        for pattern in critical_patterns:
            if pattern in message_lower:
                return 'CRITICAL', f"[CRITICAL] {message}"
        
        for pattern in important_patterns:
            if pattern in message_lower:
                return 'IMPORTANT', f"[IMPORTANT] {message}"
        
        for pattern in context_patterns:
            if pattern in message_lower:
                return 'CONTEXT', f"[CONTEXT] {message}"
        
        # Par défaut: IMPORTANT pour les messages utilisateur, CONTEXT pour assistant
        if role == 'user':
            return 'IMPORTANT', f"[IMPORTANT] {message}"
        else:
            return 'CONTEXT', f"[CONTEXT] {message}"
    
    def _apply_importance_filtering(self):
        """Applique un filtrage basé sur l'importance des messages"""
        if len(self.conversation_history) < self.max_history_messages:
            return  # Pas besoin de filtrer
        
        # Séparer les messages par importance
        critical = []
        important = []
        context = []
        
        for msg in self.conversation_history:
            content = msg.get('content', '')
            if '[CRITICAL]' in content:
                critical.append(msg)
            elif '[IMPORTANT]' in content:
                important.append(msg)
            else:
                context.append(msg)
        
        # Reconstruire l'historique en priorisant
        # Garder tous les CRITICAL, puis IMPORTANT, puis CONTEXT si place
        filtered_history = critical + important
        
        # Ajouter CONTEXT seulement si on a de la place
        remaining_slots = self.max_history_messages - len(filtered_history)
        if remaining_slots > 0:
            filtered_history.extend(context[-remaining_slots:])
        
        if len(filtered_history) < len(self.conversation_history):
            removed = len(self.conversation_history) - len(filtered_history)
            self.conversation_history = filtered_history
            self.token_stats['importance_filtered'] += removed
            print(f"{Colors.DIM}🏷️  Filtrage: {removed} messages contexte supprimés (priorité CRITICAL/IMPORTANT){Colors.RESET}")
    
    def _extract_tool_calls(self, text: str) -> List[Dict]:
        """
        Extrait les appels d'outils depuis le texte
        
        Args:
            text: Texte contenant potentiellement des appels d'outils
            
        Returns:
            Liste des appels d'outils
        """
        # Trouver tous les blocs <tool>...</tool>
        pattern = r'<tool>(.*?)</tool>'
        matches = re.findall(pattern, text, re.DOTALL)
        
        tool_calls = []
        for match in matches:
            # Enlever les balises <thinking> et autres balises XML
            cleaned = re.sub(r'<[^>]+>.*?</[^>]+>', '', match, flags=re.DOTALL)
            cleaned = cleaned.strip()
            
            # Essayer de parser directement
            try:
                tool_call = json.loads(cleaned)
                # Vérifier que c'est bien un appel d'outil valide
                if 'name' in tool_call and 'parameters' in tool_call:
                    tool_calls.append(tool_call)
                    continue
            except json.JSONDecodeError:
                pass
            
            # Si échec, chercher un objet JSON valide dans le texte
            # Trouver la première accolade ouvrante
            start = cleaned.find('{')
            if start == -1:
                continue
                
            # Trouver l'accolade fermante correspondante
            brace_count = 0
            end = start
            for i in range(start, len(cleaned)):
                if cleaned[i] == '{':
                    brace_count += 1
                elif cleaned[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            
            if end > start:
                json_str = cleaned[start:end]
                try:
                    tool_call = json.loads(json_str)
                    if 'name' in tool_call and 'parameters' in tool_call:
                        tool_calls.append(tool_call)
                except json.JSONDecodeError as e:
                    print(f"{Colors.RED}⚠️  Erreur parsing tool call: {e}{Colors.RESET}")
                    print(f"{Colors.DIM}Contenu: {json_str[:100]}...{Colors.RESET}")
        
        return tool_calls
    
    def _execute_tool_calls(self, tool_calls: List[Dict]) -> List[Dict]:
        """
        Exécute une liste d'appels d'outils avec détection de boucles
        
        Args:
            tool_calls: Liste des appels d'outils
            
        Returns:
            Liste des résultats
        """
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get('name')
            parameters = tool_call.get('parameters', {})
            
            # NOUVEAU: Détection de boucle
            call_signature = f"{tool_name}:{json.dumps(parameters, sort_keys=True)}"
            
            # Vérifier si cet appel exact a été fait récemment
            recent_calls = self.tool_call_history[-10:]  # Les 10 derniers appels
            identical_count = recent_calls.count(call_signature)
            
            if identical_count >= self.max_identical_calls:
                self.token_stats['loop_detections'] += 1
                error_msg = (
                    f"⚠️ BOUCLE DÉTECTÉE: L'outil '{tool_name}' avec les mêmes paramètres "
                    f"a été appelé {identical_count + 1} fois consécutivement sans succès. "
                    f"Arrêt pour éviter une boucle infinie."
                )
                print(f"\n{Colors.RED}{error_msg}{Colors.RESET}")
                
                # Retourner une erreur explicite
                results.append({
                    "tool": tool_name,
                    "parameters": parameters,
                    "result": {"error": error_msg, "loop_detected": True}
                })
                
                # Ajouter un message d'aide à l'historique
                help_msg = (
                    f"\n\n⚠️ **BOUCLE DÉTECTÉE**: Vous répétez '{tool_name}' sans succès. "
                    f"Essayez une approche différente ou demandez de l'aide à l'utilisateur."
                )
                self.add_message("user", help_msg)
                continue
            
            # Enregistrer cet appel
            self.tool_call_history.append(call_signature)
            
            # Limiter l'historique des appels pour ne pas exploser la mémoire
            if len(self.tool_call_history) > 50:
                self.tool_call_history = self.tool_call_history[-50:]
            
            print(f"\n{Colors.YELLOW}🔧 Exécution: {tool_name}({json.dumps(parameters, ensure_ascii=False)}){Colors.RESET}")
            
            result = self.tool_executor.execute(tool_name, **parameters)
            results.append({
                "tool": tool_name,
                "parameters": parameters,
                "result": result
            })
            
            # Afficher le résultat
            self._display_tool_result(tool_name, result)
        
        return results
    
    def _display_tool_result(self, tool_name: str, result: Any):
        """Affiche le résultat d'un outil de manière formatée"""
        if isinstance(result, dict) and 'error' in result:
            print(f"{Colors.RED}❌ Erreur: {result['error']}{Colors.RESET}")
        elif tool_name == 'execute_command' and isinstance(result, dict):
            if result.get('success'):
                print(f"{Colors.GREEN}✓ Succès{Colors.RESET}")
                if result.get('stdout'):
                    stdout = result['stdout'][:500]  # Limiter l'affichage
                    print(f"{Colors.DIM}{stdout}{Colors.RESET}")
                    if len(result['stdout']) > 500:
                        print(f"{Colors.DIM}... (tronqué){Colors.RESET}")
            else:
                print(f"{Colors.RED}✗ Échec (code: {result.get('returncode')}){Colors.RESET}")
                if result.get('stderr'):
                    print(f"{Colors.RED}{result['stderr'][:200]}{Colors.RESET}")
        elif isinstance(result, (list, dict)):
            result_str = json.dumps(result, indent=2, ensure_ascii=False)[:500]
            print(f"{Colors.GREEN}✓ {result_str}{Colors.RESET}")
        else:
            print(f"{Colors.GREEN}✓ {str(result)[:500]}{Colors.RESET}")
    
    def _estimate_tokens(self, text: str) -> int:
        """Estime le nombre de tokens (approximation: 1 token ≈ 4 chars)"""
        return len(text) // 4
    
    def _update_conversation_summary(self) -> str:
        """Génère un résumé compact de la conversation en cours"""
        try:
            # Construire un contexte compact des derniers messages
            recent_context = ""
            for msg in self.conversation_history[-8:]:  # 8 derniers messages
                role = msg['role']
                content = msg['content'][:500]  # Limiter à 500 chars
                recent_context += f"{role}: {content}\n\n"
            
            # Demander un résumé ultra-compact
            summary_prompt = f"""Résume cette conversation en MAX 3 lignes courtes:
- Demande initiale: {self.initial_request or 'Non définie'}
- Actions récentes:
{recent_context}

Résumé (3 lignes max, format: 'Objectif: ... | Fait: ... | Reste: ...'):"""
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": summary_prompt}],
                "temperature": 0.3,
                "max_tokens": 200
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                summary = result['choices'][0]['message']['content'].strip()
                self.conversation_summary = summary
                return summary
            else:
                return None
        except Exception:
            return None
    
    def _truncate_tool_result(self, result: any, max_chars: int = 10000, tool_name: str = "") -> str:
        """Tronque les résultats d'outils pour éviter overflow (CRITIQUE)"""
        if isinstance(result, dict) and 'error' in result:
            # Garder les erreurs complètes (courtes)
            return json.dumps(result, ensure_ascii=False)
        
        # Convertir en string et tronquer agressivement
        result_str = json.dumps(result, ensure_ascii=False, indent=2)
        
        # Limite très grande pour read_file (agent lit ~1000 lignes à la fois)
        effective_max = 100000 if tool_name == "read_file" else max_chars
        
        if len(result_str) <= effective_max:
            return result_str
        
        # Tronquer avec message explicite
        truncated = result_str[:effective_max]
        return truncated + f"\n... [TRONQUÉ - {len(result_str)} chars total, montré {effective_max}]"
    
    def _truncate_history(self):
        """Tronque l'historique si trop long (garde TOUJOURS le 1er message utilisateur + messages récents)"""
        # NOUVEAU: Étape 1 - Compression du contexte (éliminer répétitions)
        self._compress_context()
        
        # NOUVEAU: Étape 2 - Filtrage par importance si nécessaire
        self._apply_importance_filtering()
        
        # Identifier le premier message utilisateur (instruction initiale CRITIQUE)
        first_user_msg = None
        first_user_idx = None
        for idx, msg in enumerate(self.conversation_history):
            if msg['role'] == 'user':
                first_user_msg = msg
                first_user_idx = idx
                break
        
        # 1. Limite par nombre de messages
        if len(self.conversation_history) > self.max_history_messages:
            # CRITIQUE: Garder le 1er message user + les N-1 derniers messages
            if first_user_msg:
                # Retirer temporairement le premier message
                remaining_history = self.conversation_history[first_user_idx+1:]
                # Garder les N-1 derniers
                kept_recent = remaining_history[-(self.max_history_messages-1):]
                # Reconstruire: [premier_user] + [messages récents]
                removed = len(self.conversation_history) - len(kept_recent) - 1
                self.conversation_history = [first_user_msg] + kept_recent
            else:
                # Fallback: garder les N derniers si pas de message user trouvé
                removed = len(self.conversation_history) - self.max_history_messages
                self.conversation_history = self.conversation_history[-self.max_history_messages:]
            
            self.token_stats['history_truncations'] += 1
            print(f"{Colors.DIM}✂️  Historique tronqué ({removed} messages supprimés, instruction initiale préservée){Colors.RESET}")
        
        # 2. Limite par tokens totaux
        total_tokens = sum(self._estimate_tokens(m['content']) for m in self.conversation_history)
        
        while total_tokens > self.max_context_tokens and len(self.conversation_history) > 6:
            # Supprimer les messages intermédiaires (PAS le premier user, PAS les 5 derniers)
            if len(self.conversation_history) <= 6:
                break  # Garder minimum: [first_user] + [5 derniers]
            
            # Trouver l'index du premier message user
            first_idx = 0
            for idx, msg in enumerate(self.conversation_history):
                if msg['role'] == 'user':
                    first_idx = idx
                    break
            
            # Supprimer le message juste après le premier (position first_idx+1)
            if first_idx + 1 < len(self.conversation_history) - 5:
                removed_msg = self.conversation_history.pop(first_idx + 1)
                total_tokens -= self._estimate_tokens(removed_msg['content'])
                self.token_stats['history_truncations'] += 1
                print(f"{Colors.DIM}✂️  Message intermédiaire supprimé (tokens: {self._estimate_tokens(removed_msg['content'])}){Colors.RESET}")
            else:
                # Si on ne peut plus supprimer sans toucher aux 5 derniers, arrêter
                break
    
    def _handle_api_error(self, error_code: int, error_message: str, retry_count: int) -> dict:
        """Gère les erreurs API avec stratégies d'auto-correction"""
        self.token_stats['api_errors'] += 1
        
        print(f"\n{Colors.YELLOW}⚠️  Erreur API détectée (tentative {retry_count}/{self.max_retries}){Colors.RESET}")
        
        # Stratégie 1: Context overflow (erreur 400 avec "context length")
        if error_code == 400 and "context length" in error_message.lower():
            print(f"{Colors.CYAN}🔧 Auto-correction: Réduction drastique de l'historique{Colors.RESET}")
            
            # Garder seulement les 5 derniers messages
            if len(self.conversation_history) > 5:
                kept = self.conversation_history[-5:]
                removed = len(self.conversation_history) - 5
                self.conversation_history = kept
                self.token_stats['auto_corrections'] += 1
                print(f"{Colors.GREEN}✓ {removed} messages supprimés, retry automatique{Colors.RESET}")
                return {'retry': True, 'strategy': 'context_reduction'}
            else:
                # Historique déjà minimal, réduire le system prompt
                print(f"{Colors.RED}⚠️  Historique minimal, impossible de réduire davantage{Colors.RESET}")
                return {'retry': False, 'strategy': 'none'}
        
        # Stratégie 2: Rate limit (erreur 429)
        elif error_code == 429:
            import time
            wait_time = min(2 ** retry_count, 10)  # Backoff exponentiel (max 10s)
            print(f"{Colors.CYAN}🔧 Auto-correction: Attente {wait_time}s (rate limit){Colors.RESET}")
            time.sleep(wait_time)
            self.token_stats['auto_corrections'] += 1
            return {'retry': True, 'strategy': 'backoff'}
        
        # Stratégie 3: Invalid request (erreur 400 autre)
        elif error_code == 400:
            print(f"{Colors.RED}⚠️  Requête invalide, vérification des paramètres{Colors.RESET}")
            # Nettoyer les messages potentiellement problématiques
            for msg in self.conversation_history:
                if len(msg.get('content', '')) > 50000:  # Messages trop longs
                    msg['content'] = msg['content'][:50000] + "... [tronqué]"
                    self.token_stats['auto_corrections'] += 1
                    print(f"{Colors.GREEN}✓ Message long tronqué{Colors.RESET}")
                    return {'retry': True, 'strategy': 'message_truncation'}
            return {'retry': False, 'strategy': 'none'}
        
        # Stratégie 4: Erreur serveur (5xx)
        elif error_code >= 500:
            import time
            wait_time = 2
            print(f"{Colors.CYAN}🔧 Auto-correction: Erreur serveur, attente {wait_time}s{Colors.RESET}")
            time.sleep(wait_time)
            self.token_stats['auto_corrections'] += 1
            return {'retry': True, 'strategy': 'server_error_wait'}
        
        return {'retry': False, 'strategy': 'unknown'}
        # 2. Limite par tokens totaux
        total_tokens = sum(self._estimate_tokens(m['content']) for m in self.conversation_history)
        
        while total_tokens > self.max_context_tokens and len(self.conversation_history) > 2:
            # Supprimer les plus anciens messages (garder au moins 2 pour le contexte)
            removed_msg = self.conversation_history.pop(0)
            total_tokens -= self._estimate_tokens(removed_msg['content'])
            self.token_stats['history_truncations'] += 1
            print(f"{Colors.DIM}✂️  Message ancien supprimé (tokens: {self._estimate_tokens(removed_msg['content'])}){Colors.RESET}")
    
    def _get_relevant_memory(self, user_message: str, max_facts: int = 3, min_score: float = 0.4) -> str:
        """
        Récupère les faits pertinents de la mémoire (avec limite stricte)
        
        Args:
            user_message: Message de l'utilisateur
            max_facts: Nombre max de faits (limite tokens)
            min_score: Score minimum de pertinence
            
        Returns:
            Contexte mémoire formaté (compact)
        """
        try:
            # Recherche sémantique
            relevant_facts = self.memory.search_facts(user_message, limit=max_facts)
            
            # Filtrer par score
            relevant_facts = [f for f in relevant_facts if f.get('score', 0) >= min_score]
            
            if not relevant_facts:
                return ""
            
            # Formater de manière COMPACTE pour économiser tokens
            context = "\n[Mémoire: "
            facts_text = []
            for fact in relevant_facts:
                # Format ultra-compact: juste le fait
                facts_text.append(fact['fact'])
            
            context += "; ".join(facts_text) + "]"
            
            # Estimer et tracker les tokens utilisés
            tokens_used = self._estimate_tokens(context)
            self.token_stats['memory_tokens'] += tokens_used
            
            return context
        except Exception as e:
            # Ne pas crasher si la mémoire échoue
            print(f"{Colors.DIM}⚠️  Mémoire indisponible: {e}{Colors.RESET}")
            return ""
    
    def chat(self, user_message: str, stream: bool = True) -> str:
        """Envoie un message à DeepSeek et récupère la réponse avec exécution des outils"""
        
        # RAPPEL AUTOMATIQUE de la mémoire (avec limite stricte)
        memory_context = self._get_relevant_memory(user_message, max_facts=3, min_score=0.4)
        
        # Ajouter contexte mémoire au message si pertinent
        if memory_context:
            enhanced_message = memory_context + "\n\n" + user_message
        else:
            enhanced_message = user_message
        
        # NOUVEAU: Tagger le message selon son importance
        importance, tagged_message = self._tag_message_importance(enhanced_message, 'user')
        
        # Ajouter le message utilisateur avec tag d'importance
        self.add_message("user", tagged_message)
        
        # CRITIQUE: Sauvegarder la demande initiale si c'est le premier message
        if self.initial_request is None and not enhanced_message.startswith("## Résultats des outils:"):
            self.initial_request = user_message  # Version originale sans contexte mémoire
        
        max_iterations = 25  # Éviter les boucles infinies (augmenté pour les tâches complexes)
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Tronquer l'historique si nécessaire (AVANT chaque requête)
            self._truncate_history()
            
            # Mettre à jour le résumé toutes les 5 itérations
            if iteration > 0 and iteration % 5 == 0 and iteration != self.last_summary_iteration:
                print(f"{Colors.DIM}📝 Mise à jour du résumé de conversation...{Colors.RESET}")
                self._update_conversation_summary()
                self.last_summary_iteration = iteration
            
            # Préparer les messages avec le système
            system_content = self.system_prompt
            
            # Ajouter le résumé de conversation au prompt système si disponible
            if self.conversation_summary and iteration > 5:
                system_content += f"\n\n## 📋 CONTEXTE CONVERSATION:\n{self.conversation_summary}"
            
            messages = [
                {"role": "system", "content": system_content}
            ] + self.conversation_history
            
            # CRITIQUE: Ajouter rappel de la demande initiale si on a fait plus de 15 itérations
            if iteration > 15 and self.initial_request and len(messages) > 1:
                reminder = f"\n\n⚠️ RAPPEL DEMANDE INITIALE: {self.initial_request}"
                messages[1]['content'] += reminder  # Ajouter au premier message user
            
            # Préparer la requête
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": messages,
                "stream": stream,
                "temperature": 0.7
            }
            
            # Estimer tokens envoyés
            total_content = "".join([m['content'] for m in messages])
            self.token_stats['total_input'] += self._estimate_tokens(total_content)
            
            if stream:
                full_response = self._stream_response(headers, data)
            else:
                full_response = self._get_response(headers, data)
            
            # Estimer tokens output
            self.token_stats['total_output'] += self._estimate_tokens(full_response)
            
            # Extraire et exécuter les appels d'outils
            tool_calls = self._extract_tool_calls(full_response)
            
            if not tool_calls:
                # Pas d'appel d'outil, c'est la réponse finale
                return full_response
            
            # Exécuter les outils
            tool_results = self._execute_tool_calls(tool_calls)
            
            # CRITIQUE: Tronquer les résultats AVANT d'ajouter à l'historique
            results_text = "\n\n## Résultats des outils:\n\n"
            for result in tool_results:
                # Limiter chaque résultat (10K par défaut, 20K pour read_file)
                truncated_result = self._truncate_tool_result(result['result'], max_chars=10000, tool_name=result['tool'])
                results_text += f"**{result['tool']}**: {truncated_result}\n\n"
            
            # Tronquer l'historique AVANT d'ajouter les nouveaux résultats
            self._truncate_history()
            
            self.add_message("user", results_text)
            
            print(f"\n{Colors.MAGENTA}🔄 L'agent analyse les résultats...{Colors.RESET}\n")
        
        print(f"{Colors.YELLOW}⚠️  Nombre maximum d'itérations atteint{Colors.RESET}")
        print(f"{Colors.YELLOW}💡 Dernière réponse de l'agent:{Colors.RESET}")
        return full_response
    
    def _stream_response(self, headers: Dict, data: Dict, retry_count: int = 0) -> str:
        """Récupère une réponse en streaming avec auto-correction"""
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                stream=True,
                timeout=60
            )
            
            if response.status_code != 200:
                error_msg = f"Erreur API {response.status_code}: {response.text}"
                
                # Tentative d'auto-correction
                if retry_count < self.max_retries:
                    correction = self._handle_api_error(response.status_code, response.text, retry_count + 1)
                    if correction['retry']:
                        print(f"{Colors.GREEN}♻️  Nouvelle tentative...{Colors.RESET}")
                        return self._stream_response(headers, data, retry_count + 1)
                
                # Échec définitif
                print(f"{Colors.RED}{error_msg}{Colors.RESET}")
                return f"[ERREUR API - {response.status_code}]"
            
            # Streaming normal
            full_response = ""
            print(f"{Colors.CYAN}🤖 Agent:{Colors.RESET} ", end="", flush=True)
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]  # Enlever 'data: '
                        
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    print(content, end="", flush=True)
                                    full_response += content
                        except json.JSONDecodeError:
                            continue
            
            print()  # Nouvelle ligne à la fin
            
            # NOUVEAU: Tagger la réponse selon son importance
            importance, tagged_response = self._tag_message_importance(full_response, 'assistant')
            
            # Ajouter la réponse à l'historique avec tag
            self.add_message("assistant", tagged_response)
            return full_response
            
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur inattendue: {e}{Colors.RESET}")
            return f"[ERREUR - {str(e)}]"
    
    def _get_response(self, headers: dict, data: dict, retry_count: int = 0) -> str:
        """Récupère une réponse complète (non streaming) avec auto-correction"""
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                error_msg = f"Erreur API {response.status_code}: {response.text}"
                
                # Tentative d'auto-correction
                if retry_count < self.max_retries:
                    correction = self._handle_api_error(response.status_code, response.text, retry_count + 1)
                    if correction['retry']:
                        print(f"{Colors.GREEN}♻️  Nouvelle tentative...{Colors.RESET}")
                        return self._get_response(headers, data, retry_count + 1)
                
                # Échec définitif
                print(f"{Colors.RED}{error_msg}{Colors.RESET}")
                return f"[ERREUR API - {response.status_code}]"
            
            result = response.json()
            assistant_message = result['choices'][0]['message']['content']
            
            # NOUVEAU: Tagger la réponse selon son importance
            importance, tagged_message = self._tag_message_importance(assistant_message, 'assistant')
            
            # Ajouter à l'historique avec tag
            self.add_message("assistant", tagged_message)
            
            return assistant_message
            
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur inattendue: {e}{Colors.RESET}")
            return f"[ERREUR - {str(e)}]"
    
    def clear_history(self):
        """Efface l'historique de la conversation"""
        self.conversation_history = []
        print(f"{Colors.YELLOW}🔄 Historique effacé{Colors.RESET}")
    
    def save_conversation(self) -> bool:
        """Sauvegarde la conversation courante dans la mémoire"""
        try:
            if len(self.conversation_history) < 2:
                return False  # Pas assez de messages à sauvegarder
            
            # Extraire les sujets et actions de la conversation
            topics = []
            outcomes = []
            
            for msg in self.conversation_history:
                if msg['role'] == 'user':
                    # Extraire les premiers mots comme sujets
                    words = msg['content'].split()[:5]
                    topic = ' '.join(words)
                    if topic and topic not in topics:
                        topics.append(topic)
                elif 'succès' in msg['content'].lower() or 'créé' in msg['content'].lower():
                    # Extraire les actions réussies
                    lines = msg['content'].split('\n')
                    for line in lines[:3]:
                        if line.strip():
                            outcomes.append(line.strip()[:100])
            
            # Limiter la taille
            topics = topics[:5]
            outcomes = outcomes[:5]
            
            # Créer un résumé
            summary = f"Conversation du {datetime.now().strftime('%Y-%m-%d %H:%M')}: "
            if self.initial_request:
                summary += self.initial_request[:200]
            else:
                summary += "Session interactive"
            
            # Sauvegarder dans Qdrant
            self.memory.store_conversation_summary(
                summary=summary,
                topics=topics,
                outcomes=outcomes
            )
            return True
        except Exception as e:
            print(f"{Colors.DIM}⚠️  Erreur sauvegarde conversation: {e}{Colors.RESET}")
            return False
    
    def load_last_conversation(self) -> Optional[str]:
        """Charge le résumé de la dernière conversation"""
        try:
            # Rechercher les conversations récentes
            results = self.memory.client.scroll(
                collection_name=self.memory.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="type", match=MatchValue(value="conversation"))]
                ),
                limit=1,
                with_payload=True,
                order_by="timestamp"
            )
            
            if results and len(results[0]) > 0:
                last_conv = results[0][0].payload
                summary = f"📜 Dernière conversation:\n"
                summary += f"  {last_conv.get('summary', 'N/A')}\n"
                if last_conv.get('topics'):
                    summary += f"  Sujets: {', '.join(last_conv['topics'][:3])}\n"
                if last_conv.get('outcomes'):
                    summary += f"  Actions: {', '.join(last_conv['outcomes'][:2])}"
                return summary
        except Exception as e:
            print(f"{Colors.DIM}⚠️  Erreur chargement conversation: {e}{Colors.RESET}")
        return None
    
    def show_stats(self):
        """Affiche les statistiques de la session"""
        user_msgs = sum(1 for msg in self.conversation_history if msg['role'] == 'user')
        assistant_msgs = sum(1 for msg in self.conversation_history if msg['role'] == 'assistant')
        
        # Compter les messages par importance
        critical_count = sum(1 for msg in self.conversation_history if '[CRITICAL]' in msg.get('content', ''))
        important_count = sum(1 for msg in self.conversation_history if '[IMPORTANT]' in msg.get('content', ''))
        context_count = len(self.conversation_history) - critical_count - important_count
        
        print(f"\n{Colors.CYAN}📊 Statistiques de session:{Colors.RESET}")
        print(f"  Messages utilisateur: {user_msgs}")
        print(f"  Messages assistant: {assistant_msgs}")
        print(f"  Total: {len(self.conversation_history)}")
        print(f"  Truncations: {self.token_stats.get('history_truncations', 0)} fois")
        
        # Tokens historique
        history_tokens = sum(self._estimate_tokens(m['content']) for m in self.conversation_history)
        print(f"  Tokens historique: ~{history_tokens}")
        avg_tokens = history_tokens // max(len(self.conversation_history), 1)
        print(f"  Tokens moyens/msg: ~{avg_tokens}")
        
        # NOUVEAU: Métriques de contexte
        print(f"\n{Colors.CYAN}🗜️  Optimisation du contexte:{Colors.RESET}")
        print(f"  Compressions: {self.token_stats.get('compressions', 0)} fois")
        print(f"  Doublons éliminés: {self.token_stats.get('duplicates_removed', 0)} messages")
        print(f"  Filtrages par importance: {self.token_stats.get('importance_filtered', 0)} messages")
        
        # Économie estimée
        if self.token_stats.get('duplicates_removed', 0) > 0:
            saved_tokens = self.token_stats.get('duplicates_removed', 0) * avg_tokens
            total_would_be = history_tokens + saved_tokens
            reduction_pct = (saved_tokens / total_would_be * 100) if total_would_be > 0 else 0
            print(f"  Tokens économisés: ~{saved_tokens} (-{reduction_pct:.1f}%)")
        
        # Répartition par importance
        print(f"\n{Colors.CYAN}🏷️  Répartition par importance:{Colors.RESET}")
        total = len(self.conversation_history)
        if total > 0:
            print(f"  [CRITICAL]:  {critical_count:2d} ({critical_count/total*100:5.1f}%)")
            print(f"  [IMPORTANT]: {important_count:2d} ({important_count/total*100:5.1f}%)")
            print(f"  [CONTEXT]:   {context_count:2d} ({context_count/total*100:5.1f}%)")
        
        # Fiabilité
        print(f"\n{Colors.YELLOW}🛡️  Fiabilité:{Colors.RESET}")
        print(f"  Erreurs API: {self.token_stats.get('api_errors', 0)}")
        print(f"  Auto-corrections: {self.token_stats.get('auto_corrections', 0)}")
        print(f"  Boucles détectées: {self.token_stats.get('loop_detections', 0)}")
        if self.token_stats.get('api_errors', 0) > 0:
            success_rate = (1 - self.token_stats.get('api_errors', 0) / max(user_msgs, 1)) * 100
            print(f"  Taux de succès: {success_rate:.1f}%")
        
        # Stats tokens (estimation)
        # Tarif DeepSeek v3: $0.14/1M input tokens, $0.28/1M output tokens
        input_cost = self.token_stats['total_input'] * 0.14 / 1_000_000
        output_cost = self.token_stats['total_output'] * 0.28 / 1_000_000
        memory_cost = self.token_stats['memory_tokens'] * 0.14 / 1_000_000
        total_cost = input_cost + output_cost + memory_cost
        
        print(f"\n{Colors.YELLOW}💰 Consommation tokens (estimation):{Colors.RESET}")
        print(f"  Tokens input:  ~{self.token_stats['total_input']:,} (${input_cost:.6f})")
        print(f"  Tokens output: ~{self.token_stats['total_output']:,} (${output_cost:.6f})")
        print(f"  Tokens mémoire: ~{self.token_stats['memory_tokens']:,} ({self.token_stats['memory_queries']} requêtes, ${memory_cost:.6f})")
        print(f"  {Colors.BOLD}Coût total estimé: ${total_cost:.6f}{Colors.RESET}")
        print(f"{Colors.DIM}  (Tarif: $0.14/1M input, $0.28/1M output - Limite mémoire: 3 faits × 50 tokens max){Colors.RESET}")
        
        # Stats mémoire
        memory = get_memory()
        mem_stats = memory.get_statistics()
        print(f"\n{Colors.CYAN}🧠 Mémoire Qdrant:{Colors.RESET}")
        print(f"  Faits: {mem_stats['total_facts']}")
        print(f"  Décisions: {mem_stats['total_decisions']}")
        print(f"  Conversations: {mem_stats['total_conversations']}")
        print(f"  Total points: {mem_stats['total_points']}")

    
    def show_tools(self):
        """Affiche les outils disponibles"""
        print(f"\n{Colors.CYAN}🔧 Outils disponibles:{Colors.RESET}")
        for tool in self.tool_executor.list_available_tools():
            print(f"  • {tool}")


def print_banner():
    """Affiche la bannière de démarrage"""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════╗
║     DeepSeek Dev Agent - Chat avec Function Calling     ║
╚══════════════════════════════════════════════════════════╝{Colors.RESET}

{Colors.DIM}Commandes disponibles:
  /clear  - Effacer l'historique
  /stats  - Afficher les statistiques + tokens
  /tools  - Lister les outils
  /backup - Sauvegarder la mémoire Qdrant
  /backups - Lister les backups
  /restore <file> - Restaurer depuis backup
  /help   - Afficher l'aide
  /quit   - Quitter (ou Ctrl+D)

💡 Mémoire automatique activée (max 3 faits, <50 tokens/requête)
{Colors.RESET}
"""
    print(banner)


def print_help():
    """Affiche l'aide"""
    help_text = f"""
{Colors.CYAN}📖 Aide - Commandes disponibles:{Colors.RESET}

{Colors.BOLD}/clear{Colors.RESET}  - Efface l'historique de la conversation
{Colors.BOLD}/stats{Colors.RESET}  - Affiche les statistiques de la session
{Colors.BOLD}/tools{Colors.RESET}  - Liste les outils disponibles
{Colors.BOLD}/backup{Colors.RESET} - Sauvegarde la mémoire Qdrant
{Colors.BOLD}/backups{Colors.RESET} - Liste les backups disponibles
{Colors.BOLD}/restore <file>{Colors.RESET} - Restaure depuis un backup
{Colors.BOLD}/last{Colors.RESET}   - Affiche la dernière conversation
{Colors.BOLD}/help{Colors.RESET}   - Affiche cette aide
{Colors.BOLD}/quit{Colors.RESET}   - Quitte le chat (ou Ctrl+D)

{Colors.CYAN}⌨️  Édition de texte:{Colors.RESET}
  ← →    - Déplacer le curseur
  ↑ ↓    - Naviguer dans l'historique
  Ctrl+A - Début de ligne
  Ctrl+E - Fin de ligne
  Ctrl+U - Effacer la ligne
  Ctrl+K - Effacer jusqu'à la fin

{Colors.DIM}L'agent peut utiliser ses outils automatiquement pour répondre à vos demandes.
Il a accès aux fichiers, au shell, et à une mémoire persistante.
L'historique des commandes est sauvegardé dans ~/.deepseek_agent_history{Colors.RESET}
"""
    print(help_text)


def main():
    """Point d'entrée principal"""
    
    try:
        agent = DeepSeekAgent()
    except ValueError as e:
        print(f"{Colors.RED}{e}{Colors.RESET}")
        print(f"{Colors.YELLOW}💡 Définissez votre clé API: export DEEPSEEK_API_KEY='votre-clé'{Colors.RESET}")
        sys.exit(1)
    
    print_banner()
    print(f"{Colors.GREEN}✓ Agent initialisé avec succès{Colors.RESET}")
    print(f"{Colors.DIM}Instructions système chargées depuis SYSTEM.md{Colors.RESET}")
    print(f"{Colors.DIM}Outils disponibles: {len(agent.tool_executor.list_available_tools())}{Colors.RESET}\n")
    
    # Charger et afficher la dernière conversation
    last_conv = agent.load_last_conversation()
    if last_conv:
        print(last_conv)
        print()
    
    # Boucle principale
    while True:
        try:
            # Prompt utilisateur avec délimiteurs readline pour les couleurs
            if readline:
                # Utiliser les délimiteurs \001 et \002 pour que readline ignore les codes couleur
                prompt = f"\001{Colors.GREEN}\002👤 Vous:\001{Colors.RESET}\002 "
            else:
                prompt = f"{Colors.GREEN}👤 Vous:{Colors.RESET} "
            
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
            
            # Commandes spéciales
            if user_input.startswith('/'):
                command = user_input.lower()
                
                if command == '/quit' or command == '/q':
                    # Sauvegarder la conversation dans la mémoire
                    print(f"{Colors.CYAN}💾 Sauvegarde de la conversation...{Colors.RESET}")
                    if agent.save_conversation():
                        print(f"{Colors.GREEN}✅ Conversation sauvegardée{Colors.RESET}")
                    print(f"{Colors.YELLOW}👋 Au revoir !{Colors.RESET}")
                    # Sauvegarder l'historique avant de quitter
                    if readline and HISTORY_FILE:
                        try:
                            readline.write_history_file(HISTORY_FILE)
                        except Exception:
                            pass
                    break
                elif command == '/clear':
                    agent.clear_history()
                elif command == '/stats':
                    agent.show_stats()
                elif command == '/tools':
                    agent.show_tools()
                elif command == '/backup':
                    print(f"{Colors.CYAN}💾 Backup de la mémoire Qdrant...{Colors.RESET}")
                    result = backup_qdrant()
                    if result.get('success'):
                        print(f"{Colors.GREEN}✅ Backup réussi !{Colors.RESET}")
                        print(f"  Fichier: {result['backup_file']}")
                        print(f"  Points: {result['total_points']}")
                        print(f"  Taille: {result['file_size'] / 1024:.1f} KB")
                        if result.get('statistics'):
                            print(f"  Types: {result['statistics']}")
                    else:
                        print(f"{Colors.RED}❌ Erreur: {result.get('error')}{Colors.RESET}")
                elif command.startswith('/restore '):
                    backup_file = user_input[9:].strip()
                    if not backup_file:
                        print(f"{Colors.RED}❌ Usage: /restore <fichier_backup>{Colors.RESET}")
                    else:
                        print(f"{Colors.CYAN}♻️  Restauration depuis {backup_file}...{Colors.RESET}")
                        result = restore_qdrant(backup_file)
                        if result.get('success'):
                            print(f"{Colors.GREEN}✅ Restauration réussie !{Colors.RESET}")
                            print(f"  Collection: {result['collection']}")
                            print(f"  Points restaurés: {result['points_restored']}")
                        else:
                            print(f"{Colors.RED}❌ Erreur: {result.get('error')}{Colors.RESET}")
                elif command == '/backups':
                    backups = list_backups()
                    if not backups:
                        print(f"{Colors.YELLOW}ℹ️  Aucun backup trouvé{Colors.RESET}")
                    else:
                        print(f"{Colors.CYAN}📦 Backups disponibles:{Colors.RESET}")
                        for backup in backups:
                            print(f"\n  📄 {backup['filename']}")
                            print(f"     Taille: {backup['size'] / 1024:.1f} KB")
                            print(f"     Points: {backup['total_points']}")
                            print(f"     Date: {backup['created'][:19]}")
                elif command == '/last':
                    last_conv = agent.load_last_conversation()
                    if last_conv:
                        print(last_conv)
                    else:
                        print(f"{Colors.YELLOW}ℹ️  Aucune conversation précédente trouvée{Colors.RESET}")
                elif command == '/help' or command == '/?':
                    print_help()
                else:
                    print(f"{Colors.RED}❌ Commande inconnue: {user_input}{Colors.RESET}")
                    print(f"{Colors.DIM}Tapez /help pour voir les commandes disponibles{Colors.RESET}")
                
                continue
            
            # Envoyer le message à l'agent
            agent.chat(user_input, stream=True)
            print()  # Ligne vide pour la lisibilité
            
        except KeyboardInterrupt:
            # Sauvegarder la conversation dans la mémoire
            print(f"\n{Colors.CYAN}💾 Sauvegarde de la conversation...{Colors.RESET}")
            if agent.save_conversation():
                print(f"{Colors.GREEN}✅ Conversation sauvegardée{Colors.RESET}")
            print(f"{Colors.YELLOW}👋 Au revoir !{Colors.RESET}")
            # Sauvegarder l'historique avant de quitter
            if readline and HISTORY_FILE:
                try:
                    readline.write_history_file(HISTORY_FILE)
                except Exception:
                    pass
            break
        except EOFError:
            print(f"\n{Colors.YELLOW}👋 Au revoir !{Colors.RESET}")
            # Sauvegarder l'historique avant de quitter
            if readline and HISTORY_FILE:
                try:
                    readline.write_history_file(HISTORY_FILE)
                except Exception:
                    pass
            break
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur: {e}{Colors.RESET}")
            traceback.print_exc()


if __name__ == "__main__":
    main()
