#!/usr/bin/env python3
"""
Test script for the optimized character identification system
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from Modules.novel_character_identifier import NovelCharacterIdentifier

def test_optimized_character_identification():
    """Test the optimized character identification with a sample novel"""
    
    print("🧪 Testing Optimized Character Identification System")
    print("=" * 60)
    
    # Create test novel sections (simulating Lord Foul's Bane content)
    test_sections = [
        {
            "content": """
            Thomas Covenant was a writer. He lived alone in a house outside the city, 
            struggling with his leprosy and his divorce from Joan. His son Roger was 
            just a baby when Joan left him. The disease had taken two fingers from his 
            right hand, and with them, it seemed, his ability to believe in anything.
            
            Dr. Berenford had been treating his condition for years. The doctor was 
            one of the few people who understood the psychological impact of leprosy 
            in the modern world. "You must be careful, Thomas," he would say. "The 
            disease affects more than just your body."
            """,
            "page": 1,
            "title": "Chapter 1"
        },
        {
            "content": """
            The Land was a place of wonder and terror. High Lord Elena ruled from 
            Revelstone, the great stone city carved into the mountain. She was 
            beautiful and powerful, but there was something desperate in her eyes.
            
            Saltheart Foamfollower, the Giant, had been Covenant's guide and friend. 
            His laughter could shake the mountains, but his sorrow ran deeper than 
            the sea. "Ah, my friend," Foamfollower would say, "you carry burdens 
            that would crush lesser men."
            
            Lord Mhoram was wise beyond his years. He understood the prophecies 
            better than anyone, and he saw the darkness coming. Atiaran, the 
            Stonedownor, had been the first to recognize Covenant's importance.
            """,
            "page": 2,
            "title": "Chapter 2"
        },
        {
            "content": """
            Lord Foul the Despiser waited in his stronghold. The ancient evil had 
            been planning for millennia, and now his time was coming. Drool Rockworm, 
            the mad Cavewight, served as his unwitting tool, wielding the Staff of Law 
            with dangerous ignorance.
            
            Lena was young and beautiful when Covenant first met her. She lived in 
            Mithil Stonedown with her mother Atiaran. The girl's innocence would be 
            shattered by Covenant's actions, setting in motion events that would 
            echo through the ages.
            
            Bannor and Tuvor were Bloodguard, sworn to protect the Lords. Their 
            dedication was absolute, their loyalty unquestioning. They had served 
            for centuries, never aging, never faltering in their duty.
            """,
            "page": 3,
            "title": "Chapter 3"
        }
    ]
    
    # Test metadata
    test_metadata = {
        "book_title": "Lord Foul's Bane",
        "author": "Stephen R. Donaldson",
        "content_type": "novel"
    }
    
    # Test with different AI configurations
    test_configs = [
        {"provider": "mock", "debug": True},
        # Add real providers when testing
        # {"provider": "openrouter", "model": "anthropic/claude-3.5-sonnet", "debug": True}
    ]
    
    for config in test_configs:
        print(f"\n🔧 Testing with AI provider: {config['provider']}")
        print("-" * 40)
        
        try:
            # Initialize character identifier
            identifier = NovelCharacterIdentifier(ai_config=config, debug=True)
            
            # Run optimized character identification
            result = identifier.identify_characters(test_sections, test_metadata)
            
            # Display results
            print(f"✅ Analysis complete!")
            print(f"📊 Characters found: {result['total_characters']}")
            print(f"📈 Analysis method: {result['metadata']['analysis_method']}")
            
            if 'chunks_processed' in result['metadata']:
                print(f"🧩 Chunks processed: {result['metadata']['chunks_processed']}")
                print(f"🔗 API calls made: {result['metadata']['api_calls_made']}")
            
            # Show character details
            if result['characters']:
                print(f"\n👥 Characters identified:")
                for i, char in enumerate(result['characters'][:10], 1):  # Show first 10
                    name = char.get('name', 'Unknown')
                    mentions = char.get('total_mentions', char.get('mentions', 0))
                    role = char.get('role', 'Unknown')
                    confidence = char.get('confidence', 0)
                    
                    print(f"  {i}. {name}")
                    print(f"     Role: {role}")
                    print(f"     Mentions: {mentions}")
                    print(f"     Confidence: {confidence:.2f}")
                    print()
            
            # Show processing stages
            if 'processing_stages' in result:
                stages = result['processing_stages']
                print(f"📋 Processing Summary:")
                
                if 'discovery' in stages:
                    discovery = stages['discovery']
                    print(f"  Discovery: {discovery.get('unique_candidates', 0)} unique candidates found")
                
                if 'filtering' in stages:
                    filtering = stages['filtering']
                    print(f"  Filtering: {filtering.get('candidates_filtered', 0)} candidates passed filter")
                    print(f"  Filter ratio: {filtering.get('filter_ratio', 0):.2%}")
                
                if 'analysis' in stages:
                    analysis = stages['analysis']
                    print(f"  Analysis: {analysis.get('characters_confirmed', 0)} characters confirmed")
            
        except Exception as e:
            print(f"❌ Test failed with {config['provider']}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Optimized character identification testing complete!")

if __name__ == "__main__":
    test_optimized_character_identification()
