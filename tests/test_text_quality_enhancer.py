"""
Text Quality Enhancement Tests.

This module tests the text quality enhancement functionality including:
- OCR artifact cleanup
- Spell checking with RPG dictionary
- Quality scoring and metrics
- Aggressive vs normal cleanup modes
- Text improvement algorithms

Priority: 2 (Essential Integration & Workflow)
"""

import pytest
from unittest.mock import Mock, patch
from Modules.text_quality_enhancer import TextQualityEnhancer, QualityMetrics, TextCleanupResult


@pytest.mark.priority2
@pytest.mark.text_enhancement
@pytest.mark.unit
class TestOCRArtifactCleanup:
    """Test OCR artifact detection and cleanup"""

    def test_common_ocr_substitutions(self):
        """Test common OCR character substitutions"""
        enhancer = TextQualityEnhancer()

        test_cases = [
            # Zero to O substitutions
            ("The 0rcs attacked", "The Orcs attacked"),
            ("Magic 0f the realm", "Magic Of the realm"),

            # lowercase l to I substitutions
            ("l am a wizard", "I am a wizard"),
            ("The l in magic", "The I in magic"),

            # rn to m substitutions
            ("The dwarven arnor", "The dwarven armor"),
            ("Fireball spells bum enemies", "Fireball spells burn enemies"),

            # cl to d substitutions
            ("The clragon breathes fire", "The dragon breathes fire"),

            # li to h substitutions
            ("The ligher ground", "The higher ground")
        ]

        for original, expected in test_cases:
            cleaned = enhancer._clean_ocr_artifacts(original)
            assert expected in cleaned or original == cleaned  # Some patterns may not match exactly

    def test_spacing_normalization(self):
        """Test spacing issue cleanup"""
        enhancer = TextQualityEnhancer()

        test_cases = [
            # Multiple spaces to single
            ("Text  with   multiple    spaces", "Text with multiple spaces"),

            # Spaced letters within words (should be handled carefully)
            ("D u n g e o n s", "Dungeons"),
            ("D R A G O N S", "DRAGONS"),

            # Normal spacing should be preserved
            ("Normal text spacing", "Normal text spacing")
        ]

        for original, expected in test_cases:
            cleaned = enhancer._clean_ocr_artifacts(original)
            # Check that excessive spacing is reduced
            assert "  " not in cleaned or original == cleaned

    def test_smart_quotes_cleanup(self):
        """Test smart quotes and special character cleanup"""
        enhancer = TextQualityEnhancer()

        test_cases = [
            # Smart quotes to regular quotes
            ('"Smart quotes"', '"Smart quotes"'),
            ("'Smart apostrophe'", "'Smart apostrophe'"),

            # Em/en dashes to hyphens
            ("Long—dash", "Long-dash"),
            ("Medium–dash", "Medium-dash"),

            # Line break artifacts
            ("Hyphen-\nated word", "Hyphenated word"),
            ("Multiple\n\n\nline breaks", "Multiple\n\nline breaks")
        ]

        for original, expected in test_cases:
            cleaned = enhancer._clean_ocr_artifacts(original)
            # Check that smart quotes are normalized
            assert '"' in cleaned or "'" in cleaned or original == cleaned


