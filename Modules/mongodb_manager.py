#!/usr/bin/env python3
"""
MongoDB Manager Module
MongoDB connection and collection management for AI-Powered Extraction v3
"""

import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

# Try to import dotenv for loading environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load environment variables from .env file if it exists
    load_dotenv()
except ImportError:
    # If dotenv is not installed, continue without it
    pass

# Try to import pymongo
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    MongoClient = None
    ConnectionFailure = Exception
    ServerSelectionTimeoutError = Exception

# MongoDB Configuration - using environment variables with fallbacks
MONGODB_HOST = os.getenv("MONGODB_HOST", "10.202.28.46")
MONGODB_PORT = int(os.getenv("MONGODB_PORT", "27017"))
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "rpger")
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")

# Build connection string if not provided
if not MONGODB_CONNECTION_STRING:
    if MONGODB_USERNAME and MONGODB_PASSWORD:
        MONGODB_CONNECTION_STRING = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}"
    else:
        MONGODB_CONNECTION_STRING = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}"

MONGODB_CONFIG = {
    "host": MONGODB_HOST,
    "port": MONGODB_PORT,
    "database": MONGODB_DATABASE,
    "username": MONGODB_USERNAME,
    "password": MONGODB_PASSWORD,
    "connection_string": MONGODB_CONNECTION_STRING
}

