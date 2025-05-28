#!/usr/bin/env python3
"""
Test script to demonstrate hierarchical MongoDB collection naming
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from Modules.mongodb_manager import MongoDBManager

def test_hierarchical_collections():
    """Test hierarchical collection naming with sample data"""
    
    # Sample extraction data for different game systems
    test_extractions = [
        {
            "name": "D&D 1st Edition DMG",
            "data": {
                "game_metadata": {
                    "game_type": "D&D",
                    "edition": "1st Edition", 
                    "book_type": "Core Rules",
                    "book_full_name": "Advanced Dungeons & Dragons - Dungeon Masters Guide",
                    "collection_name": "dmg"
                },
                "sections": [
                    {
                        "title": "Combat Rules",
                        "content": "Combat in D&D follows a structured turn-based system...",
                        "page": 1,
                        "category": "Combat"
                    }
                ],
                "summary": {"total_pages": 1, "total_words": 50},
                "source_file": "dmg.pdf"
            },
            "expected_collection": "source_material.dand.1st_edition.core_rules.dmg"
        },
        {
            "name": "Pathfinder 2nd Edition Core Rulebook",
            "data": {
                "game_metadata": {
                    "game_type": "Pathfinder",
                    "edition": "2nd Edition",
                    "book_type": "Core Rulebook", 
                    "book_full_name": "Pathfinder Core Rulebook",
                    "collection_name": "core"
                },
                "sections": [
                    {
                        "title": "Character Creation",
                        "content": "Creating a character in Pathfinder involves several steps...",
                        "page": 1,
                        "category": "Character Creation"
                    }
                ],
                "summary": {"total_pages": 1, "total_words": 45},
                "source_file": "pathfinder_core.pdf"
            },
            "expected_collection": "source_material.pathfinder.2nd_edition.core_rulebook.core"
        },
        {
            "name": "Call of Cthulhu 7th Edition Keeper Rulebook",
            "data": {
                "game_metadata": {
                    "game_type": "Call of Cthulhu",
                    "edition": "7th Edition",
                    "book_type": "Keeper Rulebook",
                    "book_full_name": "Call of Cthulhu Keeper Rulebook",
                    "collection_name": "keeper"
                },
                "sections": [
                    {
                        "title": "Sanity Rules",
                        "content": "Sanity is a crucial mechanic in Call of Cthulhu...",
                        "page": 1,
                        "category": "Rules"
                    }
                ],
                "summary": {"total_pages": 1, "total_words": 40},
                "source_file": "coc_keeper.pdf"
            },
            "expected_collection": "source_material.call_of_cthulhu.7th_edition.keeper_rulebook.keeper"
        }
    ]
    
    # Initialize MongoDB manager
    mongodb_manager = MongoDBManager(debug=True)
    
    if not mongodb_manager.connected:
        print("❌ MongoDB not connected. Please check your .env configuration.")
        return
    
    print("🗂️  Testing Hierarchical MongoDB Collection Naming")
    print("=" * 60)
    
    for test in test_extractions:
        print(f"\n📚 Testing: {test['name']}")
        print("-" * 40)
        
        # Create collection name using the same logic as the UI
        game_metadata = test['data']['game_metadata']
        game_type = game_metadata.get('game_type', 'unknown').lower().replace(' ', '_').replace('&', 'and')
        edition = game_metadata.get('edition', 'unknown').lower().replace(' ', '_').replace('&', 'and')
        book_type = game_metadata.get('book_type', 'unknown').lower().replace(' ', '_').replace('&', 'and')
        collection_base = game_metadata.get('collection_name', 'unknown')
        
        collection_name = f"source_material.{game_type}.{edition}.{book_type}.{collection_base}"
        
        print(f"Game Type: {game_metadata['game_type']}")
        print(f"Edition: {game_metadata['edition']}")
        print(f"Book Type: {game_metadata['book_type']}")
        print(f"Collection Base: {collection_base}")
        print(f"Generated Collection: {collection_name}")
        print(f"Expected Collection: {test['expected_collection']}")
        
        # Check if it matches expected
        if collection_name == test['expected_collection']:
            print("✅ Collection name matches expected format")
        else:
            print("❌ Collection name doesn't match expected format")
        
        # Test both import styles
        print(f"\n🔄 Testing v3 Style Import...")
        success, message = mongodb_manager.import_extracted_content(
            test['data'], 
            collection_name, 
            split_sections=False
        )
        
        if success:
            print(f"✅ v3 Import: {message}")
        else:
            print(f"❌ v3 Import failed: {message}")
        
        print(f"\n🔄 Testing v1/v2 Style Import...")
        success, message = mongodb_manager.import_extracted_content(
            test['data'], 
            f"{collection_name}_split", 
            split_sections=True
        )
        
        if success:
            print(f"✅ v1/v2 Import: {message}")
        else:
            print(f"❌ v1/v2 Import failed: {message}")
    
    print("\n📊 Collection Structure Summary")
    print("-" * 40)
    print("Hierarchical Path Format:")
    print("rpger.source_material.{game_type}.{edition}.{book_type}.{collection_name}")
    print("\nExamples:")
    print("• rpger.source_material.dand.1st_edition.core_rules.dmg")
    print("• rpger.source_material.pathfinder.2nd_edition.core_rulebook.core")
    print("• rpger.source_material.call_of_cthulhu.7th_edition.keeper_rulebook.keeper")
    print("\nBenefits:")
    print("• Organized by game system")
    print("• Edition-specific separation")
    print("• Book type categorization")
    print("• Easy to query by hierarchy level")
    print("• Supports MongoDB aggregation pipelines")

if __name__ == "__main__":
    test_hierarchical_collections()
