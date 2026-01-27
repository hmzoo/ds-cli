"""
Outils pour l'agent DeepSeek Dev
"""

from .file_tools import (
    read_file,
    write_file,
    list_files,
    file_exists,
    append_file,
    replace_in_file
)

from .shell_tools import (
    execute_command,
    check_command_exists,
    get_system_info,
    is_safe_command
)

from .memory_tools import (
    get_memory,
    remember,
    recall,
    search_facts,
    decide
)

from .web_tools import (
    search_web,
    fetch_webpage,
    extract_links,
    summarize_webpage
)

from .qdrant_backup import (
    backup_qdrant,
    restore_qdrant,
    list_backups,
    get_backup_stats
)

from .git_tools import (
    git_status,
    git_diff,
    git_commit,
    git_log,
    git_branch_list
)
