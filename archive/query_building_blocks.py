#!/usr/bin/env python3
"""
🧱 BUILDING BLOCKS QUERY TOOL
Query and display the building blocks extracted from novels for procedural NPC generation.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import pymongo
from pymongo import MongoClient

# Update path for archive location
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

def query_building_blocks_from_json(json_file: str) -> Dict[str, Any]:
    """Query building blocks from extraction results JSON file"""

    print(f"🔍 Searching for building blocks in: {json_file}")

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Look for building blocks in various locations
        building_blocks = None

        # Check if it's a novel extraction result with character identification
        if 'character_identification' in data:
            char_data = data['character_identification']
            if 'building_blocks' in char_data:
                building_blocks = char_data['building_blocks']
                print("✅ Found building blocks in character_identification section")

        # Check if building blocks are at root level
        elif 'building_blocks' in data:
            building_blocks = data['building_blocks']
            print("✅ Found building blocks at root level")

        # Check if it's in novel element extraction results
        elif 'novel_element_extraction' in data:
            novel_data = data['novel_element_extraction']
            if 'building_blocks' in novel_data:
                building_blocks = novel_data['building_blocks']
                print("✅ Found building blocks in novel_element_extraction section")

        if building_blocks:
            return analyze_building_blocks(building_blocks)
        else:
            print("❌ No building blocks found in JSON file")
            return {}

    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return {}

def query_building_blocks_from_mongodb(collection_name: str = None) -> Dict[str, Any]:
    """Query building blocks from MongoDB collections"""

    print(f"🔍 Searching for building blocks in MongoDB...")

    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://10.202.28.46:27017/', serverSelectionTimeoutMS=5000)
        client.server_info()  # Test connection
        db = client['rpger']

        # Get all collections if none specified
        if not collection_name:
            collections = db.list_collection_names()
            print(f"📚 Available collections: {collections}")

            # Look for novel collections
            novel_collections = [col for col in collections if 'novel' in col.lower()]
            if novel_collections:
                collection_name = novel_collections[0]
                print(f"🎯 Using novel collection: {collection_name}")
            else:
                print("❌ No novel collections found")
                return {}

        collection = db[collection_name]

        # Look for documents with building blocks
        doc_with_blocks = collection.find_one({'building_blocks': {'$exists': True}})

        if doc_with_blocks and 'building_blocks' in doc_with_blocks:
            print("✅ Found building blocks in MongoDB")
            return analyze_building_blocks(doc_with_blocks['building_blocks'])

        # Look for documents with character identification containing building blocks
        doc_with_char_id = collection.find_one({'character_identification.building_blocks': {'$exists': True}})

        if doc_with_char_id:
            building_blocks = doc_with_char_id['character_identification']['building_blocks']
            print("✅ Found building blocks in character identification data")
            return analyze_building_blocks(building_blocks)

        print("❌ No building blocks found in MongoDB")
        return {}

    except Exception as e:
        print(f"❌ MongoDB error: {e}")
        return {}

def analyze_building_blocks(building_blocks: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze and display building blocks structure"""

    print("\n🧱 BUILDING BLOCKS ANALYSIS")
    print("=" * 50)

    total_blocks = 0
    categories = []

    for category, blocks in building_blocks.items():
        if isinstance(blocks, list):
            count = len(blocks)
            total_blocks += count
            categories.append(category)

            print(f"\n📂 {category.upper().replace('_', ' ')}: {count} blocks")

            # Show first few examples
            if blocks:
                examples = blocks[:5]  # Show first 5 examples
                for example in examples:
                    print(f"   • {example}")
                if len(blocks) > 5:
                    print(f"   ... and {len(blocks) - 5} more")

        elif isinstance(blocks, dict):
            print(f"\n📂 {category.upper().replace('_', ' ')}: {blocks}")

    print(f"\n📊 SUMMARY:")
    print(f"   Total Categories: {len(categories)}")
    print(f"   Total Building Blocks: {total_blocks}")

    return {
        'total_blocks': total_blocks,
        'categories': categories,
        'building_blocks': building_blocks
    }

