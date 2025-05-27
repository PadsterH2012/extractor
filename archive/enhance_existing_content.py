#!/usr/bin/env python3
"""
Database Content Enhancement Tool
Retroactively enhance existing database content with text quality improvements
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import MongoDB manager
try:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from Modules.mongodb_manager import MongoDBManager
    from Modules.multi_collection_manager import MultiGameCollectionManager
    MONGODB_AVAILABLE = True
except ImportError:
    print("⚠️ MongoDB manager not available. Install with: pip install pymongo>=4.6.0")
    MONGODB_AVAILABLE = False

# Try to import nltk for better text quality enhancement
try:
    import nltk
    from nltk.tokenize import word_tokenize
    
    # Download needed NLTK data
    nltk.download('punkt', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    print("⚠️ NLTK not available. Install with: pip install nltk")
    NLTK_AVAILABLE = False


class TextQualityEnhancer:
    """Text quality analysis and enhancement tool"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        # Common words in RPG content to help identify missing spaces
        self.common_rpg_terms = [
            "FIEND", "FOLIO", "TOME", "DUNGEON", "MASTER", "DRAGON", 
            "CHARACTER", "MONSTER", "PLAYER", "SPELL", "RULEBOOK", "HANDBOOK",
            "MANUAL", "ADVENTURE", "CAMPAIGN", "WEAPON", "ARMOR", "MAGIC",
            "ITEM", "TREASURE", "CLERIC", "WIZARD", "FIGHTER", "ROGUE",
            "RANGER", "PALADIN", "DRUID", "BARD", "SORCERER", "WARLOCK",
            "BARBARIAN", "MONK"
        ]
        
        # Load dictionary if NLTK available
        self.dictionary = set()
        if NLTK_AVAILABLE:
            try:
                from nltk.corpus import words
                nltk.download('words', quiet=True)
                self.dictionary = set(w.lower() for w in words.words())
                print(f"📚 Loaded {len(self.dictionary)} dictionary words")
            except Exception as e:
                print(f"⚠️ Could not load dictionary words: {e}")
    
    def analyze_quality(self, text: str) -> Dict[str, Any]:
        """
        Analyze text quality and return metrics
        """
        if not text:
            return {"quality_score": 0, "issues": ["empty_text"], "issue_count": 1}
        
        issues = []
        issue_count = 0
        
        # Check for run-on words (words longer than 15 characters)
        long_words = [w for w in text.split() if len(w) > 15]
        if long_words:
            issues.append("run_on_words")
            issue_count += len(long_words)
        
        # Check for missing spaces between common terms
        for term in self.common_rpg_terms:
            pattern = f"([a-z]){term}"
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                issues.append("missing_spaces")
                issue_count += len(matches)
                break  # Only count this issue type once
        
        # Check for inconsistent spacing
        if "  " in text or " \n" in text or "\n " in text:
            issues.append("inconsistent_spacing")
            issue_count += text.count("  ") + text.count(" \n") + text.count("\n ")
        
        # Check for OCR artifacts (common patterns)
        ocr_artifacts = ["rn" in text and "m" not in text,  # 'rn' often mistaken for 'm'
                        "l" in text and "1" in text,       # 'l' and '1' confusion
                        "0" in text and "O" in text]       # '0' and 'O' confusion
        if any(ocr_artifacts):
            issues.append("potential_ocr_artifacts")
            issue_count += sum(1 for x in ocr_artifacts if x)
        
        # Calculate quality score (100% minus penalty for issues)
        # More serious issues have higher penalties
        base_score = 100
        penalty = min(issue_count * 5, 80)  # Cap penalty at 80 points
        quality_score = max(base_score - penalty, 0)
        
        return {
            "quality_score": quality_score,
            "issues": issues,
            "issue_count": issue_count,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def enhance_text(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Enhance text quality and return improved text with enhancement metrics
        """
        if not text:
            return text, {"changes": 0, "enhanced": False}
        
        original_text = text
        changes = 0
        
        # Fix inconsistent spacing
        # Replace multiple spaces with a single space
        text = re.sub(r' {2,}', ' ', text)
        # Fix spacing around newlines
        text = re.sub(r' \n', '\n', text)
        text = re.sub(r'\n ', '\n', text)
        
        if text != original_text:
            changes += 1
        
        # Fix common OCR artifacts
        ocr_replacements = {
            "rn": "m",       # common OCR misread
            "0": "o",        # Zero vs o
            "l": "i",        # lowercase L vs i
            "cornbat": "combat",
            "tirne": "time",
            "sarne": "same",
            "frorn": "from",
        }
        
        for wrong, correct in ocr_replacements.items():
            # Only replace if the wrong pattern is likely an error (heuristic check)
            if wrong in text and correct not in text:
                text = text.replace(wrong, correct)
                changes += 1
        
        # Fix missing spaces between common terms
        for term in self.common_rpg_terms:
            # Look for lowercase letter followed by uppercase or uppercase term
            pattern = f"([a-z])({term})"
            text = re.sub(pattern, r'\1 \2', text, flags=re.IGNORECASE)
            
            # Look for term followed by lowercase
            pattern = f"({term})([a-z])"
            text = re.sub(pattern, r'\1 \2', text, flags=re.IGNORECASE)
        
        # Fix common word run-ons in RPG texts
        common_splits = {
            "isused": "is used",
            "isthe": "is the",
            "tothe": "to the",
            "andthe": "and the",
            "forthe": "for the",
            "ofthe": "of the",
            "inthe": "in the",
            "trackof": "track of",
            "Malevolentand": "Malevolent and",
            "Benignisthe": "Benign is the"
        }
        
        for run_on, corrected in common_splits.items():
            if run_on in text:
                text = text.replace(run_on, corrected)
                changes += 1
        
        # Fix run-on words with better pattern matching
        # Common RPG word transitions that shouldn't have spaces
        excluded_pairs = ['Dungeon', 'Master', 'Rule', 'Book', 'Hand', 'Book']
        
        # Look for camelCase patterns (lowercase followed by uppercase)
        pattern = r'([a-z])([A-Z])'
        text = re.sub(pattern, lambda m: f"{m.group(1)} {m.group(2)}" 
                    if m.group(1) + m.group(2) not in excluded_pairs else m.group(0), text)
        
        # Fix run-on words if NLTK is available
        if NLTK_AVAILABLE and self.dictionary:
            # Split text into words
            words = text.split()
            enhanced_words = []
            
            for word in words:
                # Only process longer words
                if len(word) > 12:
                    # Try to find word breaks
                    better_word = self._split_run_on_word(word)
                    if better_word != word:
                        enhanced_words.append(better_word)
                        changes += 1
                        continue
                
                enhanced_words.append(word)
            
            text = ' '.join(enhanced_words)
        
        # Fix spacing for common punctuation
        text = re.sub(r'(\w)\.(\w)', r'\1. \2', text)  # Fix "word.Another" -> "word. Another"
        text = re.sub(r'(\w),(\w)', r'\1, \2', text)   # Fix "word,another" -> "word, another"
        text = re.sub(r'(\w);(\w)', r'\1; \2', text)   # Fix "word;another" -> "word; another"
        text = re.sub(r'(\w):(\w)', r'\1: \2', text)   # Fix "word:another" -> "word: another"
        
        # Check if there were changes
        if text != original_text:
            changes += 1
            
            # Normalize whitespace again as a final step
            text = ' '.join(text.split())
        
        metrics = {
            "changes": changes,
            "enhanced": text != original_text,
            "char_count_before": len(original_text),
            "char_count_after": len(text),
            "word_count_before": len(original_text.split()),
            "word_count_after": len(text.split()),
            "enhanced_at": datetime.now().isoformat()
        }
        
        return text, metrics
    
    def _split_run_on_word(self, word: str) -> str:
        """
        Attempt to split run-on words into proper words
        """
        if len(word) < 8:  # Don't process short words
            return word
            
        # Try different split positions
        for i in range(3, len(word) - 3):
            first_part = word[:i].lower()
            second_part = word[i:].lower()
            
            # Check if both parts are in dictionary or common RPG terms
            if (first_part in self.dictionary or 
                first_part.upper() in [t.upper() for t in self.common_rpg_terms]):
                
                if (second_part in self.dictionary or 
                    second_part.upper() in [t.upper() for t in self.common_rpg_terms]):
                    
                    # Preserve original case as much as possible
                    if word[0].isupper():
                        first_part = first_part.capitalize()
                    if word[i].isupper():
                        second_part = second_part.capitalize()
                    
                    return f"{first_part} {second_part}"
        
        # Regex-based approach for common patterns
        # Look for camelCase pattern
        camel_match = re.search(r'([a-z]+)([A-Z][a-z]+)', word)
        if camel_match:
            first = camel_match.group(1)
            second = camel_match.group(2)
            return f"{first} {second}"
            
        # Look for specific joining patterns in RPG texts
        for pattern in ["isthe", "andthe", "forthe", "ofthe", "tothe"]:
            if pattern in word.lower():
                parts = word.lower().split(pattern)
                if len(parts) == 2:
                    first = parts[0]
                    second = pattern[:2] + " " + pattern[2:] + parts[1]
                    
                    # Preserve original case
                    if word[0].isupper():
                        first = first.capitalize()
                    
                    return f"{first} {second}"
        
        return word
    
    def get_before_after_comparison(self, original: str, enhanced: str) -> Dict[str, Any]:
        """
        Generate a comparison between original and enhanced text
        """
        if original == enhanced:
            return {
                "changed": False,
                "diff_ratio": 0,
            }
        
        # Calculate text difference ratio
        total_chars = len(original)
        if total_chars == 0:
            diff_ratio = 0
        else:
            # Count differing characters
            diff_count = sum(1 for i in range(min(len(original), len(enhanced))) 
                            if original[i] != enhanced[i])
            diff_count += abs(len(original) - len(enhanced))
            diff_ratio = (diff_count / total_chars) * 100
        
        # Get quality scores
        original_quality = self.analyze_quality(original)
        enhanced_quality = self.analyze_quality(enhanced)
        
        return {
            "changed": True,
            "diff_ratio": diff_ratio,
            "quality_before": original_quality["quality_score"],
            "quality_after": enhanced_quality["quality_score"],
            "issues_before": original_quality["issue_count"],
            "issues_after": enhanced_quality["issue_count"],
            "comparison_time": datetime.now().isoformat()
        }


class DatabaseContentEnhancer:
    """Tool for enhancing content quality in databases"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.enhancer = TextQualityEnhancer(debug=debug)
        self.mongodb_manager = None
        self.chromadb_manager = None
        
        # Initialize database connections
        if MONGODB_AVAILABLE:
            try:
                self.mongodb_manager = MongoDBManager(debug=debug)
                if self.mongodb_manager.connected:
                    print("✅ Connected to MongoDB")
            except Exception as e:
                print(f"❌ MongoDB connection failed: {e}")
        
        try:
            self.chromadb_manager = MultiGameCollectionManager(debug=debug)
            print("✅ Connected to ChromaDB")
        except Exception as e:
            print(f"❌ ChromaDB connection failed: {e}")
    
    def scan_collections(self, database_type: str, collections: List[str], 
                       threshold: int = 75, limit: int = 100) -> Dict[str, Any]:
        """
        Scan collections for content below quality threshold
        """
        results = {
            "total_scanned": 0,
            "below_threshold": 0,
            "collections": {},
            "documents": []
        }
        
        if database_type in ["mongodb", "both"] and self.mongodb_manager and self.mongodb_manager.connected:
            for collection_name in collections:
                try:
                    print(f"📊 Scanning MongoDB collection: {collection_name}")
                    collection = self.mongodb_manager.database[collection_name]
                    
                    # Get total document count
                    total_docs = collection.count_documents({})
                    scanned = 0
                    below_threshold = 0
                    
                    # Process in batches to avoid memory issues
                    batch_size = min(limit, 100)  # Process up to 100 at a time
                    for doc in collection.find({}).limit(limit):
                        scanned += 1
                        content = doc.get("content", "")
                        
                        # Analyze quality
                        quality = self.enhancer.analyze_quality(content)
                        
                        if quality["quality_score"] < threshold:
                            below_threshold += 1
                            results["documents"].append({
                                "database": "mongodb",
                                "collection": collection_name,
                                "document_id": doc.get("_id"),
                                "quality_score": quality["quality_score"],
                                "issues": quality["issues"],
                                "issue_count": quality["issue_count"],
                                "content": content[:100] + "..." if len(content) > 100 else content
                            })
                    
                    # Add collection results
                    results["collections"][f"mongodb:{collection_name}"] = {
                        "total": total_docs,
                        "scanned": scanned,
                        "below_threshold": below_threshold,
                        "percent_low_quality": (below_threshold / scanned * 100) if scanned > 0 else 0
                    }
                    
                    results["total_scanned"] += scanned
                    results["below_threshold"] += below_threshold
                    
                    print(f"  - Scanned {scanned} documents, {below_threshold} below quality threshold")
                
                except Exception as e:
                    print(f"❌ Error scanning MongoDB collection {collection_name}: {e}")
        
        if database_type in ["chromadb", "both"] and self.chromadb_manager:
            for collection_name in collections:
                if collection_name not in self.chromadb_manager.collections:
                    print(f"❌ ChromaDB collection {collection_name} not found")
                    continue
                
                try:
                    print(f"📊 Scanning ChromaDB collection: {collection_name}")
                    
                    # Get documents from collection
                    docs = self.chromadb_manager.browse_collection(collection_name, limit=limit)
                    scanned = len(docs)
                    below_threshold = 0
                    
                    for doc in docs:
                        content = doc.get("content", "")
                        
                        # Analyze quality
                        quality = self.enhancer.analyze_quality(content)
                        
                        if quality["quality_score"] < threshold:
                            below_threshold += 1
                            results["documents"].append({
                                "database": "chromadb",
                                "collection": collection_name,
                                "document_id": doc.get("id"),
                                "quality_score": quality["quality_score"],
                                "issues": quality["issues"],
                                "issue_count": quality["issue_count"],
                                "content": content[:100] + "..." if len(content) > 100 else content
                            })
                    
                    # Add collection results
                    results["collections"][f"chromadb:{collection_name}"] = {
                        "total": scanned,  # ChromaDB doesn't easily provide total count
                        "scanned": scanned,
                        "below_threshold": below_threshold,
                        "percent_low_quality": (below_threshold / scanned * 100) if scanned > 0 else 0
                    }
                    
                    results["total_scanned"] += scanned
                    results["below_threshold"] += below_threshold
                    
                    print(f"  - Scanned {scanned} documents, {below_threshold} below quality threshold")
                
                except Exception as e:
                    print(f"❌ Error scanning ChromaDB collection {collection_name}: {e}")
        
        return results
    
    def enhance_batch(self, documents: List[Dict], dry_run: bool = True) -> Dict[str, Any]:
        """
        Process a batch of documents and enhance their content
        """
        results = {
            "total": len(documents),
            "enhanced": 0,
            "skipped": 0,
            "dry_run": dry_run,
            "documents": []
        }
        
        for doc in documents:
            database = doc["database"]
            collection = doc["collection"]
            doc_id = doc["document_id"]
            content = self._get_document_content(database, collection, doc_id)
            
            if not content:
                print(f"⚠️ Could not retrieve content for document {doc_id} in {database}:{collection}")
                results["skipped"] += 1
                continue
            
            # Enhance content
            enhanced_content, metrics = self.enhancer.enhance_text(content)
            
            # Get comparison metrics
            comparison = self.enhancer.get_before_after_comparison(content, enhanced_content)
            
            document_result = {
                "database": database,
                "collection": collection,
                "document_id": doc_id,
                "enhanced": metrics["enhanced"],
                "changes": metrics["changes"],
                "quality_before": comparison.get("quality_before", 0),
                "quality_after": comparison.get("quality_after", 0),
                "content_before": content[:100] + "..." if len(content) > 100 else content,
                "content_after": enhanced_content[:100] + "..." if len(enhanced_content) > 100 else enhanced_content
            }
            
            results["documents"].append(document_result)
            
            if metrics["enhanced"]:
                results["enhanced"] += 1
                
                # Update document if not a dry run
                if not dry_run:
                    self._update_document_content(database, collection, doc_id, enhanced_content)
                    print(f"✅ Enhanced document {doc_id} in {database}:{collection}")
                else:
                    print(f"📝 Would enhance document {doc_id} in {database}:{collection} (dry run)")
            else:
                results["skipped"] += 1
                print(f"⏩ No changes needed for document {doc_id} in {database}:{collection}")
        
        return results
    
    def backup_collection(self, database_type: str, collection_name: str, output_dir: Path) -> bool:
        """
        Create a backup of a collection before enhancing it
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if database_type == "mongodb" and self.mongodb_manager and self.mongodb_manager.connected:
            try:
                collection = self.mongodb_manager.database[collection_name]
                backup_file = output_dir / f"mongodb_{collection_name}_backup_{timestamp}.json"
                
                # Get all documents
                docs = list(collection.find({}))
                
                # Convert ObjectId to string for JSON serialization
                for doc in docs:
                    if "_id" in doc and not isinstance(doc["_id"], str):
                        doc["_id"] = str(doc["_id"])
                
                # Save as JSON
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(docs, f, ensure_ascii=False, indent=2)
                
                print(f"✅ Backed up {len(docs)} documents from MongoDB:{collection_name} to {backup_file}")
                return True
            
            except Exception as e:
                print(f"❌ Error backing up MongoDB collection {collection_name}: {e}")
                return False
        
        elif database_type == "chromadb" and self.chromadb_manager:
            try:
                if collection_name not in self.chromadb_manager.collections:
                    print(f"❌ ChromaDB collection {collection_name} not found")
                    return False
                
                # Get all documents
                docs = self.chromadb_manager.browse_collection(collection_name, limit=10000)
                
                backup_file = output_dir / f"chromadb_{collection_name}_backup_{timestamp}.json"
                
                # Save as JSON
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(docs, f, ensure_ascii=False, indent=2)
                
                print(f"✅ Backed up {len(docs)} documents from ChromaDB:{collection_name} to {backup_file}")
                return True
            
            except Exception as e:
                print(f"❌ Error backing up ChromaDB collection {collection_name}: {e}")
                return False
        
        return False
    
    def _get_document_content(self, database: str, collection: str, doc_id: str) -> str:
        """
        Get document content from database
        """
        try:
            if database == "mongodb" and self.mongodb_manager and self.mongodb_manager.connected:
                collection_obj = self.mongodb_manager.database[collection]
                doc = collection_obj.find_one({"_id": doc_id})
                if doc:
                    return doc.get("content", "")
            
            elif database == "chromadb" and self.chromadb_manager:
                # This is an inefficient way to get a single document but works for this tool
                docs = self.chromadb_manager.browse_collection(collection, limit=1000)
                for doc in docs:
                    if doc.get("id") == doc_id:
                        return doc.get("content", doc.get("document", ""))
        
        except Exception as e:
            print(f"❌ Error getting content: {e}")
        
        return ""
    
    def _update_document_content(self, database: str, collection: str, 
                              doc_id: str, content: str) -> bool:
        """
        Update document content in database
        """
        try:
            if database == "mongodb" and self.mongodb_manager and self.mongodb_manager.connected:
                collection_obj = self.mongodb_manager.database[collection]
                result = collection_obj.update_one(
                    {"_id": doc_id}, 
                    {
                        "$set": {
                            "content": content,
                            "metadata.enhanced": True,
                            "metadata.enhanced_at": datetime.now().isoformat()
                        }
                    }
                )
                return result.modified_count > 0
            
            elif database == "chromadb" and self.chromadb_manager:
                # ChromaDB doesn't have a simple update mechanism
                # We'd need to delete and re-add the document
                # This is not implemented here as it's more complex
                print(f"⚠️ ChromaDB document update not implemented in this version")
                return False
        
        except Exception as e:
            print(f"❌ Error updating content: {e}")
        
        return False
    
    def generate_report(self, results: Dict[str, Any], output_dir: Path) -> Path:
        """
        Generate a comprehensive report of enhancement results
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"enhancement_report_{timestamp}.json"
        
        # Add timestamp and summary to results
        results["report_generated"] = datetime.now().isoformat()
        results["summary"] = {
            "total_documents": results.get("total", 0),
            "enhanced_documents": results.get("enhanced", 0),
            "skipped_documents": results.get("skipped", 0),
            "enhancement_rate": (results.get("enhanced", 0) / results.get("total", 1)) * 100,
            "dry_run": results.get("dry_run", True)
        }
        
        # Save report as JSON
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Report generated: {report_file}")
        return report_file


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Database Content Enhancement Tool")
    
    parser.add_argument("--database", "-d", choices=["mongodb", "chromadb", "both"], 
                      default="both", help="Target database(s) to enhance")
    
    parser.add_argument("--collections", "-c", nargs="+", 
                      help="Specific collections to scan (omit to scan all)")
    
    parser.add_argument("--threshold", "-t", type=int, default=75,
                      help="Quality threshold percentage (default: 75)")
    
    parser.add_argument("--limit", "-l", type=int, default=100,
                      help="Maximum documents to process (default: 100)")
    
    parser.add_argument("--batch-size", "-b", type=int, default=10,
                      help="Batch size for enhancement (default: 10)")
    
    parser.add_argument("--dry-run", action="store_true", 
                      help="Preview changes without applying them")
    
    parser.add_argument("--backup", action="store_true",
                      help="Create backups before enhancement")
    
    parser.add_argument("--output-dir", "-o", type=Path, default=Path("./output"),
                      help="Output directory for reports and backups (default: ./output)")
    
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug output")
    
    return parser.parse_args()


def main():
    """Main execution function"""
    args = parse_args()
    
    print(f"📚 Database Content Enhancement Tool")
    print(f"====================================")
    
    # Create enhancer
    enhancer = DatabaseContentEnhancer(debug=args.debug)
    
    # Check database connections
    if args.database in ["mongodb", "both"] and not enhancer.mongodb_manager:
        print("❌ MongoDB connection required but not available")
        return 1
    
    if args.database in ["chromadb", "both"] and not enhancer.chromadb_manager:
        print("❌ ChromaDB connection required but not available")
        return 1
    
    # Get collections to process
    collections = args.collections or []
    
    if not collections:
        # Get all available collections if none specified
        if args.database in ["mongodb", "both"] and enhancer.mongodb_manager:
            mongo_collections = enhancer.mongodb_manager.get_status().get("collections", [])
            collections.extend(mongo_collections)
        
        if args.database in ["chromadb", "both"] and enhancer.chromadb_manager:
            chroma_collections = list(enhancer.chromadb_manager.collections.keys())
            collections.extend(chroma_collections)
    
    if not collections:
        print("❌ No collections found to process")
        return 1
    
    print(f"🔍 Processing collections: {', '.join(collections)}")
    print(f"📊 Quality threshold: {args.threshold}%")
    print(f"📦 Document limit: {args.limit}")
    print(f"🧪 Dry run: {'Yes' if args.dry_run else 'No'}")
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup collections if requested
    if args.backup:
        print(f"\n📦 Creating backups...")
        
        for collection in collections:
            if args.database in ["mongodb", "both"] and enhancer.mongodb_manager:
                enhancer.backup_collection("mongodb", collection, args.output_dir)
            
            if args.database in ["chromadb", "both"] and enhancer.chromadb_manager:
                enhancer.backup_collection("chromadb", collection, args.output_dir)
    
    # Scan collections for low quality content
    print(f"\n🔍 Scanning collections for content below {args.threshold}% quality...")
    scan_results = enhancer.scan_collections(args.database, collections, args.threshold, args.limit)
    
    # Generate scan report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scan_report_file = args.output_dir / f"scan_report_{timestamp}.json"
    with open(scan_report_file, 'w', encoding='utf-8') as f:
        json.dump(scan_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 Scan Summary:")
    print(f"  - Total documents scanned: {scan_results['total_scanned']}")
    print(f"  - Documents below threshold: {scan_results['below_threshold']}")
    
    if scan_results['total_scanned'] > 0:
        percent = (scan_results['below_threshold'] / scan_results['total_scanned']) * 100
        print(f"  - Percentage: {percent:.1f}%")
    
    print(f"  - Scan report saved to: {scan_report_file}")
    
    # Exit if nothing to enhance
    if scan_results['below_threshold'] == 0:
        print("\n✅ All documents meet quality standards. No enhancement needed.")
        return 0
    
    # Process documents in batches
    documents_to_enhance = scan_results['documents']
    total_batches = (len(documents_to_enhance) + args.batch_size - 1) // args.batch_size
    
    print(f"\n🔄 Processing {len(documents_to_enhance)} documents in {total_batches} batches...")
    
    all_results = {
        "total": 0,
        "enhanced": 0,
        "skipped": 0,
        "dry_run": args.dry_run,
        "documents": []
    }
    
    for i in range(0, len(documents_to_enhance), args.batch_size):
        batch = documents_to_enhance[i:i+args.batch_size]
        print(f"\n🔄 Processing batch {i//args.batch_size + 1}/{total_batches} ({len(batch)} documents)...")
        
        # Process batch
        batch_results = enhancer.enhance_batch(batch, dry_run=args.dry_run)
        
        # Update overall results
        all_results["total"] += batch_results["total"]
        all_results["enhanced"] += batch_results["enhanced"]
        all_results["skipped"] += batch_results["skipped"]
        all_results["documents"].extend(batch_results["documents"])
    
    # Generate final report
    report_file = enhancer.generate_report(all_results, args.output_dir)
    
    # Print summary
    print(f"\n🎉 Enhancement Complete!")
    print(f"  - Documents processed: {all_results['total']}")
    print(f"  - Documents enhanced: {all_results['enhanced']}")
    print(f"  - Documents unchanged: {all_results['skipped']}")
    
    if all_results['total'] > 0:
        percent = (all_results['enhanced'] / all_results['total']) * 100
        print(f"  - Enhancement rate: {percent:.1f}%")
    
    if args.dry_run:
        print(f"\n⚠️ This was a dry run. No changes were applied.")
        print(f"  - Run without --dry-run to apply changes")
    
    print(f"\n📋 Detailed report saved to: {report_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())