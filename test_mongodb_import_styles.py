#!/usr/bin/env python3
"""
Test script to demonstrate the difference between v1/v2 and v3 MongoDB import styles
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from Modules.mongodb_manager import MongoDBManager

def test_import_styles():
    """Test both import styles with sample data"""
    
    # Sample extraction data (similar to what AI extraction produces)
    sample_extraction = {
        "game_metadata": {
            "game_type": "D&D",
            "edition": "1st Edition",
            "book_type": "Core Rules",
            "book_full_name": "Advanced Dungeons & Dragons - Dungeon Masters Guide",
            "collection_name": "dnd_1st_dmg"
        },
        "sections": [
            {
                "title": "Combat Rules",
                "content": "Combat in D&D follows a structured turn-based system...",
                "page": 1,
                "category": "Combat",
                "has_tables": True,
                "table_count": 2,
                "is_multi_column": False,
                "extraction_confidence": 95
            },
            {
                "title": "Magic Items",
                "content": "Magic items are powerful artifacts that can aid adventurers...",
                "page": 2,
                "category": "Magic",
                "has_tables": False,
                "table_count": 0,
                "is_multi_column": True,
                "extraction_confidence": 88
            },
            {
                "title": "Monster Statistics",
                "content": "Monsters have various statistics that determine their abilities...",
                "page": 3,
                "category": "Monsters",
                "has_tables": True,
                "table_count": 1,
                "is_multi_column": False,
                "extraction_confidence": 92
            }
        ],
        "summary": {
            "total_pages": 3,
            "total_words": 150,
            "category_distribution": {
                "Combat": 1,
                "Magic": 1,
                "Monsters": 1
            }
        },
        "source_file": "test_dmg.pdf"
    }
    
    # Initialize MongoDB manager
    mongodb_manager = MongoDBManager(debug=True)
    
    if not mongodb_manager.connected:
        print("❌ MongoDB not connected. Please check your .env configuration.")
        return
    
    print("🧪 Testing MongoDB Import Styles")
    print("=" * 50)
    
    # Test 1: v3 Style (Single Document)
    print("\n📄 Testing v3 Style (Single Document)")
    print("-" * 30)
    
    success, message = mongodb_manager.import_extracted_content(
        sample_extraction, 
        "test_v3_style", 
        split_sections=False
    )
    
    if success:
        print(f"✅ v3 Import: {message}")
    else:
        print(f"❌ v3 Import failed: {message}")
    
    # Test 2: v1/v2 Style (Split Sections)
    print("\n📑 Testing v1/v2 Style (Split Sections)")
    print("-" * 30)
    
    success, message = mongodb_manager.import_extracted_content(
        sample_extraction, 
        "test_v1v2_style", 
        split_sections=True
    )
    
    if success:
        print(f"✅ v1/v2 Import: {message}")
    else:
        print(f"❌ v1/v2 Import failed: {message}")
    
    # Show collection info
    print("\n📊 Collection Information")
    print("-" * 30)
    
    v3_info = mongodb_manager.get_collection_info("test_v3_style")
    v1v2_info = mongodb_manager.get_collection_info("test_v1v2_style")
    
    if v3_info:
        print(f"v3 Style Collection: {v3_info['document_count']} documents")
    
    if v1v2_info:
        print(f"v1/v2 Style Collection: {v1v2_info['document_count']} documents")
    
    print("\n🔍 Key Differences:")
    print("• v3 Style: 1 document with sections array (modern approach)")
    print("• v1/v2 Style: 3 separate documents (legacy compatibility)")
    print("• v1/v2 Style: Individual page browsing like your original imports")
    print("• v3 Style: Better for complex queries and maintaining context")

if __name__ == "__main__":
    test_import_styles()
