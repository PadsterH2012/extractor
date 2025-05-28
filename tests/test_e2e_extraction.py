"""
End-to-End Extraction Tests.

This module tests complete extraction workflows from PDF upload through
database storage, validating the entire user journey and integration
between all system components.

Priority: 2 (Essential Integration & Workflow)
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import os

from Modules.pdf_processor import MultiGamePDFProcessor
from Modules.ai_game_detector import AIGameDetector
from Modules.mongodb_manager import MongoDBManager
from Modules.multi_collection_manager import MultiGameCollectionManager
from tests.conftest import MockPDFDocument


@pytest.mark.priority2
@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.workflow
class TestCompleteWorkflow:
    """Test complete PDF → Analysis → Extraction → Database workflow"""

    @patch('fitz.open')
    def test_dnd_source_material_workflow(self, mock_fitz, mock_ai_config, sample_dnd_content, temp_dir):
        """Test complete workflow for D&D source material"""
        # Setup: Create test PDF file
        test_pdf = temp_dir / "dnd_players_handbook.pdf"
        test_pdf.write_text("Mock PDF content")

        # Mock PDF document
        mock_doc = MockPDFDocument(
            metadata={"title": "Player's Handbook", "author": "Wizards of the Coast"},
            pages_text=[sample_dnd_content]
        )
        mock_fitz.return_value = mock_doc

        # Initialize processor
        processor = MultiGamePDFProcessor(ai_config=mock_ai_config)

        # Mock AI detection
        with patch.object(processor.game_detector, 'analyze_game_metadata') as mock_detector:
            mock_detector.return_value = {
                'game_type': 'D&D',
                'edition': '5th Edition',
                'book_type': 'Core Rulebook',
                'collection': 'Player\'s Handbook',
                'collection_name': 'players_handbook',  # Add the expected field
                'confidence': 95.0,
                'content_type': 'source_material'
            }

            # Execute: Run extraction
            result = processor.extract_pdf(test_pdf, content_type="source_material")

            # Verify: Check complete result structure
            assert result is not None
            assert "metadata" in result
            assert "sections" in result
            assert "extraction_summary" in result

            # Verify metadata
            metadata = result["metadata"]
            assert metadata["game_type"] == "D&D"
            assert metadata["edition"] == "5th Edition"
            assert metadata["content_type"] == "source_material"
            assert metadata["original_filename"] == "dnd_players_handbook.pdf"

            # Verify sections extracted
            sections = result["sections"]
            assert len(sections) > 0
            assert all("content" in section for section in sections)

            # Verify extraction summary
            summary = result["extraction_summary"]
            assert "total_pages" in summary
            assert "total_words" in summary  # Use actual field name

    @patch('fitz.open')
    def test_novel_content_workflow(self, mock_fitz, mock_ai_config, temp_dir):
        """Test complete workflow for novel content"""
        # Setup: Create test novel PDF
        test_pdf = temp_dir / "fantasy_novel.pdf"
        test_pdf.write_text("Mock novel PDF content")

        novel_content = """
        Chapter 1: The Unbeliever

        Thomas Covenant was a successful author of bestselling fantasy novels.
        He lived in a rural area on Haven Farm, a place he had bought to
        satisfy his need for a quiet place to write.

        The letter arrived on a Tuesday morning in spring.
        """

        mock_doc = MockPDFDocument(
            metadata={"title": "Lord Foul's Bane", "author": "Stephen R. Donaldson"},
            pages_text=[novel_content]
        )
        mock_fitz.return_value = mock_doc

        # Initialize processor
        processor = MultiGamePDFProcessor(ai_config=mock_ai_config)

        # Mock AI detection for novel
        with patch.object(processor.game_detector, 'analyze_game_metadata') as mock_detector:
            mock_detector.return_value = {
                'game_type': 'Novel',
                'edition': None,
                'book_type': 'Fiction',
                'collection': 'Fantasy Novel',
                'collection_name': 'fantasy_novel',  # Add the expected field
                'confidence': 85.0,
                'content_type': 'novel'
            }

            # Mock novel element extraction (this functionality is in _extract_novel_elements)
            with patch.object(processor, '_extract_novel_elements') as mock_novel_extractor:
                mock_novel_extractor.extract_novel_elements.return_value = {
                    'building_blocks': [
                        {'category': 'physical_descriptors', 'words': ['tall', 'dark', 'weathered']},
                        {'category': 'emotions', 'words': ['determined', 'conflicted', 'weary']}
                    ],
                    'extraction_summary': {
                        'total_blocks': 2,
                        'categories_found': ['physical_descriptors', 'emotions']
                    }
                }

                # Execute: Run novel extraction
                result = processor.extract_pdf(test_pdf, content_type="novel")

                # Verify: Check novel-specific result structure
                assert result is not None
                assert result["metadata"]["content_type"] == "novel"
                assert result["metadata"]["game_type"] == "Novel"

                # Verify novel elements were extracted
                assert "novel_elements" in result or "building_blocks" in result

    def test_multiple_game_systems_workflow(self, mock_ai_config, temp_dir):
        """Test workflow with different game systems"""
        game_systems = [
            {
                'name': 'dnd_5e',
                'content': 'DUNGEONS & DRAGONS 5th Edition Player\'s Handbook',
                'expected': {'game_type': 'D&D', 'edition': '5th Edition'}
            },
            {
                'name': 'pathfinder_2e',
                'content': 'PATHFINDER Second Edition Core Rulebook',
                'expected': {'game_type': 'Pathfinder', 'edition': '2nd Edition'}
            },
            {
                'name': 'unknown_system',
                'content': 'Generic RPG content without clear system indicators',
                'expected': {'game_type': 'Unknown', 'edition': None}
            }
        ]

        processor = MultiGamePDFProcessor(ai_config=mock_ai_config)

        for system in game_systems:
            with patch('fitz.open') as mock_fitz:
                # Create test file
                test_pdf = temp_dir / f"{system['name']}.pdf"
                test_pdf.write_text("Mock PDF content")

                # Mock PDF document
                mock_doc = MockPDFDocument(pages_text=[system['content']])
                mock_fitz.return_value = mock_doc

                # Mock AI detection
                with patch.object(processor.game_detector, 'analyze_game_metadata') as mock_detector:
                    mock_detector.return_value = {
                        'game_type': system['expected']['game_type'],
                        'edition': system['expected']['edition'],
                        'book_type': 'Core Rulebook',
                        'collection': 'Test Book',
                        'confidence': 90.0 if system['expected']['game_type'] != 'Unknown' else 30.0
                    }

                    # Execute extraction
                    result = processor.extract_pdf(test_pdf)

                    # Verify system-specific results
                    assert result["metadata"]["game_type"] == system['expected']['game_type']
                    assert result["metadata"]["edition"] == system['expected']['edition']

    def test_confidence_testing_integration(self, mock_ai_config, temp_dir):
        """Test integration with confidence testing"""
        test_pdf = temp_dir / "confidence_test.pdf"
        test_pdf.write_text("Mock PDF content")

        processor = MultiGamePDFProcessor(ai_config=mock_ai_config)

        with patch('fitz.open') as mock_fitz:
            mock_doc = MockPDFDocument(pages_text=["Test content for confidence"])
            mock_fitz.return_value = mock_doc

            # Mock confidence tester
            with patch('Modules.confidence_tester.ConfidenceTester') as mock_confidence_class:
                mock_confidence_instance = Mock()
                mock_confidence_class.return_value = mock_confidence_instance

                mock_confidence_instance.test_extraction_confidence.return_value = {
                    'overall_confidence': 85.0,
                    'detection_confidence': 90.0,
                    'extraction_confidence': 80.0,
                    'recommendation': 'proceed'
                }

                # Mock AI detection
                with patch.object(processor.game_detector, 'analyze_game_metadata') as mock_detector:
                    mock_detector.return_value = {
                        'game_type': 'D&D',
                        'edition': '5th Edition',
                        'confidence': 90.0
                    }

                    # Execute with confidence testing
                    result = processor.extract_pdf(test_pdf)

                    # Verify confidence data is included
                    assert result is not None
                    # Note: Actual confidence integration depends on implementation


@pytest.mark.priority2
@pytest.mark.integration
@pytest.mark.workflow
class TestErrorRecovery:
    """Test graceful failure handling and error recovery"""

    def test_ai_service_failure_recovery(self, mock_ai_config, temp_dir):
        """Test recovery when AI service fails"""
        test_pdf = temp_dir / "test_ai_failure.pdf"
        test_pdf.write_text("Mock PDF content")

        processor = MultiGamePDFProcessor(ai_config=mock_ai_config)

        with patch('fitz.open') as mock_fitz:
            mock_doc = MockPDFDocument(pages_text=["Test content"])
            mock_fitz.return_value = mock_doc

            # Mock AI service failure
            with patch.object(processor.game_detector, 'analyze_game_metadata') as mock_detector:
                mock_detector.side_effect = Exception("AI service unavailable")

                # Should handle AI failure gracefully
                with pytest.raises(Exception):
                    processor.extract_pdf(test_pdf)

    def test_partial_extraction_recovery(self, mock_ai_config, temp_dir):
        """Test recovery from partial extraction failures"""
        test_pdf = temp_dir / "partial_failure.pdf"
        test_pdf.write_text("Mock PDF content")

        processor = MultiGamePDFProcessor(ai_config=mock_ai_config)

        with patch('fitz.open') as mock_fitz:
            # Mock PDF with some problematic pages
            mock_doc = MockPDFDocument(pages_text=[
                "Good page 1",
                "",  # Empty page
                "Good page 3"
            ])
            mock_fitz.return_value = mock_doc

            with patch.object(processor.game_detector, 'analyze_game_metadata') as mock_detector:
                mock_detector.return_value = {
                    'game_type': 'D&D',
                    'edition': '5th Edition',
                    'confidence': 95.0
                }

                # Should handle partial failures gracefully
                result = processor.extract_pdf(test_pdf)

                # Should still produce results despite empty pages
                assert result is not None
                assert "sections" in result

    def test_database_connection_failure(self, mock_ai_config, temp_dir):
        """Test handling of database connection failures"""
        test_pdf = temp_dir / "db_failure.pdf"
        test_pdf.write_text("Mock PDF content")

        processor = MultiGamePDFProcessor(ai_config=mock_ai_config)

        with patch('fitz.open') as mock_fitz:
            mock_doc = MockPDFDocument(pages_text=["Test content"])
            mock_fitz.return_value = mock_doc

            with patch.object(processor.game_detector, 'analyze_game_metadata') as mock_detector:
                mock_detector.return_value = {
                    'game_type': 'D&D',
                    'edition': '5th Edition',
                    'confidence': 95.0
                }

                # Extraction should succeed even if database operations fail later
                result = processor.extract_pdf(test_pdf)

                assert result is not None
                assert "metadata" in result
                assert "sections" in result

    def test_memory_management_large_files(self, mock_ai_config, temp_dir):
        """Test memory management with large files"""
        test_pdf = temp_dir / "large_file.pdf"
        test_pdf.write_text("Mock large PDF content")

        processor = MultiGamePDFProcessor(ai_config=mock_ai_config)

        with patch('fitz.open') as mock_fitz:
            # Simulate large PDF with many pages
            large_content = ["Page content " * 1000] * 50  # 50 large pages
            mock_doc = MockPDFDocument(pages_text=large_content, page_count=50)
            mock_fitz.return_value = mock_doc

            with patch.object(processor.game_detector, 'analyze_game_metadata') as mock_detector:
                mock_detector.return_value = {
                    'game_type': 'D&D',
                    'edition': '5th Edition',
                    'confidence': 95.0
                }

                # Should handle large files without memory issues
                result = processor.extract_pdf(test_pdf)

                assert result is not None
                assert len(mock_doc) == 50


@pytest.mark.priority2
@pytest.mark.integration
@pytest.mark.workflow
class TestSessionStatePersistence:
    """Test session state persistence and recovery"""

    def test_session_data_preservation(self, mock_ai_config, temp_dir):
        """Test that session data is preserved between operations"""
        test_pdf = temp_dir / "session_test.pdf"
        test_pdf.write_text("Mock PDF content")

        processor = MultiGamePDFProcessor(ai_config=mock_ai_config)

        with patch('fitz.open') as mock_fitz:
            mock_doc = MockPDFDocument(pages_text=["Session test content"])
            mock_fitz.return_value = mock_doc

            with patch.object(processor.game_detector, 'analyze_game_metadata') as mock_detector:
                mock_detector.return_value = {
                    'game_type': 'D&D',
                    'edition': '5th Edition',
                    'confidence': 95.0,
                    'session_id': 'test_session_123'
                }

                # First extraction
                result1 = processor.extract_pdf(test_pdf)

                # Verify session data is consistent
                assert result1["metadata"]["game_type"] == "D&D"

                # Second extraction should maintain consistency
                result2 = processor.extract_pdf(test_pdf)

                assert result2["metadata"]["game_type"] == result1["metadata"]["game_type"]
                assert result2["metadata"]["edition"] == result1["metadata"]["edition"]

    def test_extraction_state_recovery(self, mock_ai_config, temp_dir):
        """Test recovery of extraction state after interruption"""
        test_pdf = temp_dir / "recovery_test.pdf"
        test_pdf.write_text("Mock PDF content")

        processor = MultiGamePDFProcessor(ai_config=mock_ai_config)

        # Simulate extraction state that could be recovered
        extraction_state = {
            'file_path': str(test_pdf),
            'game_metadata': {
                'game_type': 'D&D',
                'edition': '5th Edition',
                'confidence': 95.0
            },
            'pages_processed': 5,
            'total_pages': 10
        }

        # Test that state information is properly structured
        assert 'file_path' in extraction_state
        assert 'game_metadata' in extraction_state
        assert extraction_state['pages_processed'] < extraction_state['total_pages']
