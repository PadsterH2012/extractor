"""
Comprehensive tests for AI Game Detection functionality.

This module tests the AI-powered game detection capabilities including:
- Game type detection accuracy
- Edition identification
- Confidence scoring
- AI provider integration (OpenRouter, Anthropic, Mock)
- Error handling and fallback mechanisms
- Content analysis and metadata extraction

Priority: 1 (Critical Core Functionality)
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

from Modules.ai_game_detector import AIGameDetector
from tests.conftest import MockPDFDocument


class TestGameTypeDetection:
    """Test game type detection accuracy"""

    def test_dnd_5e_detection(self, mock_ai_config, sample_dnd_content):
        """Test detection of D&D 5th Edition content"""
        detector = AIGameDetector(ai_config=mock_ai_config)

        # Mock the AI response for D&D content
        with patch.object(detector, '_perform_ai_analysis') as mock_ai:
            mock_ai.return_value = {
                "game_type": "D&D",
                "edition": "5th Edition",
                "book_type": "Core Rulebook",
                "collection": "Player's Handbook",
                "confidence": 95.0,
                "reasoning": "Clear D&D 5th Edition content with standard ability scores"
            }

            # Use analyze_game_metadata with a mock PDF path
            with patch('fitz.open') as mock_fitz:
                mock_doc = MockPDFDocument(pages_text=[sample_dnd_content])
                mock_fitz.return_value = mock_doc
                result = detector.analyze_game_metadata(Path("test.pdf"))

            assert result["game_type"] == "D&D"
            assert result["edition"] == "5th Edition"
            assert result["confidence"] >= 90.0
            assert "reasoning" in result

    def test_pathfinder_2e_detection(self, mock_ai_config, sample_pathfinder_content):
        """Test detection of Pathfinder 2nd Edition content"""
        detector = AIGameDetector(ai_config=mock_ai_config)

        with patch.object(detector, '_call_ai_provider') as mock_ai:
            mock_ai.return_value = {
                "game_type": "Pathfinder",
                "edition": "2nd Edition",
                "book_type": "Core Rulebook",
                "collection": "Core Rulebook",
                "confidence": 92.0,
                "reasoning": "Pathfinder 2nd Edition with ancestries and backgrounds"
            }

            result = detector.detect_game_type(sample_pathfinder_content)

            assert result["game_type"] == "Pathfinder"
            assert result["edition"] == "2nd Edition"
            assert result["confidence"] >= 90.0

    def test_unknown_content_detection(self, mock_ai_config):
        """Test detection of unknown/unrecognized content"""
        detector = AIGameDetector(ai_config=mock_ai_config)

        unknown_content = """
        This is some generic text that doesn't relate to any specific
        tabletop RPG system. It might be a novel or technical manual.
        """

        with patch.object(detector, '_call_ai_provider') as mock_ai:
            mock_ai.return_value = {
                "game_type": "Unknown",
                "edition": None,
                "book_type": "Unknown",
                "collection": "Unknown",
                "confidence": 25.0,
                "reasoning": "No clear RPG system indicators found"
            }

            result = detector.detect_game_type(unknown_content)

            assert result["game_type"] == "Unknown"
            assert result["confidence"] < 50.0

    def test_novel_content_detection(self, mock_ai_config):
        """Test detection of novel/fiction content"""
        detector = AIGameDetector(ai_config=mock_ai_config)

        novel_content = """
        Chapter 1: The Unbeliever

        Thomas Covenant was a successful author of bestselling fantasy novels.
        He lived in a rural area on Haven Farm, a place he had bought to
        satisfy his need for a quiet place to write.
        """

        with patch.object(detector, '_call_ai_provider') as mock_ai:
            mock_ai.return_value = {
                "game_type": "Novel",
                "edition": None,
                "book_type": "Fiction",
                "collection": "Fantasy Novel",
                "confidence": 85.0,
                "reasoning": "Narrative fiction content with character development"
            }

            result = detector.detect_game_type(novel_content)

            assert result["game_type"] == "Novel"
            assert result["book_type"] == "Fiction"
            assert result["confidence"] >= 80.0

    def test_confidence_scoring_accuracy(self, mock_ai_config):
        """Test that confidence scores reflect detection accuracy"""
        detector = AIGameDetector(ai_config=mock_ai_config)

        # High confidence content (clear D&D indicators)
        high_confidence_content = """
        DUNGEONS & DRAGONS
        Player's Handbook
        5th Edition

        Ability Scores: Strength, Dexterity, Constitution, Intelligence, Wisdom, Charisma
        Classes: Fighter, Wizard, Rogue, Cleric
        """

        # Low confidence content (ambiguous)
        low_confidence_content = """
        Some text about adventures and magic.
        Characters have abilities and skills.
        """

        with patch.object(detector, '_call_ai_provider') as mock_ai:
            # High confidence response
            mock_ai.return_value = {
                "game_type": "D&D",
                "edition": "5th Edition",
                "confidence": 98.0,
                "reasoning": "Explicit D&D branding and standard terminology"
            }

            high_result = detector.detect_game_type(high_confidence_content)
            assert high_result["confidence"] >= 95.0

            # Low confidence response
            mock_ai.return_value = {
                "game_type": "Unknown",
                "edition": None,
                "confidence": 35.0,
                "reasoning": "Generic RPG terms without specific system indicators"
            }

            low_result = detector.detect_game_type(low_confidence_content)
            assert low_result["confidence"] < 50.0


class TestAIProviderIntegration:
    """Test integration with different AI providers"""

    def test_openrouter_integration(self, sample_dnd_content):
        """Test OpenRouter API integration"""
        openrouter_config = {
            "provider": "openrouter",
            "model": "anthropic/claude-3.5-sonnet",
            "api_key": "test-key",
            "base_url": "https://openrouter.ai/api/v1"
        }

        detector = AIGameDetector(ai_config=openrouter_config)

        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "game_type": "D&D",
                            "edition": "5th Edition",
                            "book_type": "Core Rulebook",
                            "collection": "Player's Handbook",
                            "confidence": 95.0,
                            "reasoning": "Clear D&D 5th Edition content"
                        })
                    }
                }]
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = detector.detect_game_type(sample_dnd_content)

            assert result["game_type"] == "D&D"
            assert mock_post.called

            # Verify correct API endpoint and headers
            call_args = mock_post.call_args
            assert "openrouter.ai" in call_args[1]["url"] or "openrouter.ai" in call_args[0][0]
            assert "Authorization" in call_args[1]["headers"]

    def test_anthropic_integration(self, sample_dnd_content):
        """Test Anthropic API integration"""
        anthropic_config = {
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022",
            "api_key": "test-key"
        }

        detector = AIGameDetector(ai_config=anthropic_config)

        with patch('anthropic.Anthropic') as mock_anthropic_class:
            mock_client = Mock()
            mock_anthropic_class.return_value = mock_client

            mock_response = Mock()
            mock_response.content = [Mock()]
            mock_response.content[0].text = json.dumps({
                "game_type": "D&D",
                "edition": "5th Edition",
                "book_type": "Core Rulebook",
                "collection": "Player's Handbook",
                "confidence": 95.0,
                "reasoning": "Clear D&D 5th Edition content"
            })

            mock_client.messages.create.return_value = mock_response

            result = detector.detect_game_type(sample_dnd_content)

            assert result["game_type"] == "D&D"
            assert mock_client.messages.create.called

    def test_mock_provider_fallback(self, mock_ai_config, sample_dnd_content):
        """Test mock provider fallback functionality"""
        detector = AIGameDetector(ai_config=mock_ai_config)

        result = detector.detect_game_type(sample_dnd_content)

        # Mock provider should return basic detection
        assert "game_type" in result
        assert "confidence" in result
        assert isinstance(result["confidence"], (int, float))

    def test_provider_switching(self, sample_dnd_content):
        """Test switching between AI providers"""
        # Start with OpenRouter
        openrouter_config = {
            "provider": "openrouter",
            "model": "anthropic/claude-3.5-sonnet",
            "api_key": "test-key"
        }

        detector = AIGameDetector(ai_config=openrouter_config)

        # Switch to Anthropic
        anthropic_config = {
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022",
            "api_key": "test-key"
        }

        detector.ai_config = anthropic_config

        # Should adapt to new provider
        with patch.object(detector, '_call_ai_provider') as mock_ai:
            mock_ai.return_value = {
                "game_type": "D&D",
                "edition": "5th Edition",
                "confidence": 95.0
            }

            result = detector.detect_game_type(sample_dnd_content)
            assert result["game_type"] == "D&D"


class TestErrorHandling:
    """Test error handling and fallback mechanisms"""

    def test_api_timeout_handling(self, mock_ai_config, sample_dnd_content):
        """Test handling of API timeouts"""
        detector = AIGameDetector(ai_config=mock_ai_config)

        with patch.object(detector, '_call_ai_provider') as mock_ai:
            mock_ai.side_effect = TimeoutError("API request timed out")

            with pytest.raises(Exception):
                detector.detect_game_type(sample_dnd_content)

    def test_api_rate_limit_handling(self, mock_ai_config, sample_dnd_content):
        """Test handling of API rate limits"""
        detector = AIGameDetector(ai_config=mock_ai_config)

        with patch.object(detector, '_call_ai_provider') as mock_ai:
            mock_ai.side_effect = Exception("Rate limit exceeded")

            with pytest.raises(Exception):
                detector.detect_game_type(sample_dnd_content)

    def test_invalid_api_response_handling(self, mock_ai_config, sample_dnd_content):
        """Test handling of invalid API responses"""
        detector = AIGameDetector(ai_config=mock_ai_config)

        with patch.object(detector, '_call_ai_provider') as mock_ai:
            # Return invalid JSON
            mock_ai.return_value = "Invalid JSON response"

            with pytest.raises(Exception):
                detector.detect_game_type(sample_dnd_content)

    def test_missing_api_key_handling(self, sample_dnd_content):
        """Test handling of missing API keys"""
        config_without_key = {
            "provider": "openrouter",
            "model": "anthropic/claude-3.5-sonnet"
            # Missing api_key
        }

        detector = AIGameDetector(ai_config=config_without_key)

        # Should handle missing API key gracefully
        with pytest.raises(Exception):
            detector.detect_game_type(sample_dnd_content)

    def test_network_error_handling(self, mock_ai_config, sample_dnd_content):
        """Test handling of network connectivity issues"""
        detector = AIGameDetector(ai_config=mock_ai_config)

        with patch.object(detector, '_call_ai_provider') as mock_ai:
            mock_ai.side_effect = ConnectionError("Network unreachable")

            with pytest.raises(Exception):
                detector.detect_game_type(sample_dnd_content)


class TestContentAnalysis:
    """Test content analysis and metadata extraction"""

    def test_analyze_game_metadata_from_pdf(self, mock_ai_config, sample_dnd_content):
        """Test analyzing game metadata from PDF content"""
        detector = AIGameDetector(ai_config=mock_ai_config)

        # Create a mock PDF with D&D content
        mock_pdf = MockPDFDocument(
            metadata={"title": "Player's Handbook", "author": "Wizards of the Coast"},
            pages_text=[sample_dnd_content]
        )

        with patch('fitz.open', return_value=mock_pdf):
            with patch.object(detector, '_call_ai_provider') as mock_ai:
                mock_ai.return_value = {
                    "game_type": "D&D",
                    "edition": "5th Edition",
                    "book_type": "Core Rulebook",
                    "collection": "Player's Handbook",
                    "confidence": 95.0,
                    "reasoning": "Clear D&D 5th Edition content"
                }

                result = detector.analyze_game_metadata(Path("test.pdf"))

                assert result["game_type"] == "D&D"
                assert result["edition"] == "5th Edition"
                assert result["confidence"] >= 90.0

    def test_content_sampling_strategy(self, mock_ai_config):
        """Test content sampling for large documents"""
        detector = AIGameDetector(ai_config=mock_ai_config)

        # Create a large document
        large_content = ["Page " + str(i) + " content"] * 100
        mock_pdf = MockPDFDocument(pages_text=large_content, page_count=100)

        with patch('fitz.open', return_value=mock_pdf):
            with patch.object(detector, '_call_ai_provider') as mock_ai:
                mock_ai.return_value = {
                    "game_type": "D&D",
                    "edition": "5th Edition",
                    "confidence": 85.0
                }

                result = detector.analyze_game_metadata(Path("large.pdf"))

                # Should successfully analyze even large documents
                assert result["game_type"] == "D&D"
                assert mock_ai.called

    def test_metadata_confidence_thresholds(self, mock_ai_config):
        """Test confidence threshold handling"""
        detector = AIGameDetector(ai_config=mock_ai_config)

        test_cases = [
            (95.0, "high"),    # High confidence
            (75.0, "medium"),  # Medium confidence
            (45.0, "low"),     # Low confidence
            (15.0, "very_low") # Very low confidence
        ]

        for confidence, expected_level in test_cases:
            with patch.object(detector, '_call_ai_provider') as mock_ai:
                mock_ai.return_value = {
                    "game_type": "D&D" if confidence > 50 else "Unknown",
                    "edition": "5th Edition" if confidence > 70 else None,
                    "confidence": confidence
                }

                result = detector.detect_game_type("Test content")

                assert result["confidence"] == confidence
                if confidence > 50:
                    assert result["game_type"] != "Unknown"
                else:
                    assert result["game_type"] == "Unknown"
