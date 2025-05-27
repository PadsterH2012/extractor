#!/usr/bin/env python3
"""
Extraction v3: Multi-Game RPG PDF Processor
Unified command-line interface for multi-game PDF extraction and collection management

Usage:
  python3 Extraction.py extract <pdf_file>                    # Extract single PDF
  python3 Extraction.py batch <pdf_directory>                 # Process all PDFs in directory
  python3 Extraction.py import <json_file>                    # Import to ChromaDB
  python3 Extraction.py status                                # Show collection status
  python3 Extraction.py browse <collection>                   # Browse specific collection
  python3 Extraction.py search <query>                        # Search across collections
  python3 Extraction.py compare <query>                       # Compare results across collections
  python3 Extraction.py full <pdf_file_or_dir>               # Extract + Import in one step

Game-Aware Options:
  --game-type "D&D"                                           # Force specific game type
  --edition "1st"                                             # Force specific edition
  --across-games                                              # Compare across different games
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file from current directory
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")

# Import modules
from Modules.pdf_processor import MultiGamePDFProcessor
from Modules.multi_collection_manager import MultiGameCollectionManager
from Modules.game_configs import get_supported_games

def main():
    parser = argparse.ArgumentParser(
        description="Extraction v3: Multi-Game RPG PDF Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract single PDF with auto-detection
  python3 Extraction.py extract "D&D_5th_Edition_PHB.pdf"

  # Force specific game type
  python3 Extraction.py extract "unknown_rpg.pdf" --game-type "Pathfinder" --edition "2nd"

  # Batch process directory
  python3 Extraction.py batch ./mixed_rpg_pdfs/

  # Search specific game
  python3 Extraction.py search "armor class" --game-type "D&D" --edition "1st"

  # Cross-game comparison
  python3 Extraction.py compare "saving throws" --across-games

  # Show collections by game
  python3 Extraction.py status --game-type "Pathfinder"
        """
    )

    parser.add_argument("command",
                       choices=["extract", "batch", "import", "status", "browse", "search", "compare", "full"],
                       help="Command to execute")
    parser.add_argument("target", nargs="?",
                       help="PDF file, directory, JSON file, collection name, or search query")

    # Output options
    parser.add_argument("-o", "--output", type=Path, default=Path("./extracted"),
                       help="Output directory (default: ./extracted)")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Verbose logging")
    parser.add_argument("--debug", action="store_true",
                       help="Debug mode with detailed output")

    # Game-specific options
    parser.add_argument("--game-type", "-g",
                       help="Force game type detection (overrides AI)")
    parser.add_argument("--edition", "-e",
                       help="Force edition detection (overrides AI)")
    parser.add_argument("--book", "-b",
                       help="Filter by book type")

    # AI options
    parser.add_argument("--ai-provider",
                       choices=["openai", "claude", "anthropic", "local", "mock"],
                       default="mock",
                       help="AI provider for game detection (default: mock)")
    parser.add_argument("--no-ai", action="store_true",
                       help="Disable AI detection, use fallback methods")
    parser.add_argument("--ai-model",
                       help="Specific AI model to use (e.g., gpt-4, claude-3-sonnet)")
    parser.add_argument("--ai-api-key",
                       help="API key for AI provider (overrides environment variable)")
    parser.add_argument("--ai-base-url",
                       help="Custom base URL for AI API (for local/custom endpoints)")
    parser.add_argument("--ai-max-tokens", type=int, default=4000,
                       help="Maximum tokens for AI responses (default: 4000)")
    parser.add_argument("--ai-temperature", type=float, default=0.1,
                       help="AI temperature for consistency (default: 0.1)")
    parser.add_argument("--ai-timeout", type=int, default=30,
                       help="AI request timeout in seconds (default: 30)")
    parser.add_argument("--ai-retries", type=int, default=3,
                       help="Number of AI request retries (default: 3)")
    parser.add_argument("--ai-debug", action="store_true",
                       help="Enable detailed AI debugging output")
    parser.add_argument("--ai-cache", action="store_true", default=True,
                       help="Enable AI response caching (default: enabled)")
    parser.add_argument("--no-ai-cache", action="store_false", dest="ai_cache",
                       help="Disable AI response caching")

    # Collection options
    parser.add_argument("--collection",
                       help="Force specific ChromaDB collection name")
    parser.add_argument("--across-games", action="store_true",
                       help="Compare across different game types")
    parser.add_argument("--limit", "-l", type=int, default=5,
                       help="Number of results to return")

    args = parser.parse_args()

    # Validate arguments
    if args.command in ["extract", "batch", "import", "full"] and not args.target:
        print("❌ Target file/directory required for this command")
        sys.exit(1)

    if args.command in ["browse", "search", "compare"] and not args.target:
        print("❌ Collection name or search query required for this command")
        sys.exit(1)

    try:
        # Initialize components with AI options
        ai_provider = "mock" if args.no_ai else args.ai_provider

        # Build AI configuration
        ai_config = {
            "provider": ai_provider,
            "model": args.ai_model,
            "api_key": args.ai_api_key,
            "base_url": args.ai_base_url,
            "max_tokens": args.ai_max_tokens,
            "temperature": args.ai_temperature,
            "timeout": args.ai_timeout,
            "retries": args.ai_retries,
            "debug": args.ai_debug,
            "cache_enabled": args.ai_cache
        }

        processor = MultiGamePDFProcessor(
            verbose=args.verbose,
            debug=args.debug,
            ai_config=ai_config
        )
        manager = MultiGameCollectionManager(debug=args.debug)

        if args.command == "extract":
            handle_extract(processor, args)

        elif args.command == "batch":
            handle_batch(processor, args)

        elif args.command == "import":
            handle_import(manager, args)

        elif args.command == "status":
            handle_status(manager, args)

        elif args.command == "browse":
            handle_browse(manager, args)

        elif args.command == "search":
            handle_search(manager, args)

        elif args.command == "compare":
            handle_compare(manager, args)

        elif args.command == "full":
            handle_full(processor, manager, args)

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def handle_extract(processor: MultiGamePDFProcessor, args):
    """Handle single PDF extraction"""
    pdf_path = Path(args.target)
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        sys.exit(1)

    print(f"📄 Extracting: {pdf_path.name}")
    if args.game_type:
        print(f"🎮 Forced game type: {args.game_type}")
    if args.edition:
        print(f"📖 Forced edition: {args.edition}")

    # Extract PDF
    extraction_data = processor.extract_pdf(pdf_path, args.game_type, args.edition)

    # Save extraction
    output_files = processor.save_extraction(extraction_data, args.output)

    # Display results
    summary = extraction_data["extraction_summary"]
    print(f"\n✅ Extraction complete!")
    print(f"🎮 Game: {summary['game_type']}")
    print(f"📖 Edition: {summary['edition']}")
    print(f"🏷️  Collection: {summary['collection_name']}")
    print(f"📄 Pages: {summary['total_pages']}")
    print(f"📊 Words: {summary['total_words']:,}")
    print(f"📋 Tables: {summary['total_tables']}")

    print(f"\n💾 Output files:")
    for format_name, file_path in output_files.items():
        print(f"  {format_name}: {file_path}")

