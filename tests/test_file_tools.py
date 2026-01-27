"""
Tests unitaires pour les outils de fichiers
"""

import pytest
import tempfile
import os
from pathlib import Path
from tools.file_tools import (
    read_file,
    write_file,
    append_file,
    replace_in_file,
    list_files,
    file_exists
)


class TestFileTools:
    """Tests pour les outils de manipulation de fichiers"""
    
    def setup_method(self):
        """Créer un répertoire temporaire pour chaque test"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
    
    def teardown_method(self):
        """Nettoyer après chaque test"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_write_file(self):
        """Test d'écriture de fichier"""
        content = "Hello, World!"
        result = write_file(self.test_file, content)
        
        assert result['success'] is True
        assert result['size'] == len(content)
        assert os.path.exists(self.test_file)
        
        # Vérifier le contenu
        with open(self.test_file, 'r') as f:
            assert f.read() == content
    
    def test_write_file_large(self):
        """Test d'écriture d'un fichier trop grand"""
        large_content = "x" * 60000  # > 50KB limit
        result = write_file(self.test_file, large_content)
        
        assert result['success'] is False
        assert 'trop volumineux' in result['error']
    
    def test_read_file(self):
        """Test de lecture de fichier"""
        content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        with open(self.test_file, 'w') as f:
            f.write(content)
        
        # Lire tout le fichier
        result = read_file(self.test_file)
        assert result == content
        
        # Lire des lignes spécifiques (inclut le \n final)
        result = read_file(self.test_file, start_line=2, end_line=3)
        assert result == "Line 2\nLine 3\n"
    
    def test_read_file_not_found(self):
        """Test de lecture d'un fichier inexistant"""
        with pytest.raises(FileNotFoundError):
            read_file("/non/existent/file.txt")
    
    def test_append_file(self):
        """Test d'ajout à un fichier"""
        # Créer un fichier initial
        write_file(self.test_file, "Initial content\n")
        
        # Ajouter du contenu
        result = append_file(self.test_file, "Appended content")
        assert result['success'] is True
        
        # Vérifier
        content = read_file(self.test_file)
        assert content == "Initial content\nAppended content"
    
    def test_replace_in_file(self):
        """Test de remplacement dans un fichier"""
        # Créer un fichier
        original = "Hello World\nThis is a test\nHello again"
        write_file(self.test_file, original)
        
        # Remplacer
        result = replace_in_file(self.test_file, "Hello", "Hi")
        assert result['success'] is True
        assert result['replacements'] == 2
        
        # Vérifier
        content = read_file(self.test_file)
        assert content == "Hi World\nThis is a test\nHi again"
    
    def test_replace_in_file_not_found(self):
        """Test de remplacement d'un texte inexistant"""
        write_file(self.test_file, "Hello World")
        
        result = replace_in_file(self.test_file, "Goodbye", "Hi")
        assert result['success'] is False
        assert 'non trouvé' in result['error']
    
    def test_file_exists(self):
        """Test de vérification d'existence"""
        # Fichier inexistant
        result = file_exists(self.test_file)
        assert result is False
        
        # Créer le fichier
        write_file(self.test_file, "test")
        
        # Fichier existant
        result = file_exists(self.test_file)
        assert result is True
    
    def test_list_files(self):
        """Test de listage de fichiers"""
        # Créer quelques fichiers
        for i in range(3):
            write_file(os.path.join(self.temp_dir, f"file{i}.py"), "test")
        write_file(os.path.join(self.temp_dir, "readme.txt"), "test")
        
        # Lister tous les fichiers
        result = list_files(self.temp_dir)
        assert 'count' in result
        assert result['count'] == 4
        
        # Lister uniquement les .py
        result = list_files(self.temp_dir, pattern="*.py")
        assert 'count' in result
        assert result['count'] == 3