class MongoDBManager:
    """MongoDB connection and collection management"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.client = None
        self.database = None
        self.connected = False

        if not PYMONGO_AVAILABLE:
            if self.debug:
                print("⚠️  PyMongo not available. Install with: pip install pymongo>=4.6.0")
            return

        self._connect()

    def _connect(self) -> bool:
        """Establish connection to MongoDB"""
        try:
            if self.debug:
                print(f"🔌 Connecting to MongoDB: {MONGODB_HOST}:{MONGODB_PORT}")

            # Create client with timeout
            self.client = MongoClient(
                MONGODB_CONNECTION_STRING,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )

            # Test connection
            self.client.admin.command('ping')

            # Get database
            self.database = self.client[MONGODB_DATABASE]
            self.connected = True

            if self.debug:
                print(f"✅ Connected to MongoDB database: {MONGODB_DATABASE}")

            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            if self.debug:
                print(f"❌ MongoDB connection failed: {e}")
            self.connected = False
            return False
        except Exception as e:
            if self.debug:
                print(f"❌ MongoDB connection error: {e}")
            self.connected = False
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get MongoDB connection status and database info"""
        if not PYMONGO_AVAILABLE:
            return {
                "status": "PyMongo not installed",
                "connected": False,
                "error": "Install pymongo>=4.6.0"
            }

        if not self.connected:
            return {
                "status": "Disconnected",
                "connected": False,
                "host": MONGODB_HOST,
                "port": MONGODB_PORT,
                "database": MONGODB_DATABASE
            }

        try:
            # Get server info
            server_info = self.client.server_info()

            # Get database stats
            db_stats = self.database.command("dbStats")

            # Get collection names
            collections = self.database.list_collection_names()

            return {
                "status": "Connected",
                "connected": True,
                "host": MONGODB_HOST,
                "port": MONGODB_PORT,
                "database": MONGODB_DATABASE,
                "server_version": server_info.get("version", "Unknown"),
                "collections": len(collections),
                "collection_names": collections[:10],  # First 10 collections
                "database_size": db_stats.get("dataSize", 0),
                "storage_size": db_stats.get("storageSize", 0)
            }

        except Exception as e:
            return {
                "status": f"Error: {str(e)}",
                "connected": False,
                "host": MONGODB_HOST,
                "port": MONGODB_PORT,
                "database": MONGODB_DATABASE
            }

    def test_connection(self) -> Tuple[bool, str]:
        """Test MongoDB connection and return status"""
        if not PYMONGO_AVAILABLE:
            return False, "PyMongo not installed"

        try:
            if not self.connected:
                self._connect()

            if self.connected:
                # Test with a simple ping
                self.client.admin.command('ping')
                return True, "Connected"
            else:
                return False, "Connection failed"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific collection"""
        if not self.connected:
            return None

        try:
            collection = self.database[collection_name]

            # Get collection stats
            stats = self.database.command("collStats", collection_name)

            # Get document count
            doc_count = collection.count_documents({})

            # Get sample document
            sample_doc = collection.find_one()

            return {
                "name": collection_name,
                "document_count": doc_count,
                "size": stats.get("size", 0),
                "storage_size": stats.get("storageSize", 0),
                "indexes": stats.get("nindexes", 0),
                "sample_document": sample_doc is not None,
                "sample_fields": list(sample_doc.keys()) if sample_doc else []
            }

        except Exception as e:
            if self.debug:
                print(f"❌ Error getting collection info for {collection_name}: {e}")
            return None

    def import_extracted_content(self, extraction_data: Dict[str, Any],
                               collection_name: str = "extracted_content",
                               split_sections: bool = False) -> Tuple[bool, str]:
        """Import extracted PDF content to MongoDB

        Args:
            extraction_data: The extracted content data
            collection_name: Target MongoDB collection
            split_sections: If True, create separate documents for each section (v1/v2 style)
                          If False, create single document with sections array (v3 style, default)
        """
        if not self.connected:
            return False, "Not connected to MongoDB"

        try:
            collection = self.database[collection_name]
            game_metadata = extraction_data.get("game_metadata", {})
            sections = extraction_data.get("sections", [])

            if split_sections and sections:
                # v1/v2 style: Create separate document for each section
                inserted_ids = []

                for i, section in enumerate(sections):
                    # Create individual document for each section
                    section_doc = {
                        "_id": f"{game_metadata.get('collection_name', 'unknown')}_page_{section.get('page', i)}_{i}",
                        "source": game_metadata.get('book_full_name', 'Unknown'),
                        "title": section.get('title', f"Section {i+1}"),
                        "content": section.get('content', ''),
                        "page": section.get('page', i+1),
                        "category": section.get('category', 'General'),
                        "tags": self._extract_tags(section.get('content', '')),
                        "word_count": len(section.get('content', '').split()) if section.get('content') else 0,
                        "has_tables": section.get('has_tables', False),
                        "table_count": section.get('table_count', 0),
                        "is_multi_column": section.get('is_multi_column', False),
                        "extraction_confidence": section.get('extraction_confidence', 0),
                        "metadata": {
                            "extraction_method": "ai_powered_v3_split",
                            "game_type": game_metadata.get('game_type', 'Unknown'),
                            "edition": game_metadata.get('edition', 'Unknown'),
                            "book_type": game_metadata.get('book_type', 'Unknown'),
                            "source_file": extraction_data.get("source_file", ""),
                            "section_index": i,
                            "total_sections": len(sections)
                        },
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "import_date": datetime.now(timezone.utc)
                    }

                    try:
                        result = collection.insert_one(section_doc)
                        inserted_ids.append(str(result.inserted_id))
                    except Exception as e:
                        if self.debug:
                            print(f"⚠️  Failed to insert section {i}: {e}")
                        continue

                if self.debug:
                    print(f"✅ Imported {len(inserted_ids)} sections to MongoDB collection '{collection_name}'")

                return True, f"Imported {len(inserted_ids)} sections"

            else:
                # v3 style: Single document with sections array (default)
                document = {
                    "import_date": datetime.now(timezone.utc),
                    "game_metadata": game_metadata,
                    "sections": sections,
                    "summary": extraction_data.get("summary", {}),
                    "source_file": extraction_data.get("source_file", ""),
                    "extraction_method": "ai_powered_v3"
                }

                # Insert document
                result = collection.insert_one(document)

                if self.debug:
                    print(f"✅ Imported to MongoDB collection '{collection_name}': {result.inserted_id}")

                return True, f"Imported with ID: {result.inserted_id}"

        except Exception as e:
            error_msg = f"MongoDB import error: {str(e)}"
            if self.debug:
                print(f"❌ {error_msg}")
            return False, error_msg

    def _extract_tags(self, content: str) -> List[str]:
        """Extract simple tags from content for v1/v2 compatibility"""
        if not content:
            return []

        # Simple tag extraction - look for common RPG terms
        common_terms = [
            'spell', 'magic', 'weapon', 'armor', 'monster', 'creature',
            'class', 'race', 'skill', 'feat', 'ability', 'combat',
            'dungeon', 'treasure', 'item', 'equipment', 'character'
        ]

        content_lower = content.lower()
        found_tags = []

        for term in common_terms:
            if term in content_lower:
                found_tags.append(term.title())

        # Limit to 5 tags maximum
        return found_tags[:5]

    def query_by_game_edition(self, game_type: str, edition: str = None, book_type: str = None) -> List[Dict[str, Any]]:
        """Query content across all collections for a specific game/edition

        Args:
            game_type: Game system (e.g., 'D&D', 'Pathfinder')
            edition: Edition (e.g., '1st Edition', '5th Edition') - optional
            book_type: Book type (e.g., 'Core Rules', 'Supplement') - optional

        Returns:
            List of documents matching the criteria
        """
        if not self.connected:
            if self.debug:
                print("❌ Not connected to MongoDB")
            return []

        try:
            # Normalize game type for collection name matching
            game_normalized = game_type.lower().replace(' ', '_').replace('&', 'and')

            # Build collection name pattern
            pattern_parts = ['source_material', game_normalized]
            if edition:
                edition_normalized = edition.lower().replace(' ', '_').replace('&', 'and')
                pattern_parts.append(edition_normalized)

            pattern = '.'.join(pattern_parts)

            # Find matching collections
            all_collections = self.database.list_collection_names()
            matching_collections = [col for col in all_collections if col.startswith(pattern)]

            if self.debug:
                print(f"🔍 Found {len(matching_collections)} collections matching pattern: {pattern}")
                for col in matching_collections:
                    print(f"   • {col}")

            # Query each matching collection
            results = []
            for collection_name in matching_collections:
                collection = self.database[collection_name]

                # Build query filter
                query_filter = {}
                if book_type:
                    # Try to match book type in collection name or metadata
                    book_type_normalized = book_type.lower().replace(' ', '_').replace('&', 'and')
                    if book_type_normalized not in collection_name:
                        # Skip this collection if book type doesn't match
                        continue

                # Get documents from this collection
                docs = list(collection.find(query_filter))

                # Add collection info to each document
                for doc in docs:
                    doc['_source_collection'] = collection_name
                    doc['_collection_parts'] = self._parse_collection_name(collection_name)

                results.extend(docs)

                if self.debug:
                    print(f"   📄 {collection_name}: {len(docs)} documents")

            if self.debug:
                print(f"✅ Total results: {len(results)} documents")

            return results

        except Exception as e:
            if self.debug:
                print(f"❌ Query error: {e}")
            return []

    def _parse_collection_name(self, collection_name: str) -> Dict[str, str]:
        """Parse hierarchical collection name into components"""
        parts = collection_name.split('.')
        if len(parts) >= 5 and parts[0] == 'source_material':
            return {
                'game_type': parts[1].replace('_', ' ').replace('and', '&').title(),
                'edition': parts[2].replace('_', ' ').title(),
                'book_type': parts[3].replace('_', ' ').title(),
                'collection_name': parts[4]
            }
        return {}

    def chromadb_to_mongodb_format(self, chroma_doc: Dict[str, Any],
                                 collection_name: str) -> Dict[str, Any]:
        """Convert ChromaDB document to MongoDB format"""
        try:
            # Extract metadata
            metadata = chroma_doc.get('metadata', {})
            content = chroma_doc.get('document', '')
            doc_id = chroma_doc.get('id', '')

            # Create MongoDB document
            mongo_doc = {
                "_id": f"{collection_name}_{doc_id}",
                "source": metadata.get('source', 'Unknown'),
                "title": metadata.get('title', ''),
                "content": content,
                "page": metadata.get('page', 0),
                "category": metadata.get('category', 'General'),
                "tags": self._extract_tags(content),
                "word_count": len(content.split()) if content else 0,
                "metadata": {
                    "extraction_method": "chromadb_transfer",
                    "original_collection": collection_name,
                    "original_id": doc_id,
                    "transfer_date": datetime.now(timezone.utc).isoformat()
                },
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            return mongo_doc

        except Exception as e:
            if self.debug:
                print(f"❌ Error converting ChromaDB to MongoDB format: {e}")
            return {}

    def _extract_tags(self, content: str) -> List[str]:
        """Extract tags from content for MongoDB indexing"""
        if not content:
            return []

        # Simple tag extraction - can be enhanced with NLP
        common_rpg_terms = [
            'combat', 'spell', 'magic', 'weapon', 'armor', 'character',
            'monster', 'dungeon', 'treasure', 'experience', 'level',
            'class', 'race', 'ability', 'skill', 'feat', 'item'
        ]

        content_lower = content.lower()
        found_tags = []

        for term in common_rpg_terms:
            if term in content_lower:
                found_tags.append(term)

        return found_tags[:10]  # Limit to 10 tags

    def upload_chromadb_results(self, chroma_results: List[Dict[str, Any]],
                              mongo_collection: str,
                              source_collection: str = "unknown") -> Tuple[bool, str]:
        """Upload ChromaDB search results to MongoDB collection"""
        if not self.connected:
            return False, "Not connected to MongoDB"

        try:
            collection = self.database[mongo_collection]

            # Convert ChromaDB results to MongoDB format
            mongo_docs = []
            for result in chroma_results:
                mongo_doc = self.chromadb_to_mongodb_format(result, source_collection)
                if mongo_doc:
                    mongo_docs.append(mongo_doc)

            if not mongo_docs:
                return False, "No valid documents to upload"

            # Insert documents
            result = collection.insert_many(mongo_docs, ordered=False)

            if self.debug:
                print(f"✅ Uploaded {len(result.inserted_ids)} documents to MongoDB collection '{mongo_collection}'")

            return True, f"Uploaded {len(result.inserted_ids)} documents"

        except Exception as e:
            error_msg = f"MongoDB upload error: {str(e)}"
            if self.debug:
                print(f"❌ {error_msg}")
            return False, error_msg

    def check_deletion_safety(self, collection_name: str) -> Dict[str, Any]:
        """Check if collection is safe to delete"""
        if not self.connected:
            return {'safe_to_delete': False, 'reason': 'Database not connected'}

        # Define protected collections
        protected_collections = [
            'system.config',
            'system.users',
            'system.audit_log'
        ]

        if collection_name in protected_collections:
            return {
                'safe_to_delete': False,
                'reason': 'System collection cannot be deleted'
            }

        # Check if collection was created recently (within 24 hours)
        collection = self.database[collection_name]
        try:
            stats = self.database.command('collStats', collection_name)
            created_date = stats.get('createdDate')
            if created_date:
                hours_since_creation = (datetime.now(timezone.utc) - created_date).total_seconds() / 3600
                if hours_since_creation < 24:
                    return {
                        'safe_to_delete': False,
                        'reason': f'Collection created {hours_since_creation:.1f} hours ago. Wait 24 hours before deletion.'
                    }
        except:
            pass  # If we can't get creation date, allow deletion

        # Check collection size (warn for large collections)
        document_count = collection.count_documents({})
        if document_count > 10000:
            return {
                'safe_to_delete': True,
                'reason': f'Large collection ({document_count:,} documents). Backup strongly recommended.',
                'warning': True
            }

        return {'safe_to_delete': True, 'reason': 'Collection is safe to delete'}

    def create_collection_backup(self, collection_name: str) -> Dict[str, Any]:
        """Create a backup of the collection before deletion"""
        if not self.connected:
            return {'success': False, 'error': 'Database not connected'}

        try:
            from pathlib import Path
            import json

            # Create backup directory
            backup_dir = Path('backups') / 'collections'
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Generate backup filename with timestamp
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            backup_filename = f'{collection_name}_{timestamp}.json'
            backup_path = backup_dir / backup_filename

            # Export collection data
            collection = self.database[collection_name]
            documents = list(collection.find({}))

            # Convert ObjectId to string for JSON serialization
            for doc in documents:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])

            # Create backup metadata
            backup_data = {
                'backup_info': {
                    'collection_name': collection_name,
                    'backup_date': datetime.now(timezone.utc).isoformat() + 'Z',
                    'document_count': len(documents),
                    'backup_version': '1.0'
                },
                'documents': documents
            }

            # Write backup file
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            return {
                'success': True,
                'backup_path': str(backup_path),
                'document_count': len(documents),
                'backup_size': backup_path.stat().st_size
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Backup creation failed: {str(e)}'
            }

    def delete_collection_safe(self, collection_name: str) -> Dict[str, Any]:
        """Safely delete a collection with logging"""
        if not self.connected:
            return {'success': False, 'error': 'Database not connected'}

        try:
            # Get final collection stats before deletion
            collection = self.database[collection_name]
            final_count = collection.count_documents({})

            # Perform deletion
            collection.drop()

            return {
                'success': True,
                'documents_deleted': final_count,
                'deletion_time': datetime.now(timezone.utc).isoformat() + 'Z'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Collection deletion failed: {str(e)}'
            }

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.connected = False
            if self.debug:
                print("🔌 MongoDB connection closed")

    def __del__(self):
        """Cleanup on object destruction"""
        self.close()

# Convenience function for quick status check
def check_mongodb_status() -> Dict[str, Any]:
    """Quick MongoDB status check without creating persistent connection"""
    manager = MongoDBManager(debug=False)
    status = manager.get_status()
    manager.close()
    return status

# Convenience function for quick connection test
def test_mongodb_connection() -> Tuple[bool, str]:
    """Quick MongoDB connection test"""
    manager = MongoDBManager(debug=False)
    result = manager.test_connection()
    manager.close()
    return result