def handle_batch(processor: MultiGamePDFProcessor, args):
    """Handle batch PDF processing"""
    pdf_dir = Path(args.target)
    if not pdf_dir.is_dir():
        print(f"❌ Directory not found: {pdf_dir}")
        sys.exit(1)

    print(f"📁 Batch processing: {pdf_dir}")
    if args.game_type:
        print(f"🎮 Forced game type: {args.game_type}")
    if args.edition:
        print(f"📖 Forced edition: {args.edition}")

    # Process all PDFs
    results = processor.batch_extract(pdf_dir, args.game_type, args.edition)

    # Save each extraction
    total_pages = 0
    total_words = 0
    total_tables = 0

    for result in results:
        if result["success"]:
            pdf_file = result["file"]
            extraction_data = result["data"]

            # Save to subdirectory
            pdf_output_dir = args.output / pdf_file.stem
            output_files = processor.save_extraction(extraction_data, pdf_output_dir)

            summary = extraction_data["extraction_summary"]
            total_pages += summary["total_pages"]
            total_words += summary["total_words"]
            total_tables += summary["total_tables"]

            print(f"✅ {pdf_file.name}: {summary['total_pages']} pages, "
                  f"{summary['total_words']:,} words, {summary['total_tables']} tables")
            print(f"   🎮 {summary['game_type']} | 📖 {summary['edition']} | 🏷️  {summary['collection_name']}")
        else:
            print(f"❌ {result['file'].name}: {result['error']}")

    successful = sum(1 for r in results if r["success"])
    print(f"\n🎉 Batch complete: {successful}/{len(results)} successful")
    print(f"📊 Total: {total_pages} pages, {total_words:,} words, {total_tables} tables")

