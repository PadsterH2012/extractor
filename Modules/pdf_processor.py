#!/usr/bin/env python3
"""
Multi-Game PDF Processor Module
Enhanced PDF extraction with game-aware processing
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import fitz  # PyMuPDF
import pdfplumber

from .ai_game_detector import AIGameDetector
from .ai_categorizer import AICategorizer

class MultiGamePDFProcessor:
    """Enhanced PDF processor with AI-powered multi-game support"""

    def __init__(self, verbose: bool = False, debug: bool = False, ai_config: Dict[str, Any] = None):
        self.verbose = verbose
        self.debug = debug
        self.ai_config = ai_config or {"provider": "mock"}
        self.setup_logging()

        # Initialize AI components with full configuration
        self.game_detector = AIGameDetector(ai_config=self.ai_config, debug=debug)
        self.categorizer = AICategorizer(ai_config=self.ai_config, debug=debug)

        self.logger.info(f"AI-Powered Multi-Game PDF Processor initialized (Provider: {self.ai_config['provider']})")

    def setup_logging(self):
        """Setup logging configuration"""
        level = logging.DEBUG if self.verbose else logging.INFO

        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger(__name__)

    def extract_pdf(self, pdf_path: Path, force_game_type: Optional[str] = None,
                   force_edition: Optional[str] = None, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract content from a single PDF with game-aware processing

        Args:
            pdf_path: Path to PDF file
            force_game_type: Override game type detection
            force_edition: Override edition detection
            content_type: Type of content ('source_material' or 'novel')

        Returns:
            Extraction data with game metadata
        """
        self.logger.info(f"Extracting: {pdf_path.name}")

        # Validate PDF
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            raise Exception(f"Cannot open PDF: {e}")

        # Use AI to analyze and detect game metadata
        if force_game_type or force_edition:
            # If forced, create metadata manually
            game_metadata = self._create_forced_metadata(pdf_path, force_game_type, force_edition)
        else:
            # Use AI detection
            game_metadata = self.game_detector.analyze_game_metadata(pdf_path)
        
        # Add content type to metadata
        if content_type:
            game_metadata['content_type'] = content_type
        else:
            game_metadata['content_type'] = 'source_material'  # Default

        # Log detected information
        self.logger.info(f"🎮 Game: {game_metadata['game_type']}")
        self.logger.info(f"📖 Edition: {game_metadata['edition']}")
        self.logger.info(f"📚 Book: {game_metadata.get('book_type', 'Unknown')}")
        self.logger.info(f"📑 Content Type: {game_metadata['content_type']}")
        self.logger.info(f"🏷️  Collection: {game_metadata['collection_name']}")

        # Extract content with game context
        extracted_sections = self._extract_sections(doc, game_metadata)

        doc.close()

        # Build complete metadata
        complete_metadata = self._build_complete_metadata(pdf_path, game_metadata)

        self.logger.info(f"Extracted {len(extracted_sections)} sections")

        return {
            "metadata": complete_metadata,
            "sections": extracted_sections,
            "extraction_summary": self._build_extraction_summary(
                extracted_sections, game_metadata
            )
        }

    def _extract_sample_content(self, doc, max_pages: int = 3, max_chars: int = 3000) -> str:
        """Extract sample content for game type detection"""
        sample_content = ""

        for page_num in range(min(max_pages, len(doc))):
            page = doc[page_num]
            page_text = page.get_text()
            sample_content += page_text[:max_chars // max_pages]

            if len(sample_content) >= max_chars:
                break

        return sample_content[:max_chars]

    def _extract_sections(self, doc, game_metadata: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract sections with game-aware processing"""
        sections = []
        total_tables = 0

        for page_num in range(len(doc)):
            self.logger.debug(f"Processing page {page_num + 1}/{len(doc)}")

            page = doc[page_num]
            text = page.get_text()

            if text.strip():
                # Handle multi-column layout
                blocks = page.get_text("dict")
                is_multi_column = self._detect_multi_column_layout(blocks, page.rect.width)

                if is_multi_column:
                    text = self._process_multi_column_text(blocks, page.rect.width)

                # Extract tables
                tables = self._extract_tables_from_page(doc.name, page_num)
                total_tables += len(tables)

                # Generate title from first line
                first_line = text.split('\n')[0].strip()[:100]
                title = first_line if len(first_line) > 10 else f"Page {page_num + 1}"

                # AI-powered categorization
                categorization_result = self.categorizer.categorize_content(text, game_metadata)
                category = categorization_result["primary_category"]

                # Create section with game metadata
                section = {
                    "page": page_num + 1,
                    "title": title,
                    "content": text.strip(),
                    "word_count": len(text.split()),
                    "category": category,
                    "tables": tables,
                    "is_multi_column": is_multi_column,
                    "extraction_method": "text_with_tables",
                    "extraction_confidence": 95.0,
                    "game_type": game_metadata["game_type"],
                    "edition": game_metadata["edition"],
                    "book": game_metadata.get("book_type", "Unknown")
                }

                sections.append(section)

        return sections

    def _create_forced_metadata(self, pdf_path: Path, force_game_type: Optional[str],
                               force_edition: Optional[str]) -> Dict[str, Any]:
        """Create metadata when game type or edition is forced"""

        # Use AI detection but override specific fields
        ai_metadata = self.game_detector.analyze_game_metadata(pdf_path)

        if force_game_type:
            ai_metadata["game_type"] = force_game_type
            ai_metadata["collection_prefix"] = self._generate_collection_prefix(force_game_type)

        if force_edition:
            ai_metadata["edition"] = force_edition

        # Regenerate collection name with forced values
        ai_metadata["collection_name"] = self._generate_collection_name(ai_metadata)

        return ai_metadata

    def _generate_collection_prefix(self, game_type: str) -> str:
        """Generate collection prefix from game type"""
        prefix_map = {
            "D&D": "dnd",
            "Pathfinder": "pf",
            "Call of Cthulhu": "coc",
            "Vampire": "vtm",
            "Werewolf": "wta",
            "Cyberpunk": "cp",
            "Shadowrun": "sr"
        }
        return prefix_map.get(game_type, game_type.lower().replace(" ", "")[:5])

    def _generate_collection_name(self, metadata: Dict[str, Any]) -> str:
        """Generate collection name from metadata"""
        prefix = metadata.get("collection_prefix", "unknown")
        edition = metadata["edition"].replace(".", "").lower()
        book = metadata["book_type"].lower()
        return f"{prefix}_{edition}_{book}"

    def _detect_multi_column_layout(self, blocks: Dict, page_width: float) -> bool:
        """Detect multi-column layout"""
        if not blocks or not blocks.get("blocks"):
            return False

        text_blocks = []
        for block in blocks["blocks"]:
            if block.get("type") == 0:  # Text block
                bbox = block.get("bbox", [0, 0, 0, 0])
                x0, y0, x1, y1 = bbox
                if x1 - x0 > 50:  # Reasonable width
                    text_blocks.append({
                        "x_center": (x0 + x1) / 2,
                        "width": x1 - x0
                    })

        if len(text_blocks) < 2:
            return False

        # Check for distinct column positions
        centers = [block["x_center"] for block in text_blocks]
        centers.sort()

        # Look for gaps indicating columns
        for i in range(1, len(centers)):
            gap = centers[i] - centers[i-1]
            if gap > page_width * 0.1:  # 10% of page width
                return True

        return False

    def _process_multi_column_text(self, blocks: Dict, page_width: float) -> str:
        """Process multi-column text in correct reading order"""
        if not blocks or not blocks.get("blocks"):
            return ""

        text_blocks = []
        for block in blocks["blocks"]:
            if block.get("type") == 0:  # Text block
                bbox = block.get("bbox", [0, 0, 0, 0])
                x0, y0, x1, y1 = bbox

                # Determine column (left vs right)
                x_center = (x0 + x1) / 2
                column = 0 if x_center < page_width / 2 else 1

                text_blocks.append({
                    "text": self._extract_block_text(block),
                    "y_pos": y0,
                    "column": column
                })

        # Sort by column, then by y position
        text_blocks.sort(key=lambda b: (b["column"], b["y_pos"]))

        return "\n".join(block["text"] for block in text_blocks if block["text"].strip())

    def _extract_block_text(self, block: Dict) -> str:
        """Extract text from a block"""
        text_parts = []
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text_parts.append(span.get("text", ""))
        return " ".join(text_parts)

    def _extract_tables_from_page(self, pdf_path: str, page_num: int) -> List[Dict]:
        """Extract tables from a specific page"""
        tables = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    page_tables = page.extract_tables()

                    for i, table in enumerate(page_tables):
                        if table and len(table) > 1:  # Valid table
                            # Clean and structure table data
                            cleaned_table = []
                            for row in table:
                                if row and any(cell and str(cell).strip() for cell in row):
                                    cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                                    cleaned_table.append(cleaned_row)

                            if len(cleaned_table) > 1:  # Has header + data
                                tables.append({
                                    "table_id": f"page_{page_num + 1}_table_{i + 1}",
                                    "headers": cleaned_table[0],
                                    "rows": cleaned_table[1:],
                                    "row_count": len(cleaned_table) - 1,
                                    "column_count": len(cleaned_table[0]),
                                    "extraction_method": "pdfplumber"
                                })

        except Exception as e:
            self.logger.warning(f"Table extraction failed for page {page_num + 1}: {e}")

        return tables

    def _build_complete_metadata(self, pdf_path: Path, game_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Build complete metadata including file and AI-detected game information"""

        return {
            "original_filename": pdf_path.name,
            "file_size": pdf_path.stat().st_size,
            "source_type": "pdf_extraction",
            "processing_date": datetime.now().isoformat(),

            # AI-detected game metadata
            "game_type": game_metadata["game_type"],
            "game_full_name": game_metadata.get("game_full_name", game_metadata["game_type"]),
            "edition": game_metadata["edition"],
            "book": game_metadata.get("book_type", "Core"),
            "book_full_name": game_metadata.get("book_full_name", pdf_path.stem),
            "collection_name": game_metadata["collection_name"],
            "publisher": game_metadata.get("publisher", "Unknown"),
            "publication_year": game_metadata.get("publication_year"),

            # Source information
            "source": f"{game_metadata.get('game_full_name', game_metadata['game_type'])} {game_metadata['edition']} Edition - {game_metadata.get('book_full_name', 'Unknown Book')}",

            # AI analysis results
            "core_mechanics": game_metadata.get("core_mechanics", []),
            "detection_confidence": game_metadata.get("confidence", 0.5),
            "detection_method": game_metadata.get("detection_method", "ai_analysis"),
            "ai_reasoning": game_metadata.get("reasoning", ""),
            "detected_categories": game_metadata.get("detected_categories", []),
            "language": game_metadata.get("language", "English")
        }

    def _build_extraction_summary(self, sections: List[Dict], game_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Build extraction summary with game context"""

        total_words = sum(s["word_count"] for s in sections)
        total_tables = sum(len(s["tables"]) for s in sections)

        # Category distribution
        categories = {}
        for section in sections:
            category = section["category"]
            categories[category] = categories.get(category, 0) + 1

        return {
            "total_pages": len(sections),
            "total_words": total_words,
            "total_tables": total_tables,
            "extraction_timestamp": datetime.now().isoformat(),
            "content_type": game_metadata.get("content_type", "source_material"),
            "game_type": game_metadata["game_type"],
            "edition": game_metadata["edition"],
            "book": game_metadata.get("book_type", "Unknown"),
            "collection_name": game_metadata["collection_name"],
            "category_distribution": categories,
            "average_words_per_page": total_words // len(sections) if sections else 0
        }

    def save_extraction(self, extraction_data: Dict, output_dir: Path) -> Dict[str, Path]:
        """Save extraction in multiple formats"""

        output_dir.mkdir(parents=True, exist_ok=True)
        metadata = extraction_data["metadata"]

        # Generate base filename from collection name
        base_name = metadata["collection_name"]

        # Save ChromaDB-ready JSON
        chromadb_data = self._prepare_chromadb_format(extraction_data)
        chromadb_file = output_dir / f"{base_name}_chromadb.json"

        with open(chromadb_file, 'w', encoding='utf-8') as f:
            json.dump(chromadb_data, f, indent=2, ensure_ascii=False)

        # Save raw extraction data
        raw_file = output_dir / f"{base_name}_raw.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(extraction_data, f, indent=2, ensure_ascii=False)

        # Save summary
        summary_file = output_dir / f"{base_name}_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(extraction_data["extraction_summary"], f, indent=2, ensure_ascii=False)

        return {
            "chromadb": chromadb_file,
            "raw": raw_file,
            "summary": summary_file
        }

    def _prepare_chromadb_format(self, extraction_data: Dict) -> List[Dict]:
        """Prepare data in ChromaDB format"""

        metadata = extraction_data["metadata"]
        sections = extraction_data["sections"]

        chromadb_docs = []

        for section in sections:
            doc_id = f"{metadata['collection_name']}_page_{section['page']:03d}"

            # Enhanced metadata for ChromaDB
            doc_metadata = {
                "title": section["title"],
                "page": section["page"],
                "category": section["category"],
                "word_count": section["word_count"],
                "has_tables": len(section["tables"]) > 0,
                "table_count": len(section["tables"]),
                "is_multi_column": section["is_multi_column"],

                # Game metadata
                "game_type": metadata["game_type"],
                "edition": metadata["edition"],
                "book": metadata["book"],
                "source": metadata["source"],
                "collection_name": metadata["collection_name"],

                # Processing metadata
                "extraction_method": section["extraction_method"],
                "extraction_confidence": section["extraction_confidence"],
                "processing_date": metadata["processing_date"]
            }

            # Add table information if present
            if section["tables"]:
                doc_metadata["tables"] = section["tables"]

            chromadb_docs.append({
                "id": doc_id,
                "document": section["content"],
                "metadata": doc_metadata
            })

        return chromadb_docs

    def batch_extract(self, pdf_directory: Path, force_game_type: Optional[str] = None,
                     force_edition: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract multiple PDFs from a directory

        Args:
            pdf_directory: Directory containing PDF files
            force_game_type: Override game type for all PDFs
            force_edition: Override edition for all PDFs

        Returns:
            List of extraction results
        """
        if not pdf_directory.is_dir():
            raise ValueError(f"Directory not found: {pdf_directory}")

        pdf_files = list(pdf_directory.glob("*.pdf"))
        if not pdf_files:
            raise ValueError(f"No PDF files found in: {pdf_directory}")

        self.logger.info(f"Batch processing {len(pdf_files)} PDFs")

        results = []
        for pdf_file in pdf_files:
            try:
                self.logger.info(f"Processing: {pdf_file.name}")
                extraction_data = self.extract_pdf(pdf_file, force_game_type, force_edition)
                results.append({
                    "file": pdf_file,
                    "success": True,
                    "data": extraction_data
                })
            except Exception as e:
                self.logger.error(f"Failed to process {pdf_file.name}: {e}")
                results.append({
                    "file": pdf_file,
                    "success": False,
                    "error": str(e)
                })

        successful = sum(1 for r in results if r["success"])
        self.logger.info(f"Batch complete: {successful}/{len(results)} successful")

        return results
