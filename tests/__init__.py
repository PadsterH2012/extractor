"""
Test package for the Extractor project.

This package contains comprehensive tests for all core functionality:
- PDF processing and extraction
- AI game detection and categorization
- MongoDB operations and data management
- Text quality enhancement
- End-to-end workflows

Test Structure:
- test_pdf_processor.py: Core PDF processing functionality
- test_ai_game_detector.py: AI-powered game detection
- test_mongodb_manager.py: Database operations
- test_text_quality_enhancer.py: Text enhancement features
- test_e2e_extraction.py: End-to-end workflow tests

Test Data:
- fixtures/: Test PDFs and mock data
- conftest.py: Shared fixtures and configuration
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))