def handle_import(manager: MultiGameCollectionManager, args):
    """Handle JSON import to ChromaDB"""
    json_path = Path(args.target)
    if not json_path.exists():
        print(f"❌ JSON file not found: {json_path}")
        sys.exit(1)

    print(f"📥 Importing: {json_path.name}")
    success = manager.import_to_chromadb(json_path, args.collection)

    if success:
        print("✅ Import successful!")
    else:
        print("❌ Import failed!")
        sys.exit(1)

def handle_status(manager: MultiGameCollectionManager, args):
    """Handle collection status display"""
    stats = manager.show_status(args.game_type)

    if args.verbose:
        print(f"\n📈 Statistics:")
        print(f"  Total Collections: {stats['total_collections']}")
        print(f"  Total Documents: {stats['total_documents']:,}")

def handle_browse(manager: MultiGameCollectionManager, args):
    """Handle collection browsing"""
    collection_name = args.target

    if collection_name not in manager.collections:
        print(f"❌ Collection '{collection_name}' not found")
        print(f"Available: {', '.join(manager.collections.keys())}")
        sys.exit(1)

    docs = manager.browse_collection(collection_name, args.limit)

    if docs:
        parsed = manager.parse_collection_name(collection_name)
        print(f"📖 Browsing {collection_name} ({len(docs)} documents):")
        print(f"🎮 Game: {parsed['game_type']} | 📖 Edition: {parsed['edition']} | 📚 Book: {parsed['book']}")
        print("=" * 70)

        for i, doc_data in enumerate(docs):
            metadata = doc_data["metadata"]
            title = metadata.get("title", "Unknown")
            page = metadata.get("page", "?")
            category = metadata.get("category", "General")

            print(f"\n{i+1}. {title}")
            print(f"   📄 Page: {page} | 📂 Category: {category}")

            preview = doc_data["content"][:200] + "..." if len(doc_data["content"]) > 200 else doc_data["content"]
            print(f"   📝 {preview}")
    else:
        print(f"❌ No documents found in {collection_name}")

def handle_search(manager: MultiGameCollectionManager, args):
    """Handle collection searching"""
    query = args.target

    # Search with game filtering
    all_results = manager.search_with_game_filter(
        query,
        game_type=args.game_type,
        edition=args.edition,
        book=args.book,
        n_results=args.limit
    )

    if all_results:
        print(f"🔍 Search results for '{query}':")
        print("=" * 70)

        for collection_name, results in all_results.items():
            parsed = manager.parse_collection_name(collection_name)
            print(f"\n📚 {parsed['game_type']} {parsed['edition']} {parsed['book']} ({len(results)} results):")

            for i, result in enumerate(results):
                metadata = result["metadata"]
                title = metadata.get("title", "Unknown")
                page = metadata.get("page", "?")

                print(f"  {i+1}. {title} (Page {page})")
                preview = result["content"][:100] + "..." if len(result["content"]) > 100 else result["content"]
                print(f"      {preview}")

                if "distance" in result:
                    print(f"      📊 Relevance: {1-result['distance']:.2f}")
    else:
        print(f"❌ No results found for '{query}' with specified criteria")

