#!/usr/bin/env python3
"""
🧱 BUILDING BLOCKS DEMO
Demonstrates the building blocks system for procedural NPC generation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Modules.building_blocks_manager import BuildingBlocksManager
import random

def demo_building_blocks_queries():
    """Demonstrate various building blocks queries"""
    
    print("🧱 BUILDING BLOCKS SYSTEM DEMO")
    print("=" * 50)
    
    try:
        # Initialize building blocks manager
        blocks_manager = BuildingBlocksManager()
        
        # Get collection statistics
        stats = blocks_manager.get_statistics()
        
        print(f"\n📊 COLLECTION OVERVIEW:")
        print(f"   Total Building Blocks: {stats['total_blocks']:,}")
        print(f"   Total Categories: {stats['total_categories']}")
        print(f"   Collection: {stats['collection_name']}")
        
        if stats['total_blocks'] == 0:
            print("\n❌ No building blocks found!")
            print("\n💡 TO POPULATE BUILDING BLOCKS:")
            print("   1. Upload a novel PDF to the UI (http://localhost:5001)")
            print("   2. Select 'Novel' content type")
            print("   3. Run extraction with character identification enabled")
            print("   4. Building blocks will be automatically stored!")
            return False
        
        # Show categories with counts
        print(f"\n📂 AVAILABLE CATEGORIES:")
        for category in stats['categories']:
            novels = len(category['novels'])
            print(f"   • {category['_id']}: {category['count']} blocks from {novels} novel(s)")
        
        # Show novels
        print(f"\n📚 SOURCE NOVELS:")
        for novel in stats['novels']:
            categories = len(novel['categories'])
            print(f"   • {novel['_id']} by {novel['author']}: {novel['blocks']} blocks across {categories} categories")
        
        # Demonstrate procedural generation
        print(f"\n🎲 PROCEDURAL NPC GENERATION DEMO:")
        
        # Generate random NPCs using building blocks
        for i in range(3):
            print(f"\n   🧙 NPC #{i+1}:")
            
            # Get random descriptors from different categories
            try:
                physical = blocks_manager.get_random_blocks('physical_descriptors', count=2)
                emotional = blocks_manager.get_random_blocks('emotional_words', count=1)
                colors = blocks_manager.get_random_blocks('colors', count=1)
                actions = blocks_manager.get_random_blocks('action_verbs', count=1)
                
                if physical:
                    print(f"     Physical: {', '.join(physical)}")
                if emotional:
                    print(f"     Personality: {emotional[0]}")
                if colors:
                    print(f"     Distinctive Color: {colors[0]}")
                if actions:
                    print(f"     Typical Action: {actions[0]}")
                    
            except Exception as e:
                print(f"     ⚠️ Could not generate NPC: {e}")
        
        # Demonstrate category-specific queries
        print(f"\n🔍 CATEGORY-SPECIFIC QUERIES:")
        
        example_categories = ['physical_descriptors', 'emotional_words', 'colors', 'action_verbs']
        
        for category in example_categories:
            try:
                blocks = blocks_manager.get_blocks_by_category(category, limit=5)
                if blocks:
                    print(f"\n   {category.upper().replace('_', ' ')} (showing 5/{len(blocks)}):")
                    for block in blocks[:5]:
                        source = block.get('source', {})
                        novel = source.get('novel_title', 'Unknown')
                        print(f"     • {block['metadata']['original_case']} (from {novel})")
            except Exception as e:
                print(f"   ⚠️ Could not query {category}: {e}")
        
        # Demonstrate search functionality
        print(f"\n🔍 SEARCH FUNCTIONALITY:")
        
        search_terms = ['dark', 'bright', 'tall', 'quick']
        
        for term in search_terms:
            try:
                results = blocks_manager.search_blocks(term, limit=3)
                if results:
                    print(f"\n   Search '{term}' found {len(results)} matches:")
                    for result in results[:3]:
                        category = result['category']
                        original = result['metadata']['original_case']
                        print(f"     • {original} ({category})")
            except Exception as e:
                print(f"   ⚠️ Search for '{term}' failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

def demo_procedural_generation():
    """Demonstrate procedural NPC generation using building blocks"""
    
    print("\n🎭 PROCEDURAL NPC GENERATION")
    print("=" * 40)
    
    try:
        blocks_manager = BuildingBlocksManager()
        
        # Generate 5 random NPCs
        for i in range(5):
            print(f"\n🧙 Generated NPC #{i+1}:")
            
            # Get building blocks for different aspects
            physical = blocks_manager.get_random_blocks('physical_descriptors', count=3)
            emotional = blocks_manager.get_random_blocks('emotional_words', count=2)
            colors = blocks_manager.get_random_blocks('colors', count=1)
            textures = blocks_manager.get_random_blocks('textures', count=1)
            actions = blocks_manager.get_random_blocks('action_verbs', count=2)
            
            # Create NPC description
            description_parts = []
            
            if physical:
                description_parts.append(f"Physical: {', '.join(physical)}")
            if emotional:
                description_parts.append(f"Personality: {', '.join(emotional)}")
            if colors and textures:
                description_parts.append(f"Appearance: {colors[0]} and {textures[0]}")
            elif colors:
                description_parts.append(f"Distinctive Color: {colors[0]}")
            if actions:
                description_parts.append(f"Behaviors: {', '.join(actions)}")
            
            for part in description_parts:
                print(f"     {part}")
            
            if not description_parts:
                print("     ⚠️ No building blocks available for generation")
        
    except Exception as e:
        print(f"❌ Procedural generation failed: {e}")

def main():
    """Main demo function"""
    
    # Run building blocks demo
    success = demo_building_blocks_queries()
    
    if success:
        # Run procedural generation demo
        demo_procedural_generation()
        
        print(f"\n🎉 BUILDING BLOCKS SYSTEM WORKING PERFECTLY!")
        print(f"\n💡 NEXT STEPS:")
        print(f"   • Extract more novels to expand the building blocks library")
        print(f"   • Use building blocks for procedural NPC generation")
        print(f"   • Combine blocks from multiple novels for variety")
        print(f"   • Search and filter blocks by category or content")
    else:
        print(f"\n💡 Run a novel extraction first to populate building blocks!")

if __name__ == "__main__":
    main()
