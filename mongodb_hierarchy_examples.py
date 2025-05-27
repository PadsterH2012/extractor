#!/usr/bin/env python3
"""
MongoDB Hierarchy Examples - Different approaches to organize RPG content
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from Modules.mongodb_manager import MongoDBManager

def demonstrate_hierarchy_approaches():
    """Demonstrate different approaches to hierarchical organization in MongoDB"""
    
    print("🗂️  MongoDB Hierarchy Approaches for RPG Content")
    print("=" * 60)
    
    # Sample game content
    sample_content = {
        "game_type": "D&D",
        "edition": "1st Edition", 
        "book_type": "Core Rules",
        "book_title": "Player's Handbook",
        "collection_name": "phb",
        "sections": [
            {
                "title": "Character Classes",
                "content": "The character classes available in AD&D include...",
                "page": 15,
                "category": "Character Creation"
            },
            {
                "title": "Spells",
                "content": "Magic-user spells are organized by level...",
                "page": 45,
                "category": "Magic"
            }
        ]
    }
    
    print("\n📊 Approach Comparison:")
    print("-" * 40)
    
    # Approach 1: Separate Collections (Current Implementation)
    print("\n🔹 Approach 1: Separate Collections (Current)")
    print("   Collection Names:")
    print("   • source_material.dand.1st_edition.core_rules.phb")
    print("   • source_material.dand.1st_edition.core_rules.dmg")
    print("   • source_material.pathfinder.2nd_edition.core_rulebook.core")
    print("   • source_material.call_of_cthulhu.7th_edition.keeper_rulebook.keeper")
    
    print("\n   Pros:")
    print("   ✅ Clear separation by game/edition/book")
    print("   ✅ Easy to query specific books")
    print("   ✅ Good for large datasets")
    print("   ✅ Natural MongoDB sharding")
    
    print("\n   Cons:")
    print("   ❌ Many collections (can become unwieldy)")
    print("   ❌ Cross-book queries require multiple collections")
    print("   ❌ Collection management overhead")
    
    # Approach 2: Single Collection with Hierarchical Documents
    print("\n🔹 Approach 2: Single Collection with Hierarchical Metadata")
    print("   Collection: source_material")
    print("   Document Structure:")
    print("   {")
    print("     '_id': ObjectId('...'),")
    print("     'hierarchical_path': {")
    print("       'game_type': 'D&D',")
    print("       'edition': '1st Edition',")
    print("       'book_type': 'Core Rules',")
    print("       'collection_name': 'phb',")
    print("       'full_path': 'D&D/1st Edition/Core Rules/phb'")
    print("     },")
    print("     'sections': [...],")
    print("     'content': '...'")
    print("   }")
    
    print("\n   Pros:")
    print("   ✅ Single collection to manage")
    print("   ✅ Easy cross-book queries")
    print("   ✅ Flexible folder-like structure")
    print("   ✅ Supports MongoDB aggregation pipelines")
    
    print("\n   Cons:")
    print("   ❌ Large collection size")
    print("   ❌ Requires good indexing strategy")
    print("   ❌ Less natural separation")
    
    # Approach 3: Hybrid Approach
    print("\n🔹 Approach 3: Hybrid - Game-Level Collections")
    print("   Collection Names:")
    print("   • dnd_source_material")
    print("   • pathfinder_source_material") 
    print("   • call_of_cthulhu_source_material")
    print("   Document Structure:")
    print("   {")
    print("     'edition': '1st Edition',")
    print("     'book_type': 'Core Rules',")
    print("     'book_path': '1st_edition/core_rules/phb',")
    print("     'sections': [...]")
    print("   }")
    
    print("\n   Pros:")
    print("   ✅ Balanced approach")
    print("   ✅ Game-level separation")
    print("   ✅ Manageable collection count")
    print("   ✅ Good query performance")
    
    print("\n   Cons:")
    print("   ❌ Still multiple collections")
    print("   ❌ Cross-game queries need multiple collections")
    
    # Query Examples
    print("\n🔍 Query Examples:")
    print("-" * 40)
    
    print("\n📝 Approach 1 Queries (Separate Collections):")
    print("   # Get all D&D 1st Edition content")
    print("   db.getCollectionNames().filter(name => name.includes('dand.1st_edition'))")
    print("   ")
    print("   # Get specific book")
    print("   db['source_material.dand.1st_edition.core_rules.phb'].find()")
    print("   ")
    print("   # Get all supplements across games")
    print("   db.getCollectionNames().filter(name => name.includes('supplement'))")
    
    print("\n📝 Approach 2 Queries (Single Collection):")
    print("   # Get all D&D 1st Edition content")
    print("   db.source_material.find({'hierarchical_path.game_type': 'D&D', 'hierarchical_path.edition': '1st Edition'})")
    print("   ")
    print("   # Get specific book")
    print("   db.source_material.find({'hierarchical_path.full_path': 'D&D/1st Edition/Core Rules/phb'})")
    print("   ")
    print("   # Get all supplements across games")
    print("   db.source_material.find({'hierarchical_path.book_type': 'Supplement'})")
    
    print("\n📝 Approach 3 Queries (Hybrid):")
    print("   # Get all D&D 1st Edition content")
    print("   db.dnd_source_material.find({'edition': '1st Edition'})")
    print("   ")
    print("   # Get specific book")
    print("   db.dnd_source_material.find({'book_path': '1st_edition/core_rules/phb'})")
    print("   ")
    print("   # Get all supplements (requires multiple queries)")
    print("   db.dnd_source_material.find({'book_type': 'Supplement'})")
    print("   db.pathfinder_source_material.find({'book_type': 'Supplement'})")
    
    # Recommendations
    print("\n💡 Recommendations:")
    print("-" * 40)
    print("🎯 For Small to Medium Collections (< 1000 books):")
    print("   → Use Approach 1 (Current): Separate collections")
    print("   → Clear organization, easy to understand")
    print("   → Good performance for specific book queries")
    
    print("\n🎯 For Large Collections (> 1000 books):")
    print("   → Use Approach 2: Single collection with metadata")
    print("   → Better for complex cross-book analysis")
    print("   → Requires good indexing on hierarchical_path fields")
    
    print("\n🎯 For Multi-Game Platforms:")
    print("   → Use Approach 3: Game-level collections")
    print("   → Balance between organization and performance")
    print("   → Natural separation by game system")
    
    print("\n🔧 Implementation in Your System:")
    print("-" * 40)
    print("Your current system uses Approach 1 (separate collections)")
    print("To switch approaches, modify the 'use_hierarchical_collections' parameter")
    print("in the import request:")
    print("")
    print("// Current (Approach 1)")
    print("{ 'use_hierarchical_collections': true }")
    print("")
    print("// Switch to Approach 2")
    print("{ 'use_hierarchical_collections': false }")

if __name__ == "__main__":
    demonstrate_hierarchy_approaches()