def handle_compare(manager: MultiGameCollectionManager, args):
    """Handle cross-collection comparison"""
    query = args.target

    if args.across_games:
        manager.compare_across_games(query, args.limit)
    else:
        # Compare within filtered collections
        all_results = manager.search_with_game_filter(
            query,
            game_type=args.game_type,
            edition=args.edition,
            book=args.book,
            n_results=2
        )

        if all_results:
            print(f"🔍 Comparing search results for: '{query}'")
            print("=" * 70)

            for collection_name, results in all_results.items():
                parsed = manager.parse_collection_name(collection_name)
                print(f"\n📚 {parsed['game_type']} {parsed['edition']} {parsed['book']} ({len(results)} results):")
                print("-" * 40)

                for i, result in enumerate(results):
                    metadata = result["metadata"]
                    title = metadata.get("title", "Unknown")
                    page = metadata.get("page", "?")

                    print(f"{i+1}. {title} (Page {page})")

                    # Show content preview
                    content = result["content"]
                    query_pos = content.lower().find(query.lower())
                    if query_pos != -1:
                        start = max(0, query_pos - 50)
                        end = min(len(content), query_pos + len(query) + 50)
                        context = content[start:end]
                        print(f"   📝 ...{context}...")
                    else:
                        preview = content[:100] + "..." if len(content) > 100 else content
                        print(f"   📝 {preview}")

                    if "distance" in result:
                        print(f"   📊 Relevance: {1-result['distance']:.2f}")
                    print()
        else:
            print(f"❌ No results found for '{query}' with specified criteria")

def handle_full(processor: MultiGamePDFProcessor, manager: MultiGameCollectionManager, args):
    """Handle full extraction + import workflow"""
    target_path = Path(args.target)

    if target_path.is_file():
        # Single PDF
        print(f"📄 Full processing: {target_path.name}")
        extraction_data = processor.extract_pdf(target_path, args.game_type, args.edition)
        output_files = processor.save_extraction(extraction_data, args.output)

        # Import to ChromaDB
        chromadb_file = output_files["chromadb"]
        success = manager.import_to_chromadb(chromadb_file, args.collection)

        summary = extraction_data["extraction_summary"]
        print(f"✅ Full processing complete!")
        print(f"🎮 {summary['game_type']} | 📖 {summary['edition']} | 🏷️  {summary['collection_name']}")
        print(f"📊 {summary['total_pages']} pages, {summary['total_words']:,} words")
        print(f"📥 ChromaDB import: {'✅ Success' if success else '❌ Failed'}")

    elif target_path.is_dir():
        # Batch processing
        print(f"📁 Full batch processing: {target_path}")
        results = processor.batch_extract(target_path, args.game_type, args.edition)

        import_success = 0
        for result in results:
            if result["success"]:
                pdf_file = result["file"]
                extraction_data = result["data"]

                # Save extraction
                pdf_output_dir = args.output / pdf_file.stem
                output_files = processor.save_extraction(extraction_data, pdf_output_dir)

                # Import to ChromaDB
                chromadb_file = output_files["chromadb"]
                if manager.import_to_chromadb(chromadb_file, args.collection):
                    import_success += 1

        successful_extractions = sum(1 for r in results if r["success"])
        print(f"\n🎉 Full batch complete!")
        print(f"📄 Extractions: {successful_extractions}/{len(results)} successful")
        print(f"📥 ChromaDB imports: {import_success}/{successful_extractions} successful")

    else:
        print(f"❌ Target not found: {target_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