def search_building_blocks_by_category(building_blocks: Dict[str, Any], category: str) -> List[str]:
    """Search for building blocks in a specific category"""

    category_key = category.lower().replace(' ', '_')

    if category_key in building_blocks:
        blocks = building_blocks[category_key]
        if isinstance(blocks, list):
            return blocks

    # Try partial matching
    for key, blocks in building_blocks.items():
        if category.lower() in key.lower() and isinstance(blocks, list):
            return blocks

    return []

def query_dedicated_building_blocks_collection() -> Dict[str, Any]:
    """Query the dedicated building blocks collection"""

    print("🧱 QUERYING DEDICATED BUILDING BLOCKS COLLECTION")
    print("=" * 50)

    try:
        from Modules.building_blocks_manager import BuildingBlocksManager

        # Initialize building blocks manager
        blocks_manager = BuildingBlocksManager()

        # Get collection statistics
        stats = blocks_manager.get_statistics()

        print(f"\n📊 COLLECTION STATISTICS:")
        print(f"   Total Building Blocks: {stats['total_blocks']:,}")
        print(f"   Total Categories: {stats['total_categories']}")
        print(f"   Collection: {stats['collection_name']}")

        # Show categories
        print(f"\n📂 CATEGORIES:")
        for category in stats['categories']:
            novels = len(category['novels'])
            print(f"   • {category['_id']}: {category['count']} blocks from {novels} novel(s)")

        # Show novels
        print(f"\n📚 NOVELS:")
        for novel in stats['novels']:
            categories = len(novel['categories'])
            print(f"   • {novel['_id']} by {novel['author']}: {novel['blocks']} blocks across {categories} categories")

        # Show some example blocks
        print(f"\n🎲 EXAMPLE BLOCKS:")

        # Get random blocks from different categories
        example_categories = ['physical_descriptors', 'emotional_words', 'colors', 'action_verbs']

        for category in example_categories:
            try:
                random_blocks = blocks_manager.get_random_blocks(category, count=5)
                if random_blocks:
                    print(f"\n   {category.upper().replace('_', ' ')}:")
                    for block in random_blocks:
                        print(f"     • {block}")
            except Exception as e:
                print(f"   ⚠️ Could not get examples for {category}: {e}")

        return stats

    except Exception as e:
        print(f"❌ Error querying building blocks collection: {e}")
        return {}

def main():
    """Main function to demonstrate building blocks querying"""

    print("🧱 BUILDING BLOCKS QUERY TOOL")
    print("=" * 40)

    # Method 1: Check dedicated building blocks collection
    print("\n🔍 METHOD 1: Checking dedicated building blocks collection...")

    result = query_dedicated_building_blocks_collection()
    building_blocks_found = bool(result.get('total_blocks', 0) > 0)

    # Method 2: Check latest extraction results (fallback)
    if not building_blocks_found:
        print("\n🔍 METHOD 2: Checking latest extraction results...")

        # Look for output.json files
        json_files = [
            "archive/output.json",
            "output.json",
            "results.json"
        ]

        for json_file in json_files:
            if os.path.exists(json_file):
                result = query_building_blocks_from_json(json_file)
                if result:
                    building_blocks_found = True
                    break

    # Method 3: Check MongoDB novel collections (fallback)
    if not building_blocks_found:
        print("\n🔍 METHOD 3: Checking MongoDB novel collections...")
        result = query_building_blocks_from_mongodb()
        if result:
            building_blocks_found = True

    if not building_blocks_found:
        print("\n❌ No building blocks found!")
        print("\n💡 TO GENERATE BUILDING BLOCKS:")
        print("   1. Upload a novel PDF to the UI")
        print("   2. Select 'Novel' content type")
        print("   3. Run extraction with character identification enabled")
        print("   4. The building blocks will be automatically stored in the dedicated collection")
        print("   5. Use this tool to query them!")

    return building_blocks_found

if __name__ == "__main__":
    main()
