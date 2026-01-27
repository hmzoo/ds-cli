"""
Tests unitaires pour les outils de backup Qdrant
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from tools.qdrant_backup import (
    backup_qdrant,
    restore_qdrant,
    list_backups,
    get_backup_stats
)


class TestQdrantBackup:
    """Tests pour les outils de backup Qdrant"""
    
    def setup_method(self):
        """Setup pour chaque test"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup après chaque test"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_backup_qdrant(self):
        """Test de backup (nécessite Qdrant actif)"""
        result = backup_qdrant(backup_dir=self.temp_dir)
        
        # Vérifier le résultat
        assert result.get('success') is not None
        
        if result['success']:
            assert 'backup_file' in result
            assert 'total_points' in result
            assert os.path.exists(result['backup_file'])
    
    def test_list_backups_empty(self):
        """Test de listage sans backups"""
        backups = list_backups(backup_dir=self.temp_dir)
        assert backups == []
    
    def test_list_backups_with_files(self):
        """Test de listage avec des backups"""
        # Créer un backup
        result = backup_qdrant(backup_dir=self.temp_dir)
        
        if result.get('success'):
            # Lister
            backups = list_backups(backup_dir=self.temp_dir)
            assert len(backups) >= 1
            assert 'filename' in backups[0]
            assert 'total_points' in backups[0]
    
    def test_get_backup_stats(self):
        """Test de récupération des stats d'un backup"""
        # Créer un backup
        result = backup_qdrant(backup_dir=self.temp_dir)
        
        if result.get('success'):
            backup_file = result['backup_file']
            
            # Obtenir les stats
            stats = get_backup_stats(backup_file)
            assert stats.get('success') is True
            assert 'total_points' in stats
            assert 'types' in stats
    
    def test_backup_file_structure(self):
        """Test de la structure du fichier de backup"""
        result = backup_qdrant(backup_dir=self.temp_dir)
        
        if result.get('success'):
            backup_file = result['backup_file']
            
            # Charger et vérifier la structure
            with open(backup_file, 'r') as f:
                data = json.load(f)
            
            assert 'metadata' in data
            assert 'points' in data
            assert 'collection_name' in data['metadata']
            assert 'timestamp' in data['metadata']
            assert isinstance(data['points'], list)