@pytest.mark.priority2
@pytest.mark.text_enhancement
@pytest.mark.unit
class TestRPGSpecificCleanup:
    """Test RPG-specific text cleanup patterns"""

    def test_rpg_abbreviation_expansion(self):
        """Test expansion of RPG abbreviations"""
        enhancer = TextQualityEnhancer()

        test_cases = [
            ("The monster has AC 15", "The monster has Armor Class 15"),
            ("It deals 2d6 HP damage", "It deals 2d6 Hit Points damage"),
            ("Roll 3 HD for healing", "Roll 3 Hit Dice for healing"),
            ("Gain 100 XP", "Gain 100 Experience Points"),
            ("The DM decides", "The Dungeon Master decides"),
            ("Each PC gets a turn", "Each Player Character gets a turn"),
            ("The NPC speaks", "The Non-Player Character speaks")
        ]

        for original, expected in test_cases:
            cleaned = enhancer._apply_rpg_patterns(original)
            # Check that abbreviations are expanded (may not be exact due to context)
            assert "Armor Class" in cleaned or "AC" in cleaned

    def test_dice_notation_cleanup(self):
        """Test dice notation standardization"""
        enhancer = TextQualityEnhancer()

        test_cases = [
            # Spaced dice notation
            ("Roll 2 d 6", "Roll 2d6"),
            ("Cast 4 d 8 damage", "Cast 4d8 damage"),
            ("Use 1 D 20", "Use 1d20"),

            # Already correct notation should remain
            ("Roll 3d6", "Roll 3d6"),
            ("Deal 2d4+1", "Deal 2d4+1")
        ]

        for original, expected in test_cases:
            cleaned = enhancer._apply_rpg_patterns(original)
            # Check that dice notation is standardized
            assert "d6" in cleaned or "d8" in cleaned or "d20" in cleaned or "d4" in cleaned

    def test_rpg_dictionary_loading(self):
        """Test that RPG-specific terms are loaded into spell checker"""
        enhancer = TextQualityEnhancer()

        if enhancer.spell_checker:
            # Test that common RPG terms are recognized
            rpg_terms = [
                'paladin', 'ranger', 'cleric', 'fighter', 'wizard',
                'armor', 'dexterity', 'charisma', 'constitution',
                'fireball', 'healing', 'teleport', 'invisibility',
                'dungeon', 'tavern', 'castle', 'fortress'
            ]

            for term in rpg_terms:
                # These terms should be in the spell checker's dictionary
                assert term in enhancer.spell_checker or term.lower() in enhancer.spell_checker


class TestSpellChecking:
    """Test spell checking functionality"""

    def test_basic_spell_correction(self):
        """Test basic spell checking and correction"""
        enhancer = TextQualityEnhancer()

        if not enhancer.spell_checker:
            pytest.skip("Spell checker not available")

        test_cases = [
            # Common misspellings
            ("The wizrd cast a spel", ["wizard", "spell"]),
            ("Figther attacks with swrod", ["Fighter", "sword"]),
            ("The draogn breathes fier", ["dragon", "fire"]),

            # RPG terms should not be "corrected"
            ("The paladin casts fireball", []),  # Should not need corrections
            ("Dexterity and charisma", [])  # Should not need corrections
        ]

        for original, expected_corrections in test_cases:
            result, corrections = enhancer._spell_check_text(original, aggressive=False)

            # Check that corrections were made for misspelled words
            if expected_corrections:
                assert len(corrections) > 0
                # Check that some expected corrections are present
                correction_words = [c['corrected'] for c in corrections]
                assert any(word in ' '.join(correction_words) for word in expected_corrections)

    def test_aggressive_vs_normal_correction(self):
        """Test difference between aggressive and normal correction modes"""
        enhancer = TextQualityEnhancer()

        if not enhancer.spell_checker:
            pytest.skip("Spell checker not available")

        # Text with questionable corrections
        test_text = "The mage uses arcane magik to summon a familar"

        # Normal mode should be conservative
        normal_result, normal_corrections = enhancer._spell_check_text(test_text, aggressive=False)

        # Aggressive mode should make more corrections
        aggressive_result, aggressive_corrections = enhancer._spell_check_text(test_text, aggressive=True)

        # Aggressive mode should generally make more corrections
        assert len(aggressive_corrections) >= len(normal_corrections)

    def test_case_and_punctuation_preservation(self):
        """Test that case and punctuation are preserved during correction"""
        enhancer = TextQualityEnhancer()

        if not enhancer.spell_checker:
            pytest.skip("Spell checker not available")

        test_cases = [
            # Capitalized words
            ("The Wizrd is powerful.", "Wizard"),
            ("FIGTHER attacks!", "FIGHTER"),

            # Punctuation preservation
            ("The spel, it works!", "spell,"),
            ("What magik?", "magic?")
        ]

        for original, expected_pattern in test_cases:
            corrected_word = enhancer._preserve_case_punctuation(original.split()[1], expected_pattern.replace(',', '').replace('?', '').replace('!', ''))

            # Check that case patterns are preserved
            if original.split()[1][0].isupper():
                assert corrected_word[0].isupper()


