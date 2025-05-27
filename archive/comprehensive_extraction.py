def main():
    parser = argparse.ArgumentParser(description="Extract AD&D PDF content for database ingestion")
    parser.add_argument("pdf_path", type=Path, help="Path to the AD&D PDF file")
    parser.add_argument("-o", "--output", type=Path, default=Path("./extracted"), 
                       help="Output directory (default: ./extracted)")
    parser.add_argument("-m", "--method", choices=["auto", "text", "ocr"], default="auto",
                       help="Extraction method (default: auto)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--test-first", action="store_true", 
                       help="Run confidence test before extraction")
    parser.add_argument("--test-pages", type=int, default=5,
                       help="Number of pages to test (default: 5)")
    parser.add_argument("--min-confidence", type=float, default=60.0,
                       help="Minimum confidence to proceed (default: 60.0)")
    
    args = parser.parse_args()
    
    # Setup
    setup_logging(args.verbose)
    
    # Validate input
    if not validate_pdf(args.pdf_path):
        sys.exit(1)
    
    # Run confidence test if requested or if method is auto
    if args.test_first or args.method == "auto":
        logging.info("Running confidence test...")
        
        try:
            from confidence_tester import PDFConfidenceTester, generate_confidence_report
            
            tester = PDFConfidenceTester(str(args.pdf_path))
            tester.test_pages = args.test_pages
            metrics = tester.run_comprehensive_test()
            
            # Generate test report
            test_output_dir = args.output / "confidence_test"
            test_output_dir.mkdir(parents=True, exist_ok=True)
            
            report = generate_confidence_report(
                metrics, 
                str(test_output_dir / "confidence_report.json")
            )
            
            # Display results
            print(f"\n=== CONFIDENCE TEST RESULTS ===")
            print(f"Overall Confidence: {metrics.overall_confidence:.1f}%")
            print(f"Recommended Method: {metrics.recommended_method}")
            print(f"Text Extraction: {metrics.text_extraction_confidence:.1f}%")
            print(f"OCR Extraction: {metrics.ocr_confidence:.1f}%")
            print(f"Layout Detection: {metrics.layout_detection_confidence:.1f}%")
            
            if metrics.issues_found:
                print(f"\nIssues Found ({len(metrics.issues_found)}):")
                for issue in metrics.issues_found[:5]:
                    print#!/usr/bin/env python3
"""
Complete AD&D PDF Extraction Script
Handles multi-column layouts, tables, and generates structured data for database ingestion
"""

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Dict, List, Any

