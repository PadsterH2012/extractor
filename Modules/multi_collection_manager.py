#!/usr/bin/env python3
"""
Multi-Game Collection Manager Module
Enhanced ChromaDB collection management with game-aware organization
"""

import json
import requests
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Note: No longer dependent on static game configs - uses AI detection

# ChromaDB Configuration - using your working setup
CHROMA_CONFIG = {
    "host": "10.202.28.49",
    "port": "8000",
    "base_url": "http://10.202.28.49:8000/api/v2",
    "tenant": "default_tenant",
    "database": "default_database"
}

class MultiGameCollectionManager:
    """Enhanced collection manager with multi-game support"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.base_url = f"{CHROMA_CONFIG['base_url']}/tenants/{CHROMA_CONFIG['tenant']}/databases/{CHROMA_CONFIG['database']}"
        self.collections = self.discover_collections()
        self.game_collections = self.organize_by_game_type()

    def parse_collection_name(self, collection_name: str) -> Dict[str, str]:
        """Parse collection name to extract game type, edition, and book"""

        # Handle legacy format (add_dmg -> D&D 1st DMG)
        if collection_name.startswith("add_"):
            book_abbrev = collection_name[4:].upper()
            return {
                "game_type": "D&D",
                "edition": "1st",
                "book": book_abbrev,
                "collection_name": collection_name,
                "is_legacy": True
            }

        # New format: gameprefix_edition_book (e.g., dnd_1st_dmg, pf_2nd_core)
        parts = collection_name.split("_")
        if len(parts) >= 3:
            prefix = parts[0]
            edition = parts[1]
            book = "_".join(parts[2:]).upper()

            # Map prefix to game type (AI-independent)
            prefix_map = {
                "dnd": "D&D",
                "pf": "Pathfinder",
                "coc": "Call of Cthulhu",
                "vtm": "Vampire",
                "wta": "Werewolf",
                "cp": "Cyberpunk",
                "sr": "Shadowrun",
                "gurps": "GURPS",
                "sw": "Savage Worlds"
            }
            game_type = prefix_map.get(prefix, "Unknown")

            if game_type:
                return {
                    "game_type": game_type,
                    "edition": edition,
                    "book": book,
                    "collection_name": collection_name,
                    "is_legacy": False
                }

        # Unknown format
        return {
            "game_type": "Unknown",
            "edition": "Unknown",
            "book": collection_name.upper(),
            "collection_name": collection_name,
            "is_legacy": False
        }

    def organize_by_game_type(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Organize collections by game type -> edition -> book"""
        organized = {}

        for collection_name in self.collections:
            parsed = self.parse_collection_name(collection_name)
            game_type = parsed["game_type"]
            edition = parsed["edition"]
            book = parsed["book"]

            if game_type not in organized:
                organized[game_type] = {}
            if edition not in organized[game_type]:
                organized[game_type][edition] = {}

            organized[game_type][edition][book] = collection_name

        return organized

    def discover_collections(self) -> Dict[str, str]:
        """Discover all available collections"""
        try:
            collections_url = f"{self.base_url}/collections"
            response = requests.get(collections_url)

            if response.status_code == 200:
                collections_data = response.json()
                collections = {}

                for collection in collections_data:
                    name = collection.get('name')
                    uuid = collection.get('id')
                    if name and uuid:
                        collections[name] = uuid

                if self.debug:
                    print(f"📊 Discovered {len(collections)} collections")
                return collections
            else:
                print(f"❌ Could not discover collections: {response.status_code}")
                return {}

        except Exception as e:
            print(f"❌ Collection discovery failed: {e}")
            return {}

    def filter_collections_by_criteria(self, game_type: Optional[str] = None,
                                     edition: Optional[str] = None,
                                     book: Optional[str] = None) -> List[str]:
        """Filter collections by game criteria"""
        filtered = []

        for collection_name in self.collections:
            parsed = self.parse_collection_name(collection_name)

            # Apply filters
            if game_type and parsed["game_type"] != game_type:
                continue
            if edition and parsed["edition"] != edition:
                continue
            if book and parsed["book"] != book.upper():
                continue

            filtered.append(collection_name)

        return filtered

    def get_collection_info(self, collection_name: str) -> Optional[Dict]:
        """Get detailed info about a collection with game metadata"""
        if collection_name not in self.collections:
            return None

        collection_uuid = self.collections[collection_name]
        parsed = self.parse_collection_name(collection_name)

        try:
            # Get collection details
            collection_url = f"{self.base_url}/collections/{collection_uuid}"
            response = requests.get(collection_url)

            info = {
                "name": collection_name,
                "uuid": collection_uuid,
                "status": "unknown",
                "document_count": 0,
                "metadata": {},
                "game_info": parsed
            }

            if response.status_code == 200:
                collection_data = response.json()
                info["metadata"] = collection_data.get("metadata", {})
                info["status"] = "active"

            # Get document count
            count_url = f"{self.base_url}/collections/{collection_uuid}/count"
            count_response = requests.get(count_url)

            if count_response.status_code == 200:
                try:
                    info["document_count"] = int(count_response.text)
                except:
                    info["document_count"] = count_response.text

            return info

        except Exception as e:
            if self.debug:
                print(f"❌ Error getting collection info: {e}")
            return None

    def show_status(self, game_type: Optional[str] = None) -> Dict[str, int]:
        """Show status of collections organized by game type"""
        print("📊 Multi-Game ChromaDB Collection Status")
        print("=" * 60)

        if game_type:
            print(f"🎮 Filtering by game type: {game_type}")
            print()

        total_docs = 0
        active_collections = 0

        # Group collections by game type
        for gt in sorted(self.game_collections.keys()):
            if game_type and gt != game_type:
                continue

            print(f"🎮 {gt}")
            print("-" * 40)

            game_docs = 0
            game_collections = 0

            for edition in sorted(self.game_collections[gt].keys()):
                edition_collections = []
                for book in sorted(self.game_collections[gt][edition].keys()):
                    collection_name = self.game_collections[gt][edition][book]
                    info = self.get_collection_info(collection_name)

                    if info:
                        status_icon = "✅" if info["status"] == "active" else "❌"
                        doc_count = info["document_count"]

                        edition_collections.append({
                            "book": book,
                            "collection": collection_name,
                            "status": status_icon,
                            "docs": doc_count,
                            "uuid": info["uuid"][:8]
                        })

                        if isinstance(doc_count, int):
                            game_docs += doc_count
                            game_collections += 1

                if edition_collections:
                    print(f"  📖 {edition} Edition:")
                    for coll in edition_collections:
                        print(f"    {coll['status']} {coll['book']}: {coll['docs']} docs ({coll['uuid']}...)")

            print(f"  📈 {gt} Total: {game_collections} collections, {game_docs:,} documents")
            print()

            total_docs += game_docs
            active_collections += game_collections

        print(f"🌟 Grand Total: {active_collections} active collections, {total_docs:,} total documents")

        return {
            "total_collections": active_collections,
            "total_documents": total_docs
        }

    def search_collection(self, collection_name: str, query: str, n_results: int = 5) -> List[Dict]:
        """Search a specific collection - enhanced with game metadata"""
        if collection_name not in self.collections:
            print(f"❌ Collection '{collection_name}' not found")
            return []

        collection_uuid = self.collections[collection_name]
        query_url = f"{self.base_url}/collections/{collection_uuid}/query"

        try:
            payload = {
                "query_texts": [query],
                "n_results": n_results
            }

            response = requests.post(query_url, json=payload)

            if response.status_code == 200:
                results = response.json()
                documents = results.get('documents', [[]])
                metadatas = results.get('metadatas', [[]])
                distances = results.get('distances', [[]])

                search_results = []
                for doc, metadata, distance in zip(documents[0], metadatas[0], distances[0]):
                    # Add game metadata to results
                    enhanced_metadata = metadata.copy()
                    game_info = self.parse_collection_name(collection_name)
                    enhanced_metadata.update({
                        "game_type": game_info["game_type"],
                        "edition": game_info["edition"],
                        "book": game_info["book"]
                    })

                    search_results.append({
                        "content": doc,
                        "metadata": enhanced_metadata,
                        "distance": distance,
                        "collection": collection_name
                    })

                return search_results
            else:
                # If semantic search fails, fall back to browsing + filtering
                if self.debug:
                    print(f"⚠️  Semantic search failed for {collection_name}, using text filtering...")
                return self.text_filter_collection(collection_name, query, n_results)

        except Exception as e:
            if self.debug:
                print(f"⚠️  Search error for {collection_name}: {e}")
            return self.text_filter_collection(collection_name, query, n_results)

    def text_filter_collection(self, collection_name: str, query: str, limit: int = 5) -> List[Dict]:
        """Fallback: browse collection and filter by text match"""
        docs = self.browse_collection(collection_name, limit * 3)  # Get more to filter

        query_lower = query.lower()
        matches = []

        for doc in docs:
            content = doc["content"].lower()
            if query_lower in content:
                matches.append(doc)
                if len(matches) >= limit:
                    break

        return matches

    def browse_collection(self, collection_name: str, limit: int = 10) -> List[Dict]:
        """Browse documents in a specific collection"""
        if collection_name not in self.collections:
            print(f"❌ Collection '{collection_name}' not found")
            return []

        collection_uuid = self.collections[collection_name]

        try:
            # Use your working GET method
            get_url = f"{self.base_url}/collections/{collection_uuid}/get"
            payload = {
                "include": ["documents", "metadatas"],
                "limit": limit
            }

            response = requests.post(get_url, json=payload)

            if response.status_code == 200:
                results = response.json()
                documents = results.get('documents', [])
                metadatas = results.get('metadatas', [])

                found_docs = []
                for doc, metadata in zip(documents, metadatas):
                    if doc:
                        # Add game metadata
                        enhanced_metadata = metadata.copy()
                        game_info = self.parse_collection_name(collection_name)
                        enhanced_metadata.update({
                            "game_type": game_info["game_type"],
                            "edition": game_info["edition"],
                            "book": game_info["book"]
                        })

                        found_docs.append({
                            "content": doc,
                            "metadata": enhanced_metadata,
                            "collection": collection_name
                        })

                return found_docs
            else:
                print(f"❌ Browse failed: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ Browse error: {e}")
            return []

    def search_with_game_filter(self, query: str, game_type: Optional[str] = None,
                               edition: Optional[str] = None, book: Optional[str] = None,
                               n_results: int = 3) -> Dict[str, List[Dict]]:
        """Search collections with game-aware filtering"""
        filtered_collections = self.filter_collections_by_criteria(game_type, edition, book)

        if not filtered_collections:
            print(f"❌ No collections found matching criteria")
            return {}

        print(f"🔍 Searching {len(filtered_collections)} collections...")
        if game_type:
            print(f"   🎮 Game: {game_type}")
        if edition:
            print(f"   📖 Edition: {edition}")
        if book:
            print(f"   📚 Book: {book}")
        print()

        all_results = {}

        for collection_name in filtered_collections:
            if self.debug:
                print(f"🔍 Searching {collection_name}...")
            results = self.search_collection(collection_name, query, n_results)
            if results:
                all_results[collection_name] = results

        return all_results

    def compare_across_games(self, query: str, n_results: int = 2) -> Dict[str, Dict[str, List[Dict]]]:
        """Compare search results across different game types"""
        print(f"🔍 Cross-Game Comparison for: '{query}'")
        print("=" * 70)

        game_results = {}

        for game_type in self.game_collections.keys():
            game_collections = self.filter_collections_by_criteria(game_type=game_type)
            if game_collections:
                if self.debug:
                    print(f"🎮 Searching {game_type} collections...")
                results = {}
                for collection_name in game_collections:
                    coll_results = self.search_collection(collection_name, query, n_results)
                    if coll_results:
                        results[collection_name] = coll_results

                if results:
                    game_results[game_type] = results

        if not game_results:
            print("❌ No results found in any game system")
            return {}

        # Display results organized by game type
        for game_type, game_collections in game_results.items():
            print(f"\n🎮 {game_type.upper()}")
            print("=" * 50)

            for collection_name, results in game_collections.items():
                parsed = self.parse_collection_name(collection_name)
                print(f"\n📚 {parsed['edition']} Edition {parsed['book']} ({len(results)} results):")
                print("-" * 30)

                for i, result in enumerate(results):
                    metadata = result["metadata"]
                    title = metadata.get("title", "Unknown")
                    page = metadata.get("page", "?")

                    print(f"  {i+1}. {title} (Page {page})")

                    # Show content preview
                    content = result["content"]
                    query_pos = content.lower().find(query.lower())
                    if query_pos != -1:
                        start = max(0, query_pos - 40)
                        end = min(len(content), query_pos + len(query) + 40)
                        context = content[start:end]
                        print(f"     📝 ...{context}...")
                    else:
                        preview = content[:80] + "..." if len(content) > 80 else content
                        print(f"     📝 {preview}")

                    if "distance" in result:
                        print(f"     📊 Relevance: {1-result['distance']:.2f}")

        return game_results

    def add_documents_to_collection(self, collection_name: str, documents: List[str],
                                   metadatas: List[Dict], ids: List[str]) -> bool:
        """Add documents to a ChromaDB collection"""
        try:
            # Create or get collection
            collection_uuid = self._create_or_get_collection(collection_name)
            if not collection_uuid:
                return False

            # Add documents
            add_url = f"{self.base_url}/collections/{collection_uuid}/add"
            payload = {
                "documents": documents,
                "metadatas": metadatas,
                "ids": ids
            }

            response = requests.post(add_url, json=payload)

            if response.status_code == 200:
                if self.debug:
                    print(f"✅ Added {len(documents)} documents to {collection_name}")
                return True
            else:
                print(f"❌ Failed to add documents: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error adding documents: {e}")
            return False

    def import_to_chromadb(self, json_file: Path, collection_name: Optional[str] = None) -> bool:
        """Import JSON data to ChromaDB collection"""

        if not json_file.exists():
            print(f"❌ JSON file not found: {json_file}")
            return False

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Determine collection name
            if collection_name:
                target_collection = collection_name
            elif isinstance(data, list) and len(data) > 0:
                # Try to get collection name from first document metadata
                first_doc = data[0]
                if isinstance(first_doc, dict) and "metadata" in first_doc:
                    target_collection = first_doc["metadata"].get("collection_name")
                else:
                    target_collection = json_file.stem
            else:
                target_collection = json_file.stem

            if not target_collection:
                print("❌ Could not determine collection name")
                return False

            print(f"📥 Importing to collection: {target_collection}")

            # Create or get collection
            collection_uuid = self._create_or_get_collection(target_collection)
            if not collection_uuid:
                return False

            # Prepare documents for import
            if isinstance(data, list):
                documents = data
            else:
                documents = [data]

            # Import documents
            success_count = 0
            for doc in documents:
                if self._import_document(collection_uuid, doc):
                    success_count += 1

            print(f"✅ Imported {success_count}/{len(documents)} documents")
            return success_count > 0

        except Exception as e:
            print(f"❌ Import failed: {e}")
            return False

    def _create_or_get_collection(self, collection_name: str) -> Optional[str]:
        """Create or get existing collection UUID"""

        # Check if collection already exists
        if collection_name in self.collections:
            return self.collections[collection_name]

        # Create new collection
        try:
            create_url = f"{self.base_url}/collections"
            payload = {
                "name": collection_name,
                "metadata": {
                    "created_by": "extraction_v3",
                    "created_at": str(datetime.now())
                }
            }

            response = requests.post(create_url, json=payload)

            if response.status_code == 200:
                collection_data = response.json()
                collection_uuid = collection_data.get("id")

                # Update local collections cache
                self.collections[collection_name] = collection_uuid
                self.game_collections = self.organize_by_game_type()

                print(f"✅ Created collection: {collection_name}")
                return collection_uuid
            else:
                print(f"❌ Failed to create collection: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Collection creation failed: {e}")
            return None

    def _import_document(self, collection_uuid: str, document: Dict) -> bool:
        """Import a single document to collection"""

        try:
            add_url = f"{self.base_url}/collections/{collection_uuid}/add"

            # Prepare document for ChromaDB
            if "id" in document and "document" in document:
                # Already in ChromaDB format
                payload = {
                    "ids": [document["id"]],
                    "documents": [document["document"]],
                    "metadatas": [document.get("metadata", {})]
                }
            else:
                # Convert to ChromaDB format
                doc_id = document.get("id", f"doc_{hash(str(document))}")
                content = document.get("content", str(document))
                metadata = document.get("metadata", {})

                payload = {
                    "ids": [doc_id],
                    "documents": [content],
                    "metadatas": [metadata]
                }

            response = requests.post(add_url, json=payload)
            return response.status_code == 200

        except Exception as e:
            if self.debug:
                print(f"❌ Document import failed: {e}")
            return False