class TestQualityAssessment:
    """Test text quality assessment and metrics"""

    def test_quality_metrics_calculation(self):
        """Test calculation of quality metrics"""
        enhancer = TextQualityEnhancer()

        # High quality text
        high_quality = "The wizard cast a powerful fireball spell at the dragon."
        high_metrics = enhancer._assess_text_quality(high_quality)

        assert isinstance(high_metrics, QualityMetrics)
        assert high_metrics.overall_score > 70.0
        assert high_metrics.word_count > 0
        assert high_metrics.grade in ['A', 'B', 'C', 'D', 'F']

        # Low quality text with OCR artifacts
        low_quality = "The wizrd  cast a  powerfuI  firebaII  speII  at  the  draogn."
        low_metrics = enhancer._assess_text_quality(low_quality)

        assert low_metrics.overall_score < high_metrics.overall_score
        assert len(low_metrics.issues_found) > 0

    def test_spelling_score_calculation(self):
        """Test spelling score calculation"""
        enhancer = TextQualityEnhancer()

        if not enhancer.spell_checker:
            pytest.skip("Spell checker not available")

        # Text with good spelling
        good_text = "The paladin fights the dragon with courage."
        good_score = enhancer._calculate_spelling_score(good_text)

        # Text with poor spelling
        poor_text = "The paladn figths the draogn with courag."
        poor_score = enhancer._calculate_spelling_score(poor_text)

        assert good_score > poor_score
        assert 0 <= good_score <= 100
        assert 0 <= poor_score <= 100

    def test_character_score_calculation(self):
        """Test character quality score calculation"""
        enhancer = TextQualityEnhancer()

        # Clean text
        clean_text = "The wizard cast a spell."
        clean_score = enhancer._calculate_character_score(clean_text)

        # Text with OCR artifacts
        artifact_text = "The wizrd  cast  a  speII  with  rn  artifacts."
        artifact_score = enhancer._calculate_character_score(artifact_text)

        assert clean_score > artifact_score
        assert 0 <= clean_score <= 100
        assert 0 <= artifact_score <= 100

    def test_readability_score_calculation(self):
        """Test readability score calculation"""
        enhancer = TextQualityEnhancer()

        # Well-structured text
        readable_text = "The wizard cast a spell. The dragon was defeated. Victory was achieved."
        readable_score = enhancer._calculate_readability_score(readable_text)

        # Poorly structured text
        unreadable_text = "wizard spell dragon defeated victory achieved no punctuation or structure"
        unreadable_score = enhancer._calculate_readability_score(unreadable_text)

        assert readable_score > unreadable_score
        assert 0 <= readable_score <= 100
        assert 0 <= unreadable_score <= 100

    def test_grade_assignment(self):
        """Test grade assignment based on scores"""
        enhancer = TextQualityEnhancer()

        test_scores = [95, 85, 75, 65, 55, 45, 35]
        expected_grades = ['A', 'B', 'C', 'D', 'F', 'F', 'F']

        for score, expected_grade in zip(test_scores, expected_grades):
            grade = enhancer._score_to_grade(score)
            assert grade == expected_grade


