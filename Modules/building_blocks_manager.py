#!/usr/bin/env python3
"""
🧱 BUILDING BLOCKS MANAGER
Manages building blocks in a separate MongoDB collection for procedural NPC generation.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, ConnectionFailure

class BuildingBlocksManager:
    """Manages building blocks in a dedicated MongoDB collection"""

    def __init__(self, mongo_host: str = "10.202.28.46", mongo_port: int = 27017,
                 database: str = "rpger", collection: str = "building_blocks"):
        self.mongo_host = mongo_host
        self.mongo_port = mongo_port
        self.database_name = database
        self.collection_name = collection
        self.logger = logging.getLogger(__name__)

        # Initialize MongoDB connection
        self.client = None
        self.db = None
        self.collection = None
        self._connect()

    def _connect(self):
        """Connect to MongoDB and set up collection"""
        try:
            self.client = MongoClient(f'mongodb://{self.mongo_host}:{self.mongo_port}/',
                                    serverSelectionTimeoutMS=5000)
            self.client.server_info()  # Test connection
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]

            # Create indexes for efficient querying
            self._create_indexes()

            self.logger.info(f"✅ Connected to MongoDB: {self.database_name}.{self.collection_name}")

        except Exception as e:
            self.logger.error(f"❌ MongoDB connection failed: {e}")
            raise

    def _create_indexes(self):
        """Create indexes for efficient querying"""
        try:
            # Index on source novel for filtering by book
            self.collection.create_index([("source.novel_title", ASCENDING)])

            # Index on category for filtering by block type
            self.collection.create_index([("category", ASCENDING)])

            # Index on block value for searching specific words
            self.collection.create_index([("block", ASCENDING)])

            # Compound index for efficient category + source queries
            self.collection.create_index([
                ("category", ASCENDING),
                ("source.novel_title", ASCENDING)
            ])

            # Index on creation date for sorting
            self.collection.create_index([("created_at", DESCENDING)])

            self.logger.info("📊 Building blocks indexes created")

        except Exception as e:
            self.logger.warning(f"⚠️ Index creation warning: {e}")

    def store_building_blocks(self, building_blocks: Dict[str, Any], source_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Store building blocks from novel extraction in the dedicated collection"""

        novel_title = source_metadata.get("book_title", "Unknown Novel")
        author = source_metadata.get("author", "Unknown Author")
        extraction_id = source_metadata.get("extraction_id", None)

        self.logger.info(f"🧱 Storing building blocks from: {novel_title}")

        stored_count = 0
        skipped_count = 0
        categories_processed = []

        timestamp = datetime.utcnow()

        for category, blocks in building_blocks.items():
            if isinstance(blocks, list) and blocks:
                categories_processed.append(category)

                for block in blocks:
                    if isinstance(block, str) and block.strip():
                        # Create document for this building block
                        block_doc = {
                            "block": block.strip().lower(),
                            "category": category,
                            "source": {
                                "novel_title": novel_title,
                                "author": author,
                                "extraction_id": extraction_id,
                                "filename": source_metadata.get("filename", ""),
                                "content_type": "novel"
                            },
                            "metadata": {
                                "original_case": block.strip(),
                                "word_length": len(block.strip()),
                                "has_spaces": " " in block.strip()
                            },
                            "created_at": timestamp,
                            "updated_at": timestamp
                        }

                        try:
                            # Use upsert to avoid duplicates
                            filter_query = {
                                "block": block.strip().lower(),
                                "category": category,
                                "source.novel_title": novel_title
                            }

                            # Create a copy without updated_at for setOnInsert
                            insert_doc = block_doc.copy()

                            update_query = {
                                "$setOnInsert": insert_doc,
                                "$set": {"updated_at": timestamp}
                            }

                            result = self.collection.update_one(
                                filter_query,
                                update_query,
                                upsert=True
                            )

                            if result.upserted_id:
                                stored_count += 1
                            else:
                                skipped_count += 1

                        except Exception as e:
                            self.logger.error(f"❌ Error storing block '{block}': {e}")

        # Store summary document
        summary_doc = {
            "_id": f"summary_{novel_title.lower().replace(' ', '_')}_{timestamp.strftime('%Y%m%d_%H%M%S')}",
            "type": "extraction_summary",
            "source": {
                "novel_title": novel_title,
                "author": author,
                "extraction_id": extraction_id,
                "filename": source_metadata.get("filename", "")
            },
            "statistics": {
                "total_blocks_stored": stored_count,
                "blocks_skipped": skipped_count,
                "categories_processed": categories_processed,
                "category_count": len(categories_processed)
            },
            "created_at": timestamp
        }

        try:
            self.collection.insert_one(summary_doc)
        except Exception as e:
            self.logger.warning(f"⚠️ Could not store summary: {e}")

        result = {
            "success": True,
            "blocks_stored": stored_count,
            "blocks_skipped": skipped_count,
            "categories": categories_processed,
            "novel_title": novel_title,
            "collection": f"{self.database_name}.{self.collection_name}"
        }

        self.logger.info(f"✅ Stored {stored_count} building blocks, skipped {skipped_count} duplicates")
        self.logger.info(f"📂 Categories: {categories_processed}")

        return result

    def get_blocks_by_category(self, category: str, limit: int = 100, novel_title: str = None) -> List[Dict[str, Any]]:
        """Get building blocks by category"""

        query = {"category": category, "type": {"$ne": "extraction_summary"}}

        if novel_title:
            query["source.novel_title"] = novel_title

        cursor = self.collection.find(query).limit(limit)
        blocks = list(cursor)

        self.logger.info(f"🔍 Found {len(blocks)} blocks in category '{category}'")
        return blocks

    def get_random_blocks(self, category: str, count: int = 10, novel_title: str = None) -> List[str]:
        """Get random building blocks for procedural generation"""

        pipeline = [
            {"$match": {"category": category, "type": {"$ne": "extraction_summary"}}}
        ]

        if novel_title:
            pipeline[0]["$match"]["source.novel_title"] = novel_title

        pipeline.extend([
            {"$sample": {"size": count}},
            {"$project": {"block": 1, "_id": 0}}
        ])

        cursor = self.collection.aggregate(pipeline)
        blocks = [doc["block"] for doc in cursor]

        self.logger.info(f"🎲 Generated {len(blocks)} random blocks from category '{category}'")
        return blocks

    def get_statistics(self) -> Dict[str, Any]:
        """Get building blocks collection statistics"""

        pipeline = [
            {"$match": {"type": {"$ne": "extraction_summary"}}},
            {"$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "novels": {"$addToSet": "$source.novel_title"}
            }},
            {"$sort": {"count": -1}}
        ]

        category_stats = list(self.collection.aggregate(pipeline))

        total_blocks = sum(stat["count"] for stat in category_stats)
        total_categories = len(category_stats)

        # Get novel statistics
        novel_pipeline = [
            {"$match": {"type": {"$ne": "extraction_summary"}}},
            {"$group": {
                "_id": "$source.novel_title",
                "blocks": {"$sum": 1},
                "categories": {"$addToSet": "$category"},
                "author": {"$first": "$source.author"}
            }},
            {"$sort": {"blocks": -1}}
        ]

        novel_stats = list(self.collection.aggregate(novel_pipeline))

        return {
            "total_blocks": total_blocks,
            "total_categories": total_categories,
            "categories": category_stats,
            "novels": novel_stats,
            "collection_name": f"{self.database_name}.{self.collection_name}"
        }

    def search_blocks(self, search_term: str, category: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Search building blocks by text"""

        query = {
            "block": {"$regex": search_term.lower(), "$options": "i"},
            "type": {"$ne": "extraction_summary"}
        }

        if category:
            query["category"] = category

        cursor = self.collection.find(query).limit(limit)
        blocks = list(cursor)

        self.logger.info(f"🔍 Found {len(blocks)} blocks matching '{search_term}'")
        return blocks
