#!/usr/bin/env python3
"""
Test script to demonstrate metadata override functionality
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from Modules.mongodb_manager import MongoDBManager

def test_metadata_override():
    """Test metadata override functionality with sample data"""
    
    print("🔧 Testing Metadata Override Functionality")
    print("=" * 50)
    
    # Original AI-detected metadata (potentially incorrect)
    original_metadata = {
        "game_type": "D&D",  # AI detected this
        "edition": "1st Edition",  # AI detected this
        "book_type": "Core Rules",  # AI detected this - WRONG!
        "book_full_name": "Advanced Dungeons & Dragons - Dungeon Masters Guide",
        "collection_name": "dmg"
    }
    
    # User corrections (what the user knows is correct)
    user_corrections = {
        "book_type": "Supplement",  # User corrects: it's actually a supplement
        "book_full_name": "Advanced Dungeons & Dragons - Unearthed Arcana",  # User corrects title
        "collection_name": "unearthed_arcana"  # User corrects collection name
    }
    
    print("📊 Original AI Detection:")
    print(f"  Game Type: {original_metadata['game_type']}")
    print(f"  Edition: {original_metadata['edition']}")
    print(f"  Book Type: {original_metadata['book_type']} ❌ (INCORRECT)")
    print(f"  Book Title: {original_metadata['book_full_name']} ❌ (INCORRECT)")
    print(f"  Collection: {original_metadata['collection_name']} ❌ (INCORRECT)")
    
    # Apply user corrections
    corrected_metadata = original_metadata.copy()
    corrected_metadata.update(user_corrections)
    
    print("\n✏️  User Corrections:")
    print(f"  Book Type: {original_metadata['book_type']} → {user_corrections['book_type']}")
    print(f"  Book Title: {original_metadata['book_full_name']} → {user_corrections['book_full_name']}")
    print(f"  Collection: {original_metadata['collection_name']} → {user_corrections['collection_name']}")
    
    print("\n✅ Final Corrected Metadata:")
    print(f"  Game Type: {corrected_metadata['game_type']}")
    print(f"  Edition: {corrected_metadata['edition']}")
    print(f"  Book Type: {corrected_metadata['book_type']} ✅")
    print(f"  Book Title: {corrected_metadata['book_full_name']} ✅")
    print(f"  Collection: {corrected_metadata['collection_name']} ✅")
    
    # Generate collection paths
    def generate_collection_path(metadata):
        game_type = metadata.get('game_type', 'unknown').lower().replace(' ', '_').replace('&', 'and')
        edition = metadata.get('edition', 'unknown').lower().replace(' ', '_').replace('&', 'and')
        book_type = metadata.get('book_type', 'unknown').lower().replace(' ', '_').replace('&', 'and')
        collection_base = metadata.get('collection_name', 'unknown')
        return f"source_material.{game_type}.{edition}.{book_type}.{collection_base}"
    
    original_path = generate_collection_path(original_metadata)
    corrected_path = generate_collection_path(corrected_metadata)
    
    print("\n🗂️  Collection Path Comparison:")
    print(f"  Original:  rpger.{original_path}")
    print(f"  Corrected: rpger.{corrected_path}")
    
    print("\n🎯 Benefits of Metadata Override:")
    print("  • Corrects AI misidentification")
    print("  • Ensures proper hierarchical organization")
    print("  • Prevents data from being stored in wrong collections")
    print("  • Maintains data quality and findability")
    print("  • User has final control over metadata accuracy")
    
    # Test with MongoDB if available
    mongodb_manager = MongoDBManager(debug=True)
    
    if mongodb_manager.connected:
        print("\n🧪 Testing MongoDB Import with Corrected Metadata:")
        print("-" * 40)
        
        # Sample extraction data
        sample_extraction = {
            "game_metadata": corrected_metadata,
            "sections": [
                {
                    "title": "New Spells",
                    "content": "This supplement introduces new spells for magic-users...",
                    "page": 1,
                    "category": "Spells"
                }
            ],
            "summary": {"total_pages": 1, "total_words": 50},
            "source_file": "unearthed_arcana.pdf"
        }
        
        # Test import with corrected metadata
        success, message = mongodb_manager.import_extracted_content(
            sample_extraction, 
            corrected_path, 
            split_sections=False
        )
        
        if success:
            print(f"✅ Import successful: {message}")
            print(f"📍 Stored in: rpger.{corrected_path}")
        else:
            print(f"❌ Import failed: {message}")
    else:
        print("\n⚠️  MongoDB not connected - skipping import test")
    
    print("\n🚀 How to Use in Web UI:")
    print("1. Upload and analyze PDF")
    print("2. Review AI-detected metadata in the blue info box")
    print("3. Click 'Edit Metadata' if corrections needed")
    print("4. Modify any incorrect fields")
    print("5. Watch the 'Generated Path' update in real-time")
    print("6. Click 'Save Changes' to apply corrections")
    print("7. Import to database with corrected metadata")

if __name__ == "__main__":
    test_metadata_override()