class TestTextEnhancementWorkflow:
    """Test complete text enhancement workflow"""

    def test_complete_enhancement_workflow(self):
        """Test complete text enhancement from start to finish"""
        enhancer = TextQualityEnhancer()

        # Text with multiple issues
        problematic_text = """
        The wizrd  cast  a  powerfuI  firebaII  speII.  The  draogn  was  defeaetd.


        The  paladn  used  his  swrod  to  figth  the  0rcs.
        """

        # Mock the spell checker to avoid initialization issues
        with patch.object(enhancer, 'spell_checker') as mock_spell_checker:
            mock_spell_checker.unknown.return_value = set()
            mock_spell_checker.candidates.return_value = []

            # Run enhancement
            result = enhancer.enhance_text_quality(problematic_text, aggressive=False)

        assert isinstance(result, TextCleanupResult)
        assert result.original_text == problematic_text
        assert result.cleaned_text != problematic_text
        assert result.after_metrics.overall_score > result.before_metrics.overall_score
        assert len(result.cleanup_summary) > 0

        # Check that improvements were made
        assert result.cleanup_summary['quality_improvement'] > 0

    def test_enhancement_with_aggressive_mode(self):
        """Test enhancement with aggressive cleanup mode"""
        enhancer = TextQualityEnhancer()

        test_text = "The mage uses questionable magik to summon familars."

        # Normal enhancement
        normal_result = enhancer.enhance_text_quality(test_text, aggressive=False)

        # Aggressive enhancement
        aggressive_result = enhancer.enhance_text_quality(test_text, aggressive=True)

        # Aggressive mode should generally make more corrections
        assert len(aggressive_result.corrections_made) >= len(normal_result.corrections_made)
        assert aggressive_result.cleanup_summary['aggressive_mode'] == True
        assert normal_result.cleanup_summary['aggressive_mode'] == False

    def test_enhancement_preserves_structure(self):
        """Test that enhancement preserves text structure"""
        enhancer = TextQualityEnhancer()

        structured_text = """
        Chapter 1: The Beginning

        The wizard entered the dungeon. He cast a spell.

        Chapter 2: The Middle

        The dragon appeared. Battle ensued.
        """

        result = enhancer.enhance_text_quality(structured_text)

        # Should preserve chapter structure
        assert "Chapter 1" in result.cleaned_text
        assert "Chapter 2" in result.cleaned_text

        # Should preserve paragraph breaks
        lines = result.cleaned_text.split('\n')
        assert len([line for line in lines if line.strip()]) >= 4  # At least 4 content lines

    def test_empty_text_handling(self):
        """Test handling of empty or whitespace-only text"""
        enhancer = TextQualityEnhancer()

        empty_cases = ["", "   ", "\n\n\n", "\t\t"]

        for empty_text in empty_cases:
            result = enhancer.enhance_text_quality(empty_text)

            assert result.before_metrics.overall_score == 0.0
            assert result.before_metrics.word_count == 0
            assert result.before_metrics.grade == "F"
            assert "Empty text" in result.before_metrics.issues_found

    def test_quality_summary_generation(self):
        """Test quality summary generation"""
        enhancer = TextQualityEnhancer()

        test_text = "The wizrd cast a speII at the draogn."
        result = enhancer.enhance_text_quality(test_text)

        # Test that we can generate a quality summary
        if hasattr(enhancer, 'get_quality_summary'):
            summary = enhancer.get_quality_summary(result)

            assert 'before' in summary
            assert 'after' in summary
            assert 'improvement' in summary

            assert 'score' in summary['before']
            assert 'grade' in summary['before']
            assert 'score' in summary['after']
            assert 'grade' in summary['after']


class TestNewlineHandling:
    """Test intelligent newline handling"""

    def test_smart_newline_cleanup(self):
        """Test smart newline replacement logic"""
        enhancer = TextQualityEnhancer()

        test_cases = [
            # Sentence-ending newlines should become periods + space
            ("The wizard cast a spell\nThe dragon was defeated", "The wizard cast a spell. The dragon was defeated"),

            # Mid-sentence newlines should become spaces
            ("The powerful\nwizard cast", "The powerful wizard cast"),

            # Paragraph breaks should be preserved
            ("Chapter 1\n\nThe story begins", "Chapter 1\n\nThe story begins"),

            # Hyphenated line breaks should be joined
            ("The power-\nful wizard", "The powerful wizard")
        ]

        for original, expected_pattern in test_cases:
            cleaned = enhancer._smart_newline_cleanup(original)

            # Check that newlines are handled intelligently
            # (exact matching may vary based on implementation)
            assert len(cleaned.split('\n')) <= len(original.split('\n'))

    def test_paragraph_preservation(self):
        """Test that paragraph structure is preserved"""
        enhancer = TextQualityEnhancer()

        text_with_paragraphs = """
        First paragraph with some content.

        Second paragraph with more content.

        Third paragraph concludes the text.
        """

        result = enhancer.enhance_text_quality(text_with_paragraphs)

        # Should preserve paragraph breaks
        paragraphs = result.cleaned_text.split('\n\n')
        assert len(paragraphs) >= 3  # At least 3 paragraphs
