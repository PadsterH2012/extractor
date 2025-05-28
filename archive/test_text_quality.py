#!/usr/bin/env python3
"""
Test script for Text Quality Enhancement
Demonstrates spell checking and text cleanup functionality
"""

import sys
from pathlib import Path

# Add the Modules directory to the path
sys.path.append(str(Path(__file__).parent / 'Modules'))

try:
    from text_quality_enhancer import TextQualityEnhancer
    print("✅ Text Quality Enhancer imported successfully")
except ImportError as e:
    print(f"❌ Failed to import TextQualityEnhancer: {e}")
    print("Installing required packages...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "pyspellchecker", "textblob", "nltk"])
    from text_quality_enhancer import TextQualityEnhancer
    print("✅ Text Quality Enhancer imported after installation")

def test_basic_functionality():
    """Test basic text quality enhancement"""
    print("\n" + "="*60)
    print("🧪 TESTING BASIC TEXT QUALITY ENHANCEMENT")
    print("="*60)

    # Initialize enhancer
    enhancer = TextQualityEnhancer()

    # Test text with various issues
    test_text = """
    This is a sampel text with speling erors and OCR artifcats.
    The   spacing    is   inconsistant and there are "smart quotes".

    Some words are mis-speled like "recieve" and "seperate".
    There are also rn issues where m should be, and l issues where I should be.

    THAC0 is an important D&D mechanic, as are HP and AC values.
    A fighter with 18 strength can wield a longsword effectively.
    """

    print(f"📝 Original text ({len(test_text)} chars):")
    print(test_text)

    # Test with normal cleanup
    print("\n🔧 Testing normal cleanup...")
    result = enhancer.enhance_text_quality(test_text, aggressive=False)

    print(f"\n✨ Enhanced text ({len(result.cleaned_text)} chars):")
    print(result.cleaned_text)

    # Display quality metrics
    summary = enhancer.get_quality_summary(result)
    print(f"\n📊 Quality Improvement:")
    print(f"   Before: {summary['before']['score']}% (Grade {summary['before']['grade']})")
    print(f"   After:  {summary['after']['score']}% (Grade {summary['after']['grade']})")
    print(f"   Change: +{summary['improvement']['score_change']}% ({summary['improvement']['grade_change']})")
    print(f"   Corrections: {summary['improvement']['corrections_made']}")

    # Show individual corrections
    if result.corrections_made:
        print(f"\n🔍 Corrections made:")
        for correction in result.corrections_made[:5]:  # Show first 5
            print(f"   '{correction['original']}' → '{correction['corrected']}'")
        if len(result.corrections_made) > 5:
            print(f"   ... and {len(result.corrections_made) - 5} more")

    return result

def test_aggressive_cleanup():
    """Test aggressive cleanup mode"""
    print("\n" + "="*60)
    print("🧪 TESTING AGGRESSIVE CLEANUP MODE")
    print("="*60)

    enhancer = TextQualityEnhancer()

    # Text with more challenging issues
    test_text = """
    This documnet contians many erors that need agressive corection.
    The OCR has introducted many artifcats like rn instead of m.

    Sorne words are badly mis-speled and need forceful corection.
    There are also issues with "smart quotes" and inconsistant spacing.

    D&D terns like THAC0, armor class, and hit points should be preserved.
    """

    print(f"📝 Original text:")
    print(test_text)

    # Test aggressive cleanup
    result = enhancer.enhance_text_quality(test_text, aggressive=True)

    print(f"\n✨ Aggressively enhanced text:")
    print(result.cleaned_text)

    # Display metrics
    summary = enhancer.get_quality_summary(result)
    print(f"\n📊 Aggressive Quality Improvement:")
    print(f"   Before: {summary['before']['score']}% (Grade {summary['before']['grade']})")
    print(f"   After:  {summary['after']['score']}% (Grade {summary['after']['grade']})")
    print(f"   Change: +{summary['improvement']['score_change']}% ({summary['improvement']['grade_change']})")
    print(f"   Corrections: {summary['improvement']['corrections_made']}")

    return result

def test_rpg_specific_content():
    """Test with RPG-specific content"""
    print("\n" + "="*60)
    print("🧪 TESTING RPG-SPECIFIC CONTENT")
    print("="*60)

    enhancer = TextQualityEnhancer()

    # RPG content with typical issues
    rpg_text = """
    The paladin has an AC of 2 and 45 HP. His THAC0 is 12.
    He weilds a +2 longsword and wears platemail armor.

    The wizard can cast magic missle and fireball spells.
    She has 18 inteligence and knows many cantrips.

    The party encounters a group of orcs and goblins.
    The dungeon master rolls for initative.
    """

    print(f"📝 RPG text:")
    print(rpg_text)

    result = enhancer.enhance_text_quality(rpg_text, aggressive=False)

    print(f"\n✨ Enhanced RPG text:")
    print(result.cleaned_text)

    # Check if RPG terms are preserved
    rpg_terms = ['THAC0', 'AC', 'HP', 'paladin', 'wizard', 'longsword', 'platemail']
    preserved_terms = [term for term in rpg_terms if term.lower() in result.cleaned_text.lower()]

    print(f"\n🎲 RPG Terms Preserved: {len(preserved_terms)}/{len(rpg_terms)}")
    print(f"   Preserved: {', '.join(preserved_terms)}")

    summary = enhancer.get_quality_summary(result)
    print(f"\n📊 RPG Content Quality:")
    print(f"   Before: {summary['before']['score']}% → After: {summary['after']['score']}%")

    return result

def test_newline_handling():
    """Test intelligent newline handling"""
    print("\n" + "="*60)
    print("🧪 TESTING SMART NEWLINE HANDLING")
    print("="*60)

    enhancer = TextQualityEnhancer()

    # Test text with problematic newlines
    test_text = """This is a sentence that gets broken
across multiple lines without proper
punctuation which creates readability issues

This is another paragraph
that also has line breaks
in the middle of sentences

ARMOR CLASS
This is a definition that should
be properly formatted

• List item one
• List item two
• List item three"""

    print("📝 Original text with problematic newlines:")
    print(repr(test_text))
    print("\nFormatted view:")
    print(test_text)

    # Test smart newline cleanup
    result = enhancer.enhance_text_quality(test_text, aggressive=False)

    print(f"\n✨ Enhanced text with smart newline handling:")
    print(repr(result.cleaned_text))
    print("\nFormatted view:")
    print(result.cleaned_text)

    # Show the improvement
    summary = enhancer.get_quality_summary(result)
    print(f"\n📊 Newline Cleanup Quality:")
    print(f"   Before: {summary['before']['score']}% → After: {summary['after']['score']}%")
    print(f"   Readability improvement: {summary['details']['readability_improvement']}%")

    return result

def test_quality_scoring():
    """Test quality scoring on different text types"""
    print("\n" + "="*60)
    print("🧪 TESTING QUALITY SCORING")
    print("="*60)

    enhancer = TextQualityEnhancer()

    test_cases = [
        ("Perfect text", "This is perfectly written text with no errors whatsoever."),
        ("Minor issues", "This text has a few mispelled words but is mostly good."),
        ("Major issues", "Ths txt hs mny erors nd OCR artifcts tht ned fixng."),
        ("OCR artifacts", "This text has rn instead of m and l instead of I issues."),
        ("Empty text", ""),
    ]

    print("📊 Quality Scores for Different Text Types:")
    print("-" * 60)

    for name, text in test_cases:
        if text:
            result = enhancer.enhance_text_quality(text, aggressive=False)
            summary = enhancer.get_quality_summary(result)
            print(f"{name:15} | {summary['before']['score']:5.1f}% ({summary['before']['grade']}) → {summary['after']['score']:5.1f}% ({summary['after']['grade']}) | +{summary['improvement']['score_change']:4.1f}%")
        else:
            # Handle empty text
            before_metrics = enhancer._assess_text_quality(text)
            print(f"{name:15} | {before_metrics.overall_score:5.1f}% ({before_metrics.grade}) → N/A      | N/A")

def main():
    """Run all tests"""
    print("🚀 TEXT QUALITY ENHANCEMENT TEST SUITE")
    print("Testing spell checking, OCR cleanup, and quality scoring")

    try:
        # Run all tests
        test_basic_functionality()
        test_aggressive_cleanup()
        test_rpg_specific_content()
        test_newline_handling()
        test_quality_scoring()

        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n💡 Key Features Demonstrated:")
        print("   • Spell checking with RPG dictionary")
        print("   • OCR artifact cleanup")
        print("   • Smart newline handling (\\n → '. ' where appropriate)")
        print("   • Quality scoring (A-F grades)")
        print("   • Before/after metrics")
        print("   • Normal vs aggressive cleanup modes")
        print("   • RPG-specific term preservation")

        print("\n🎯 Integration Ready:")
        print("   • Add to PDF extraction pipeline")
        print("   • Display quality scores in Web UI")
        print("   • User-controlled cleanup levels")
        print("   • Detailed improvement metrics")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
