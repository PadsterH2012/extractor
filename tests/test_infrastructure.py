"""
Test infrastructure validation.

This module contains basic tests to verify that the test infrastructure
is working correctly before running the main test suites.
"""

import pytest
import sys
from pathlib import Path


class TestInfrastructure:
    """Test that the test infrastructure is working"""
    
    def test_python_version(self):
        """Test that we're running on a supported Python version"""
        assert sys.version_info >= (3, 8), "Python 3.8+ required"
    
    def test_project_structure(self):
        """Test that the project structure is correct"""
        project_root = Path(__file__).parent.parent
        
        # Check for required directories
        assert (project_root / "Modules").exists(), "Modules directory not found"
        assert (project_root / "tests").exists(), "tests directory not found"
        
        # Check for key files
        assert (project_root / "Modules" / "pdf_processor.py").exists(), "pdf_processor.py not found"
        assert (project_root / "Modules" / "ai_game_detector.py").exists(), "ai_game_detector.py not found"
        assert (project_root / "Modules" / "mongodb_manager.py").exists(), "mongodb_manager.py not found"
    
    def test_imports(self):
        """Test that key modules can be imported"""
        try:
            from Modules.pdf_processor import MultiGamePDFProcessor
            from Modules.ai_game_detector import AIGameDetector
            from Modules.mongodb_manager import MongoDBManager
        except ImportError as e:
            pytest.fail(f"Failed to import required modules: {e}")
    
    def test_pytest_markers(self):
        """Test that pytest markers are working"""
        # This test should pass and demonstrates marker usage
        pass
    
    @pytest.mark.slow
    def test_slow_marker(self):
        """Test that slow marker is working"""
        # This test should be skipped when running with --fast
        pass
    
    def test_fixtures_available(self, mock_ai_config, temp_dir):
        """Test that fixtures from conftest.py are available"""
        assert mock_ai_config is not None
        assert "provider" in mock_ai_config
        assert temp_dir.exists()
    
    def test_mock_classes_available(self):
        """Test that mock classes from conftest.py are available"""
        from tests.conftest import MockPDFDocument, MockPDFPage
        
        # Test MockPDFDocument
        mock_doc = MockPDFDocument(
            metadata={"title": "Test"},
            pages_text=["Page 1", "Page 2"]
        )
        
        assert len(mock_doc) == 2
        assert mock_doc[0].get_text() == "Page 1"
        assert mock_doc.metadata["title"] == "Test"
        
        # Test MockPDFPage
        mock_page = MockPDFPage("Test content")
        assert mock_page.get_text() == "Test content"
        assert mock_page.rect.width == 612.0


class TestSampleData:
    """Test that sample data fixtures are working"""
    
    def test_sample_dnd_content(self, sample_dnd_content):
        """Test D&D sample content fixture"""
        assert "DUNGEONS & DRAGONS" in sample_dnd_content
        assert "Player's Handbook" in sample_dnd_content
        assert "5th Edition" in sample_dnd_content
        assert "Strength" in sample_dnd_content
    
    def test_sample_pathfinder_content(self, sample_pathfinder_content):
        """Test Pathfinder sample content fixture"""
        assert "PATHFINDER" in sample_pathfinder_content
        assert "Core Rulebook" in sample_pathfinder_content
        assert "Second Edition" in sample_pathfinder_content
        assert "Ancestries" in sample_pathfinder_content
    
    def test_sample_isbn_texts(self, sample_isbn_texts):
        """Test ISBN sample texts fixture"""
        assert "isbn_10_with_prefix" in sample_isbn_texts
        assert "isbn_13_with_prefix" in sample_isbn_texts
        assert "both_formats" in sample_isbn_texts
        assert "no_isbn" in sample_isbn_texts
        
        # Verify content
        assert "ISBN:" in sample_isbn_texts["isbn_10_with_prefix"]
        assert "ISBN-13:" in sample_isbn_texts["isbn_13_with_prefix"]
    
    def test_mock_ai_responses(self, mock_ai_response_dnd, mock_ai_response_pathfinder, mock_ai_response_unknown):
        """Test AI response fixtures"""
        # D&D response
        assert mock_ai_response_dnd["game_type"] == "D&D"
        assert mock_ai_response_dnd["edition"] == "5th Edition"
        assert mock_ai_response_dnd["confidence"] >= 90.0
        
        # Pathfinder response
        assert mock_ai_response_pathfinder["game_type"] == "Pathfinder"
        assert mock_ai_response_pathfinder["edition"] == "2nd Edition"
        assert mock_ai_response_pathfinder["confidence"] >= 90.0
        
        # Unknown response
        assert mock_ai_response_unknown["game_type"] == "Unknown"
        assert mock_ai_response_unknown["confidence"] < 50.0
    
    def test_sample_extraction_result(self, sample_extraction_result):
        """Test sample extraction result fixture"""
        assert "metadata" in sample_extraction_result
        assert "sections" in sample_extraction_result
        assert "statistics" in sample_extraction_result
        
        metadata = sample_extraction_result["metadata"]
        assert metadata["game_type"] == "D&D"
        assert metadata["edition"] == "5th Edition"
        assert "isbn" in metadata


class TestConfigurationFixtures:
    """Test configuration fixtures"""
    
    def test_mock_ai_config(self, mock_ai_config):
        """Test AI configuration fixture"""
        assert mock_ai_config["provider"] == "mock"
        assert "model" in mock_ai_config
        assert "debug" in mock_ai_config
        assert mock_ai_config["enable_text_enhancement"] == True
    
    def test_mock_mongodb_config(self, mock_mongodb_config):
        """Test MongoDB configuration fixture"""
        assert "connection_string" in mock_mongodb_config
        assert "database_name" in mock_mongodb_config
        assert mock_mongodb_config["database_name"] == "test_rpger"
    
    def test_create_test_pdf_factory(self, create_test_pdf):
        """Test PDF creation factory fixture"""
        pdf_path = create_test_pdf("test.pdf", "Test PDF content")
        
        assert pdf_path.exists()
        assert pdf_path.name == "test.pdf"
        assert "Test PDF content" in pdf_path.read_text()


if __name__ == "__main__":
    # Run infrastructure tests only
    pytest.main([__file__, "-v"])