# Import our extraction classes (assuming they're in the same directory)
# from pdf_extractor import ADDPDFExtractor
# from ocr_pdf_extractor import OCRPDFExtractor

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('pdf_extraction.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def validate_pdf(pdf_path: Path) -> bool:
    """Validate that the PDF exists and is readable"""
    if not pdf_path.exists():
        logging.error(f"PDF file not found: {pdf_path}")
        return False
    
    if not pdf_path.suffix.lower() == '.pdf':
        logging.error(f"File is not a PDF: {pdf_path}")
        return False
    
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        doc.close()
        logging.info(f"PDF validated: {page_count} pages")
        return True
    except Exception as e:
        logging.error(f"Error opening PDF: {e}")
        return False

def detect_pdf_type(pdf_path: Path) -> str:
    """Detect if PDF is text-based or image-based (scanned)"""
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        
        # Check first few pages for text content
        text_pages = 0
        pages_to_check = min(5, len(doc))
        
        for page_num in range(pages_to_check):
            page = doc[page_num]
            text = page.get_text().strip()
            if len(text) > 100:  # Reasonable amount of text
                text_pages += 1
        
        doc.close()
        
        if text_pages >= pages_to_check // 2:
            return "text"  # Mostly text-based
        else:
            return "scanned"  # Likely scanned/image-based
            
    except Exception as e:
        logging.warning(f"Could not determine PDF type: {e}")
        return "unknown"

def extract_metadata_from_filename(pdf_path: Path) -> Dict[str, Any]:
    """Extract metadata from filename"""
    filename = pdf_path.stem.lower()
    
    metadata = {
        "original_filename": pdf_path.name,
        "file_size": pdf_path.stat().st_size,
        "source_type": "pdf_extraction"
    }
    
    # Detect AD&D edition and book type from filename
    if "1st" in filename or "1e" in filename:
        metadata["edition"] = "1st Edition"
    elif "2nd" in filename or "2e" in filename:
        metadata["edition"] = "2nd Edition"
    elif "3rd" in filename or "3e" in filename:
        metadata["edition"] = "3rd Edition"
    
    # Detect book type
    if "dmg" in filename or "dungeon master" in filename:
        metadata["book_type"] = "Dungeon Masters Guide"
        metadata["abbreviation"] = "DMG"
    elif "phb" in filename or "player" in filename:
        metadata["book_type"] = "Players Handbook" 
        metadata["abbreviation"] = "PHB"
    elif "monster manual" in filename or "mm" in filename:
        metadata["book_type"] = "Monster Manual"
        metadata["abbreviation"] = "MM"
    elif "fiend folio" in filename:
        metadata["book_type"] = "Fiend Folio"
        metadata["abbreviation"] = "FF"
    
    return metadata

def create_output_structure(output_dir: Path, book_metadata: Dict) -> Dict[str, Path]:
    """Create organized output directory structure"""
    base_name = f"{book_metadata.get('edition', 'Unknown')}_{book_metadata.get('abbreviation', 'Book')}"
    base_name = base_name.replace(" ", "_").replace("&", "and")
    
    paths = {
        "base": output_dir / base_name,
        "raw_json": output_dir / base_name / "raw_extraction.json",
        "mongodb": output_dir / base_name / "mongodb_ready.json",
        "chromadb": output_dir / base_name / "chromadb_ready.json",
        "markdown": output_dir / base_name / "markdown",
        "tables": output_dir / base_name / "tables",
        "images": output_dir / base_name / "images",
        "logs": output_dir / base_name / "extraction.log"
    }
    
    # Create directories
    for key, path in paths.items():
        if key in ["markdown", "tables", "images", "base"]:
            path.mkdir(parents=True, exist_ok=True)
    
    return paths

def process_with_text_extraction(pdf_path: Path, output_paths: Dict, metadata: Dict) -> List[Dict]:
    """Process PDF using text-based extraction"""
    logging.info("Using text-based extraction method")
    
    try:
        from pdf_extractor import ADDPDFExtractor
        
        extractor = ADDPDFExtractor(str(pdf_path))
        sections = extractor.extract_with_structure()
        
        logging.info(f"Extracted {len(sections)} sections using text method")
        
        # Convert to dictionary format
        extracted_data = []
        for section in sections:
            data = {
                "title": section.title,
                "content": section.content,
                "page_start": section.page_start + 1,
                "page_end": section.page_end + 1,
                "heading_level": section.level,
                "tables": section.tables,
                "metadata": {**section.metadata, **metadata},
                "extraction_method": "text_based",
                "extraction_confidence": 95.0  # High confidence for text extraction
            }
            extracted_data.append(data)
        
        return extracted_data
        
    except ImportError:
        logging.error("Text extraction dependencies not available")
        return []
    except Exception as e:
        logging.error(f"Text extraction failed: {e}")
        return []

def process_with_ocr_extraction(pdf_path: Path, output_paths: Dict, metadata: Dict) -> List[Dict]:
    """Process PDF using OCR-based extraction"""
    logging.info("Using OCR-based extraction method")
    
    try:
        from ocr_pdf_extractor import OCRPDFExtractor
        
        extractor = OCRPDFExtractor(str(pdf_path))
        sections = extractor.extract_with_ocr()
        
        logging.info(f"Extracted {len(sections)} sections using OCR method")
        
        # Convert to dictionary format
        extracted_data = []
        for section in sections:
            data = {
                "title": section.title,
                "content": section.content,
                "page": section.page_num + 1,
                "section_type": section.section_type,
                "bbox": {
                    "x": section.bbox[0],
                    "y": section.bbox[1], 
                    "width": section.bbox[2],
                    "height": section.bbox[3]
                },
                "extraction_confidence": section.confidence,
                "metadata": {**metadata, "needs_review": section.confidence < 70},
                "extraction_method": "ocr_based"
            }
            extracted_data.append(data)
        
        return extracted_data
        
    except ImportError:
        logging.error("OCR extraction dependencies not available")
        return []
    except Exception as e:
        logging.error(f"OCR extraction failed: {e}")
        return []

def enhance_extracted_data(extracted_data: List[Dict]) -> List[Dict]:
    """Post-process and enhance extracted data"""
    logging.info("Enhancing extracted data")
    
    enhanced_data = []
    
    for item in extracted_data:
        # Clean and enhance content
        content = item.get("content", "")
        
        # Basic text cleaning
        content = content.strip()
        content = ' '.join(content.split())  # Normalize whitespace
        
        # Extract additional metadata
        word_count = len(content.split())
        char_count = len(content)
        
        # Categorize content
        category = categorize_content(item.get("title", ""), content)
        tags = generate_tags(item.get("title", ""), content)
        
        # Enhanced item
        enhanced_item = {
            **item,
            "content": content,
            "word_count": word_count,
            "char_count": char_count,
            "category": category,
            "tags": tags,
            "search_text": create_search_text(item.get("title", ""), content),
            "processing_timestamp": str(datetime.now()),
        }
        
        enhanced_data.append(enhanced_item)
    
    return enhanced_data

def categorize_content(title: str, content: str) -> str:
    """Categorize content based on title and content analysis"""
    title_lower = title.lower()
    content_lower = content.lower()
    
    # Define category keywords
    categories = {
        "Combat": ["combat", "attack", "armor", "weapon", "damage", "initiative", "thac0", "armor class"],
        "Magic": ["spell", "magic", "magical", "enchant", "potion", "scroll", "wand", "staff"],
        "Character Creation": ["character", "ability", "race", "class", "generation", "stats", "attributes"],
        "Monsters": ["monster", "creature", "encounter", "bestiary", "hit dice", "hit points"],
        "Treasure": ["treasure", "gem", "gold", "coins", "magical items", "artifact", "wealth"],
        "Campaign": ["campaign", "adventure", "world", "setting", "dungeon", "wilderness"],
        "Rules": ["rule", "procedure", "mechanic", "system", "table", "chart"],
        "Tables": ["table", "chart", "random", "generation", "roll", "dice"]
    }
    
    # Score each category
    category_scores = {}
    for category, keywords in categories.items():
        score = 0
        for keyword in keywords:
            if keyword in title_lower:
                score += 3  # Title matches are weighted higher
            if keyword in content_lower:
                score += content_lower.count(keyword)
        category_scores[category] = score
    
    # Return highest scoring category
    if category_scores:
        return max(category_scores, key=category_scores.get)
    
    return "General"

def generate_tags(title: str, content: str) -> List[str]:
    """Generate relevant tags for content"""
    tags = set()
    
    text_to_analyze = (title + " " + content).lower()
    
    # Common D&D terms
    tag_patterns = {
        "combat": ["combat", "fight", "attack", "damage"],
        "spells": ["spell", "magic", "cast", "enchant"],
        "characters": ["character", "player", "class", "level"],
        "monsters": ["monster", "creature", "beast", "dragon"],
        "treasure": ["treasure", "gold", "gem", "magic item"],
        "dice": ["dice", "roll", "d4", "d6", "d8", "d10", "d12", "d20", "d100"],
        "tables": ["table", "chart", "random"],
        "rules": ["rule", "system", "mechanic"],
        "equipment": ["armor", "weapon", "shield", "equipment"]
    }
    
    for tag, patterns in tag_patterns.items():
        if any(pattern in text_to_analyze for pattern in patterns):
            tags.add(tag)
    
    # Add specific game system tags
    if any(term in text_to_analyze for term in ["thac0", "armor class", "saving throw"]):
        tags.add("core_mechanics")
    
    if any(term in text_to_analyze for term in ["1st level", "2nd level", "3rd level"]):
        tags.add("level_based")
    
    return sorted(list(tags))

def create_search_text(title: str, content: str) -> str:
    """Create optimized search text"""
    # Combine title and first few sentences of content
    sentences = content.split('.')[:3]  # First 3 sentences
    search_parts = [title] + sentences
    
    return ' '.join(part.strip() for part in search_parts if part.strip())

def save_outputs(extracted_data: List[Dict], output_paths: Dict, metadata: Dict):
    """Save extracted data in multiple formats"""
    from datetime import datetime
    
    # Raw JSON output
    with open(output_paths["raw_json"], 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                **metadata,
                "extraction_timestamp": str(datetime.now()),
                "total_sections": len(extracted_data)
            },
            "sections": extracted_data
        }, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Saved raw JSON to {output_paths['raw_json']}")
    
    # MongoDB-ready format
    mongodb_docs = []
    for item in extracted_data:
        doc = {
            "_id": f"{metadata.get('abbreviation', 'DOC')}_{item.get('page', 0)}_{len(mongodb_docs)}",
            "source": f"AD&D {metadata.get('edition', '')} - {metadata.get('book_type', '')}",
            "title": item.get("title", ""),
            "content": item.get("content", ""),
            "category": item.get("category", "General"),
            "tags": item.get("tags", []),
            "metadata": {
                "page": item.get("page", item.get("page_start", 0)),
                "extraction_method": item.get("extraction_method", ""),
                "confidence": item.get("extraction_confidence", 0),
                "word_count": item.get("word_count", 0),
                **metadata
            },
            "search_text": item.get("search_text", ""),
            "tables": item.get("tables", []),
            "created_at": datetime.now().isoformat()
        }
        mongodb_docs.append(doc)
    
    with open(output_paths["mongodb"], 'w', encoding='utf-8') as f:
        json.dump(mongodb_docs, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Saved MongoDB format to {output_paths['mongodb']}")
    
    # ChromaDB-ready format (for vector embeddings)
    chromadb_docs = []
    for i, item in enumerate(extracted_data):
        doc = {
            "id": f"{metadata.get('abbreviation', 'DOC')}_{i}",
            "document": item.get("content", ""),
            "metadata": {
                "title": item.get("title", ""),
                "category": item.get("category", ""),
                "tags": ",".join(item.get("tags", [])),
                "page": item.get("page", item.get("page_start", 0)),
                "source": f"AD&D {metadata.get('edition', '')} - {metadata.get('book_type', '')}",
                "confidence": item.get("extraction_confidence", 0)
            }
        }
        chromadb_docs.append(doc)
    
    with open(output_paths["chromadb"], 'w', encoding='utf-8') as f:
        json.dump(chromadb_docs, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Saved ChromaDB format to {output_paths['chromadb']}")
    
    # Individual Markdown files
    for i, item in enumerate(extracted_data):
        filename = f"section_{i:03d}_{item.get('title', 'untitled').replace(' ', '_')[:50]}.md"
        filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        
        markdown_path = output_paths["markdown"] / filename
        
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(f"# {item.get('title', 'Untitled')}\n\n")
            f.write(f"**Source:** {metadata.get('book_type', 'Unknown')}\n")
            f.write(f"**Page:** {item.get('page', item.get('page_start', 'Unknown'))}\n")
            f.write(f"**Category:** {item.get('category', 'General')}\n")
            f.write(f"**Tags:** {', '.join(item.get('tags', []))}\n\n")
            f.write("---\n\n")
            f.write(item.get("content", ""))
            
            # Add tables if present
            if item.get("tables"):
                f.write("\n\n## Tables\n\n")
                for j, table in enumerate(item["tables"]):
                    f.write(f"### Table {j+1}\n\n")
                    if table.get("headers"):
                        f.write("| " + " | ".join(table["headers"]) + " |\n")
                        f.write("| " + " | ".join(["---"] * len(table["headers"])) + " |\n")
                    
                    for row in table.get("rows", []):
                        f.write("| " + " | ".join(str(cell) for cell in row) + " |\n")
                    f.write("\n")

            if metrics.issues_found:
                print(f"\nIssues Found ({len(metrics.issues_found)}):")
                for issue in metrics.issues_found[:5]:
                    print(f"  - {issue}")
                if len(metrics.issues_found) > 5:
                    print(f"  ... and {len(metrics.issues_found) - 5} more (see report)")
            
            # Show sample extractions
            if metrics.sample_extractions:
                print(f"\nSample Extractions:")
                for i, sample in enumerate(metrics.sample_extractions[:2]):
                    print(f"\n  Sample {i+1} (Page {sample.get('page', '?')}, {sample.get('method', 'unknown')}):")
                    content = sample.get('content', '')[:150]
                    print(f"    {content}...")
                    if 'confidence' in sample:
                        print(f"    Confidence: {sample['confidence']:.1f}%")
            
            print(f"\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  {rec}")
            
            # Check if confidence meets minimum threshold
            if metrics.overall_confidence < args.min_confidence:
                print(f"\n❌ Confidence {metrics.overall_confidence:.1f}% is below minimum {args.min_confidence}%")
                
                response = input("Continue anyway? [y/N]: ").strip().lower()
                if response not in ['y', 'yes']:
                    print("Extraction cancelled. Consider:")
                    print("  - Using OCR method: --method ocr")
                    print("  - Lowering confidence threshold: --min-confidence 40")
                    print("  - Manual preprocessing of the PDF")
                    sys.exit(1)
            else:
                print(f"✅ Confidence acceptable ({metrics.overall_confidence:.1f}% >= {args.min_confidence}%)")
            
            # Use recommended method if auto
            if args.method == "auto":
                if metrics.recommended_method == "manual_review_needed":
                    print("\n⚠️ Automatic method selection failed - using text extraction")
                    method = "text"
                else:
                    method = metrics.recommended_method
                    print(f"Using recommended method: {method}")
            else:
                method = args.method
                
        except ImportError:
            logging.warning("Confidence testing not available - proceeding with basic detection")
            pdf_type = detect_pdf_type(args.pdf_path)
            method = "text" if pdf_type == "text" else "ocr"
        except Exception as e:
            logging.error(f"Confidence test failed: {e}")
            print("Proceeding with basic PDF type detection...")
            pdf_type = detect_pdf_type(args.pdf_path)
            method = "text" if pdf_type == "text" else "ocr"
    else:
        # No testing - use specified method or detect
        if args.method == "auto":
            pdf_type = detect_pdf_type(args.pdf_path)
            method = "text" if pdf_type == "text" else "ocr"
        else:
            method = args.method
    
    logging.info(f"Using extraction method: {method}")
    
    # Extract metadata
    metadata = extract_metadata_from_filename(args.pdf_path)
    logging.info(f"Book metadata: {metadata}")
    
    # Create output structure
    output_paths = create_output_structure(args.output, metadata)
    logging.info(f"Output directory: {output_paths['base']}")
    
    # Extract content
    if method == "text":
        extracted_data = process_with_text_extraction(args.pdf_path, output_paths, metadata)
    else:
        extracted_data = process_with_ocr_extraction(args.pdf_path, output_paths, metadata)
    
    if not extracted_data:
        logging.error("No data extracted. Check the logs for errors.")
        
        # If we have confidence test results, show them again
        if args.test_first:
            print("\nRefer to the confidence test results above for troubleshooting.")
        
        sys.exit(1)
    
    # Enhance data
    enhanced_data = enhance_extracted_data(extracted_data)
    
    # Save outputs
    save_outputs(enhanced_data, output_paths, metadata)
    
    # Summary
    logging.info(f"Extraction complete!")
    logging.info(f"Extracted {len(enhanced_data)} sections")
    logging.info(f"Output saved to: {output_paths['base']}")
    
    # Print summary statistics
    categories = {}
    total_words = 0
    confidence_scores = []
    low_confidence_sections = 0
    
    for item in enhanced_data:
        cat = item.get("category", "Unknown")
        categories[cat] = categories.get(cat, 0) + 1
        total_words += item.get("word_count", 0)
        
        if "extraction_confidence" in item:
            conf = item["extraction_confidence"]
            confidence_scores.append(conf)
            if conf < 70:
                low_confidence_sections += 1
    
    print("\n=== EXTRACTION SUMMARY ===")
    print(f"Total sections: {len(enhanced_data)}")
    print(f"Total words: {total_words:,}")
    
    if confidence_scores:
        avg_conf = sum(confidence_scores) / len(confidence_scores)
        print(f"Average confidence: {avg_conf:.1f}%")
        if low_confidence_sections > 0:
            print(f"Low confidence sections: {low_confidence_sections} ({low_confidence_sections/len(enhanced_data)*100:.1f}%)")
    
    print(f"\nSections by category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")
    
    print(f"\nFiles created:")
    print(f"  MongoDB ready: {output_paths['mongodb']}")
    print(f"  ChromaDB ready: {output_paths['chromadb']}")
    print(f"  Individual markdown: {output_paths['markdown']}")
    
    if args.test_first:
        print(f"  Confidence report: {args.output / 'confidence_test' / 'confidence_report.json'}")
    
    # Quality recommendations
    print(f"\n=== QUALITY RECOMMENDATIONS ===")
    
    if confidence_scores:
        if avg_conf >= 80:
            print("✅ High quality extraction - ready for database import")
        elif avg_conf >= 70:
            print("⚠️ Good quality - review low confidence sections")
        else:
            print("❌ Lower quality - manual review recommended")
    
    if low_confidence_sections > len(enhanced_data) * 0.2:
        print(f"⚠️ {low_confidence_sections} sections need review (>20% of total)")
        print("   Consider manual verification for critical rules")
    
    # Database import suggestions
    print(f"\n=== NEXT STEPS ===")
    print("1. Review the extraction quality:")
    print(f"   - Check markdown files in: {output_paths['markdown']}")
    print("   - Focus on low confidence sections")
    
    print("2. Import to MongoDB:")
    print(f"   mongoimport --db rpg_data --collection add_dmg --file {output_paths['mongodb']} --jsonArray")
    
    print("3. Set up semantic search:")
    print(f"   - Use {output_paths['chromadb']} for ChromaDB")
    print("   - Consider creating embeddings for better search")
    
    if method == "ocr" and avg_conf < 80:
        print("4. OCR Quality Improvement:")
        print("   - Consider preprocessing the PDF (enhance contrast, resolution)")
        print("   - Manual correction of critical sections may be needed")

if __name__ == "__main__":
    from datetime import datetime
    main()