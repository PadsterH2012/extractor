#!/usr/bin/env python3
"""
Test script for the TextQualityEnhancer class
Shows before/after comparison of text enhancement
"""

import sys
from pathlib import Path

# Import the TextQualityEnhancer class
sys.path.append(str(Path(__file__).resolve().parent))
from enhance_existing_content import TextQualityEnhancer

# Text samples with quality issues
SAMPLES = [
    # Example from the issue description
    "FIENDFOLIO\\ Tomeof Creatures Malevolentand Benignisthefirstmajor",
    
    # Other examples with common issues
    "PlayerCharacterclasses includeFighter,Magic-User,Cleric,and Thief.",
    "Saving throwsare used to avoid  various harmful effects and are based on character class and level.",
    "Armorclassprovides protection againstenemy attacks.",
    "Dungeonlevels typically increase inchallengethe deeper you go.",
    
    # More complex example with multiple issues
    "TheCharacter Sheet isusedto keep trackof all importantstatistics forplayer characters.",
    
    # Example with OCR artifacts
    "Rn0re advanced rulesto handle cornbat situations."
]

def test_enhancement():
    """Test the TextQualityEnhancer with sample text"""
    enhancer = TextQualityEnhancer(debug=True)
    
    print("🔍 Testing Text Quality Enhancement")
    print("==================================\n")
    
    # Process the example from the issue description
    print("📋 Main Example from Issue Description:")
    example = "FIENDFOLIO\\ Tomeof Creatures Malevolentand Benignisthefirstmajor"
    print(f"Original: \"{example}\"")
    print(f"Should be: \"FIEND FOLIO Tome of Creatures Malevolent and Benign is the first major\"")
    
    quality = enhancer.analyze_quality(example)
    print(f"Original Quality Score: {quality['quality_score']}%")
    print(f"Issues: {quality['issues']}")
    
    enhanced, metrics = enhancer.enhance_text(example)
    print(f"Enhanced: \"{enhanced}\"")
    
    comparison = enhancer.get_before_after_comparison(example, enhanced)
    print(f"Quality Improvement: {quality['quality_score']}% → {comparison.get('quality_after', 0)}%")
    print(f"Changes: {metrics['changes']}")
    print()
    
    # Process additional samples
    for i, text in enumerate(SAMPLES[1:], 1):
        print(f"📝 Sample #{i}:")
        print(f"Original: \"{text}\"")
        
        # Analyze original quality
        quality = enhancer.analyze_quality(text)
        print(f"Quality Score: {quality['quality_score']}%")
        print(f"Issues: {quality['issues']}")
        
        # Enhance text
        enhanced, metrics = enhancer.enhance_text(text)
        print(f"Enhanced: \"{enhanced}\"")
        
        # Show comparison
        comparison = enhancer.get_before_after_comparison(text, enhanced)
        print(f"Quality Improvement: {quality['quality_score']}% → {comparison.get('quality_after', 0)}%")
        print(f"Changes: {metrics['changes']}")
        print()


if __name__ == "__main__":
    test_enhancement()