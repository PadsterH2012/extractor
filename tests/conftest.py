"""
Shared test fixtures and configuration for the Extractor project.

This module provides common fixtures used across multiple test files:
- Mock PDF documents and pages
- AI provider mocks
- MongoDB test configurations
- Sample test data
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock
import json


# ============================================================================
# Mock Classes for PDF Processing
# ============================================================================

class MockPDFDocument:
    """Mock PyMuPDF document for testing"""
    
    def __init__(self, metadata: Optional[Dict] = None, pages_text: Optional[List[str]] = None, 
                 page_count: int = 1, name: str = "test.pdf"):
        self.metadata = metadata or {}
        self.pages_text = pages_text or ["Sample page content"]
        self.name = name
        self._page_count = max(page_count, len(self.pages_text))
        
    def __len__(self):
        return self._page_count
    
    def __getitem__(self, index):
        if index < len(self.pages_text):
            return MockPDFPage(self.pages_text[index])
        return MockPDFPage("Empty page")
    
    def close(self):
        pass


class MockPDFPage:
    """Mock PyMuPDF page for testing"""
    
    def __init__(self, text: str = "", width: float = 612.0, height: float = 792.0):
        self.text = text
        self.rect = type('Rect', (), {'width': width, 'height': height})()
        
    def get_text(self, mode: str = "text") -> str:
        if mode == "dict":
            return {
                "blocks": [
                    {
                        "type": 0,  # Text block
                        "bbox": [0, 0, 612, 20],
                        "lines": [
                            {
                                "spans": [
                                    {
                                        "text": self.text,
                                        "bbox": [0, 0, 612, 20],
                                        "font": "Arial",
                                        "size": 12
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        return self.text


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_pdf_metadata():
    """Sample PDF metadata for testing"""
    return {
        "title": "Player's Handbook",
        "author": "Wizards of the Coast",
        "subject": "D&D 5th Edition Core Rulebook ISBN-13: 978-0-7869-6560-1",
        "keywords": "dungeons, dragons, rpg, fantasy",
        "creator": "Adobe InDesign",
        "producer": "Adobe PDF Library"
    }


@pytest.fixture
def sample_dnd_content():
    """Sample D&D content for testing game detection"""
    return """
    DUNGEONS & DRAGONS
    Player's Handbook
    5th Edition
    
    Chapter 1: Step-by-Step Characters
    Your first step in playing an adventurer in the Dungeons & Dragons game is to imagine and create a character of your own.
    
    Ability Scores
    Six abilities provide a quick description of every creature's physical and mental characteristics:
    • Strength, measuring physical power
    • Dexterity, measuring agility
    • Constitution, measuring endurance
    • Intelligence, measuring reasoning ability
    • Wisdom, measuring awareness
    • Charisma, measuring force of personality
    
    Classes
    Every adventurer is a member of a character class. Class broadly describes a character's vocation, what special talents he or she possesses, and the tactics he or she is most likely to employ when exploring a dungeon, fighting monsters, or engaging in a tense negotiation.
    """


@pytest.fixture
def sample_pathfinder_content():
    """Sample Pathfinder content for testing game detection"""
    return """
    PATHFINDER
    Core Rulebook
    Second Edition
    
    Chapter 1: Introduction
    Welcome to Pathfinder, a tabletop fantasy roleplaying game where you and your friends take on the roles of brave adventurers exploring a world beset by magic and evil.
    
    Ability Scores
    Each creature has six ability scores that represent their most basic attributes:
    • Strength represents physical power
    • Dexterity represents agility and reflexes
    • Constitution represents health and stamina
    • Intelligence represents reasoning ability
    • Wisdom represents awareness and insight
    • Charisma represents personal magnetism
    
    Ancestries and Backgrounds
    At 1st level, you build your character by making choices that reflect both their background prior to becoming an adventurer and their innate capabilities.
    """


@pytest.fixture
def mock_ai_config():
    """Mock AI configuration for testing"""
    return {
        "provider": "mock",
        "model": "mock-model",
        "api_key": "test-key",
        "enable_text_enhancement": True,
        "aggressive_cleanup": False,
        "debug": True
    }


@pytest.fixture
def mock_mongodb_config():
    """Mock MongoDB configuration for testing"""
    return {
        "connection_string": "mongodb://localhost:27017/",
        "database_name": "test_rpger",
        "username": None,
        "password": None,
        "auth_source": "admin"
    }


@pytest.fixture
def sample_isbn_texts():
    """Sample texts containing various ISBN formats"""
    return {
        "isbn_10_with_prefix": "This book has ISBN: 0-306-40615-2 on the copyright page",
        "isbn_13_with_prefix": "Published book ISBN-13: 978-0-306-40615-7 for reference",
        "isbn_10_standalone": "Copyright 2023. 0306406152 All rights reserved.",
        "isbn_13_standalone": "Reference number 9780306406157 for this edition",
        "both_formats": """
            ISBN-10: 0-306-40615-2
            ISBN-13: 978-0-306-40615-7
            Published by Test Publisher
        """,
        "no_isbn": "This text contains no ISBN numbers at all",
        "invalid_isbn": "Invalid ISBN: 123-456-789 should not match"
    }


@pytest.fixture
def mock_pdf_with_isbn(sample_pdf_metadata):
    """Create a mock PDF document with ISBN in metadata"""
    return MockPDFDocument(
        metadata=sample_pdf_metadata,
        pages_text=[
            "Title Page",
            "Copyright Page\nISBN-10: 0-7869-6560-8\nPublished 2014",
            "Table of Contents"
        ]
    )


@pytest.fixture
def mock_pdf_without_isbn():
    """Create a mock PDF document without ISBN"""
    return MockPDFDocument(
        metadata={"title": "Test Book", "author": "Test Author"},
        pages_text=["Title Page", "Content without ISBN", "More content"]
    )


@pytest.fixture
def mock_corrupted_pdf():
    """Mock a corrupted PDF that should raise exceptions"""
    mock_doc = Mock()
    mock_doc.side_effect = Exception("Corrupted PDF file")
    return mock_doc


# ============================================================================
# AI Provider Mocks
# ============================================================================

@pytest.fixture
def mock_ai_response_dnd():
    """Mock AI response for D&D content detection"""
    return {
        "game_type": "D&D",
        "edition": "5th Edition",
        "book_type": "Core Rulebook",
        "collection": "Player's Handbook",
        "confidence": 95.0,
        "reasoning": "Clear D&D 5th Edition content with standard ability scores and class system"
    }


@pytest.fixture
def mock_ai_response_pathfinder():
    """Mock AI response for Pathfinder content detection"""
    return {
        "game_type": "Pathfinder",
        "edition": "2nd Edition", 
        "book_type": "Core Rulebook",
        "collection": "Core Rulebook",
        "confidence": 92.0,
        "reasoning": "Pathfinder 2nd Edition content with ancestries and backgrounds"
    }


@pytest.fixture
def mock_ai_response_unknown():
    """Mock AI response for unknown content"""
    return {
        "game_type": "Unknown",
        "edition": None,
        "book_type": "Unknown",
        "collection": "Unknown",
        "confidence": 30.0,
        "reasoning": "Unable to identify specific game system"
    }


# ============================================================================
# Test Data Helpers
# ============================================================================

@pytest.fixture
def create_test_pdf(temp_dir):
    """Factory function to create test PDF files"""
    def _create_pdf(filename: str, content: str = "Test content") -> Path:
        pdf_path = temp_dir / filename
        # Create a minimal PDF-like file for testing
        # Note: This is not a real PDF, just for file system testing
        pdf_path.write_text(f"%PDF-1.4\n{content}\n%%EOF")
        return pdf_path
    return _create_pdf


@pytest.fixture
def sample_extraction_result():
    """Sample extraction result for testing"""
    return {
        "metadata": {
            "file_name": "test.pdf",
            "game_type": "D&D",
            "edition": "5th Edition",
            "book_type": "Core Rulebook",
            "collection": "Player's Handbook",
            "confidence": 95.0,
            "isbn": "9780786965601",
            "extraction_date": "2024-01-01T12:00:00Z"
        },
        "sections": [
            {
                "title": "Chapter 1: Characters",
                "content": "Character creation rules...",
                "page_start": 1,
                "page_end": 10,
                "section_type": "chapter"
            }
        ],
        "statistics": {
            "total_pages": 320,
            "sections_extracted": 15,
            "processing_time": 45.2
        }
    }
