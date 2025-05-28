#!/usr/bin/env python3
"""
Multi-Game PDF Processor Module
Enhanced PDF extraction with game-aware processing
"""

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import fitz  # PyMuPDF
import pdfplumber

from .ai_game_detector import AIGameDetector
from .ai_categorizer import AICategorizer
from .text_quality_enhancer import TextQualityEnhancer

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

        # Initialize text quality enhancer
        self.text_enhancer = TextQualityEnhancer(self.ai_config)

        # Text quality settings
        self.enable_text_enhancement = self.ai_config.get('enable_text_enhancement', True)
        self.aggressive_cleanup = self.ai_config.get('aggressive_cleanup', False)

        self.logger.info(f"AI-Powered Multi-Game PDF Processor initialized (Provider: {self.ai_config['provider']})")
        if self.enable_text_enhancement:
            self.logger.info("✨ Text quality enhancement enabled")

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

        # Extract ISBN from PDF metadata and content
        isbn_data = self._extract_isbn(doc, pdf_path)

        # For novels, check ISBN blacklist to prevent duplicate processing
        if game_metadata['content_type'] == 'novel' and isbn_data.get('isbn'):
            blacklist_result = self._check_isbn_blacklist(isbn_data['isbn'])
            if blacklist_result['is_duplicate']:
                doc.close()
                raise Exception(f"ISBN_DUPLICATE: This novel has already been processed on {blacklist_result['extraction_date']}. "
                              f"Extracted {blacklist_result['total_patterns']} patterns from {blacklist_result['characters_processed']} characters.")

        # Log detected information
        self.logger.info(f"🎮 Game: {game_metadata['game_type']}")
        self.logger.info(f"📖 Edition: {game_metadata['edition']}")
        self.logger.info(f"📚 Book: {game_metadata.get('book_type', 'Unknown')}")
        self.logger.info(f"📑 Content Type: {game_metadata['content_type']}")
        self.logger.info(f"🏷️  Collection: {game_metadata['collection_name']}")
        if isbn_data.get('isbn'):
            self.logger.info(f"📚 ISBN: {isbn_data['isbn']}")

        # Extract content with game context - different workflows for novels vs source material
        if game_metadata['content_type'] == 'novel':
            # MEMORY OPTIMIZATION: Disable text enhancement for novels to reduce memory usage
            original_text_enhancement = self.enable_text_enhancement
            self.enable_text_enhancement = False
            self.logger.info("🧠 Memory optimization: Disabled text enhancement for novel processing")

            try:
                # Extract novel content in narrative-focused format
                novel_data = self._extract_novel_content(doc, game_metadata)

                # For novels, perform character identification after content extraction
                character_results = self._identify_novel_characters(novel_data['raw_sections'], game_metadata)

                # Add character information to novel data structure
                novel_data['character_identification'] = character_results

                # Convert to sections format for compatibility with existing pipeline
                extracted_sections = novel_data['raw_sections']

                # Store novel-specific data in metadata for MongoDB
                game_metadata['novel_data'] = {
                    'narrative_structure': novel_data['narrative_structure'],
                    'extraction_metadata': novel_data['extraction_metadata'],
                    'character_identification': character_results
                }

            finally:
                # Restore original text enhancement setting
                self.enable_text_enhancement = original_text_enhancement

        else:
            extracted_sections = self._extract_sections(doc, game_metadata)

        doc.close()

        # Build complete metadata with ISBN
        complete_metadata = self._build_complete_metadata(pdf_path, game_metadata, isbn_data)

        self.logger.info(f"Extracted {len(extracted_sections)} sections")

        # For novels, add ISBN to blacklist after successful extraction
        if game_metadata['content_type'] == 'novel' and isbn_data.get('isbn'):
            self._add_to_isbn_blacklist(isbn_data['isbn'], complete_metadata, extracted_sections)

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

                # Apply text quality enhancement if enabled
                original_text = text
                text_quality_result = None
                if self.enable_text_enhancement and text.strip():
                    text_quality_result = self.text_enhancer.enhance_text_quality(
                        text, aggressive=self.aggressive_cleanup
                    )
                    text = text_quality_result.cleaned_text

                    if self.debug and text_quality_result:
                        quality_summary = self.text_enhancer.get_quality_summary(text_quality_result)
                        self.logger.debug(f"Page {page_num + 1} quality: {quality_summary['before']['score']}% → {quality_summary['after']['score']}% ({quality_summary['before']['grade']} → {quality_summary['after']['grade']})")

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

                # Add text quality metadata if enhancement was applied
                if text_quality_result:
                    quality_summary = self.text_enhancer.get_quality_summary(text_quality_result)
                    section.update({
                        "text_quality_enhanced": True,
                        "text_quality_before": quality_summary["before"],
                        "text_quality_after": quality_summary["after"],
                        "text_quality_improvement": quality_summary["improvement"],
                        "corrections_made": len(text_quality_result.corrections_made),
                        "cleanup_aggressive": self.aggressive_cleanup
                    })
                else:
                    section["text_quality_enhanced"] = False

                sections.append(section)

        return sections

    def _extract_novel_content(self, doc, game_metadata: Dict[str, str]) -> Dict[str, Any]:
        """Extract content from novels with narrative-focused processing"""
        self.logger.info("🔖 Processing novel content with narrative extraction")

        raw_sections = []
        total_tables = 0
        total_text = ""
        chapters_detected = []

        for page_num in range(len(doc)):
            self.logger.debug(f"Processing novel page {page_num + 1}/{len(doc)}")

            page = doc[page_num]
            text = page.get_text()

            if text.strip():
                # For novels, we focus on narrative flow rather than structured content
                # Handle multi-column layout (less common in novels but possible)
                blocks = page.get_text("dict")
                is_multi_column = self._detect_multi_column_layout(blocks, page.rect.width)

                if is_multi_column:
                    text = self._process_multi_column_text(blocks, page.rect.width)

                # Apply text quality enhancement if enabled
                text_quality_result = None
                if self.enable_text_enhancement and text.strip():
                    text_quality_result = self.text_enhancer.enhance_text_quality(
                        text,
                        aggressive=self.aggressive_cleanup
                    )
                    if text_quality_result and text_quality_result.cleaned_text:
                        text = text_quality_result.cleaned_text

                # Extract tables (less common in novels but still possible)
                tables = self._extract_tables_from_page(doc.name, page_num)
                total_tables += len(tables)

                # Generate title from first line or chapter detection
                first_line = text.split('\n')[0].strip()[:100]
                title = self._detect_novel_section_title(text, first_line, page_num)

                # Track chapter detection for narrative structure
                if any(marker in title.lower() for marker in ['chapter', 'part', 'book', 'prologue', 'epilogue']):
                    chapters_detected.append({
                        "title": title,
                        "page": page_num + 1,
                        "word_count": len(text.split())
                    })

                # Novel-specific categorization (different from RPG source material)
                category = self._categorize_novel_content(text, game_metadata)

                section = {
                    "page": page_num + 1,
                    "title": title,
                    "content": text,
                    "word_count": len(text.split()) if text else 0,
                    "tables": tables,
                    "has_tables": len(tables) > 0,
                    "table_count": len(tables),
                    "is_multi_column": is_multi_column,
                    "category": category,
                    "extraction_method": "novel_narrative_extraction",
                    "extraction_confidence": 0.85,  # Novel extraction is generally more straightforward
                    "content_type": "novel",
                    "narrative_elements": self._detect_narrative_elements(text)
                }

                # Add text quality information if enhancement was used
                if text_quality_result:
                    quality_summary = self.text_enhancer.get_quality_summary(text_quality_result)
                    section.update({
                        "text_quality_enhanced": True,
                        "text_quality_before": quality_summary["before"],
                        "text_quality_after": quality_summary["after"],
                        "text_quality_improvement": quality_summary["improvement"],
                        "corrections_made": len(text_quality_result.corrections_made),
                        "cleanup_aggressive": self.aggressive_cleanup
                    })
                else:
                    section["text_quality_enhanced"] = False

                raw_sections.append(section)
                total_text += text + "\n\n"

        # Build novel-specific data structure
        novel_data = {
            "content_type": "novel",
            "raw_sections": raw_sections,  # Keep for character identification compatibility
            "narrative_structure": {
                "total_pages": len(raw_sections),
                "total_words": len(total_text.split()),
                "total_characters": len(total_text),
                "chapters_detected": len(chapters_detected),
                "chapter_list": chapters_detected,
                "estimated_reading_time": len(total_text.split()) // 250,  # ~250 words per minute
                "narrative_flow": "continuous",
                "has_dialogue": any(section.get("narrative_elements", {}).get("has_dialogue", False) for section in raw_sections),
                "has_action": any(section.get("narrative_elements", {}).get("has_action", False) for section in raw_sections),
                "has_description": any(section.get("narrative_elements", {}).get("has_description", False) for section in raw_sections)
            },
            "extraction_metadata": {
                "title": game_metadata.get("book_title", "Unknown Novel"),
                "author": game_metadata.get("author", "Unknown Author"),
                "isbn": game_metadata.get("isbn", None),
                "extraction_date": self._get_current_timestamp(),
                "extraction_method": "novel_narrative_extraction",
                "total_tables": total_tables
            }
        }

        self.logger.info(f"📖 Novel extraction complete: {len(raw_sections)} sections, {total_tables} tables")
        self.logger.info(f"📚 Novel structure: {len(chapters_detected)} chapters, {len(total_text.split()):,} words")

        return novel_data

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()

    def _detect_novel_section_title(self, text: str, first_line: str, page_num: int) -> str:
        """Detect section titles in novels (chapters, parts, etc.)"""

        # Look for chapter markers
        chapter_patterns = [
            r'^(Chapter\s+\d+)',
            r'^(CHAPTER\s+\d+)',
            r'^(Part\s+\d+)',
            r'^(PART\s+\d+)',
            r'^(\d+\.)',
            r'^([IVX]+\.)',  # Roman numerals
        ]

        for pattern in chapter_patterns:
            match = re.match(pattern, first_line.strip(), re.IGNORECASE)
            if match:
                return match.group(1)

        # If no chapter marker, use first meaningful line
        if len(first_line) > 10:
            return first_line
        else:
            return f"Page {page_num + 1}"

    def _categorize_novel_content(self, text: str, game_metadata: Dict[str, Any]) -> str:
        """Categorize novel content (different from RPG source material)"""

        text_lower = text.lower()

        # Novel-specific categories
        if any(word in text_lower for word in ['chapter', 'part', 'book', 'prologue', 'epilogue']):
            return "Chapter/Section"
        elif any(word in text_lower for word in ['dialogue', '"', "'", 'said', 'asked', 'replied']):
            return "Dialogue"
        elif any(word in text_lower for word in ['description', 'looked', 'appeared', 'seemed', 'was']):
            return "Description"
        elif any(word in text_lower for word in ['action', 'moved', 'ran', 'walked', 'fought']):
            return "Action"
        elif any(word in text_lower for word in ['thought', 'remembered', 'wondered', 'realized']):
            return "Internal Monologue"
        else:
            return "Narrative"

    def _detect_narrative_elements(self, text: str) -> Dict[str, Any]:
        """Detect narrative elements in novel text for future pattern extraction"""

        text_lower = text.lower()

        # Count different narrative elements (foundation for future pattern extraction)
        elements = {
            "dialogue_markers": len(re.findall(r'"[^"]*"', text)),
            "character_mentions": len(re.findall(r'\b[A-Z][a-z]+\b', text)),  # Proper nouns (potential characters)
            "action_verbs": len([word for word in text_lower.split() if word in ['ran', 'walked', 'moved', 'jumped', 'fought', 'attacked']]),
            "descriptive_adjectives": len([word for word in text_lower.split() if word in ['beautiful', 'dark', 'tall', 'strong', 'mysterious', 'ancient']]),
            "emotional_words": len([word for word in text_lower.split() if word in ['angry', 'sad', 'happy', 'afraid', 'excited', 'worried']]),
            "has_dialogue": '"' in text,
            "has_action": any(word in text_lower for word in ['ran', 'walked', 'moved', 'fought']),
            "has_description": any(word in text_lower for word in ['looked', 'appeared', 'seemed', 'beautiful', 'dark'])
        }

        return elements

    def _identify_novel_characters(self, sections: List[Dict[str, Any]], game_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Identify characters in novel content using two-pass AI analysis with progress updates"""

        try:
            # Import novel element extractor
            from .novel_element_extractor import NovelElementExtractor

            # Get AI configuration from the processor's config
            ai_config = getattr(self, 'ai_config', {"provider": "mock"})

            # Initialize novel element extractor
            element_extractor = NovelElementExtractor(ai_config=ai_config, debug=self.debug)

            # Add progress callback for real-time updates
            element_extractor.progress_callback = self._character_progress_callback

            # Perform novel element extraction (characters + locations)
            self.logger.info("🎭 Starting novel element extraction")
            extraction_results = element_extractor.identify_characters(sections, game_metadata)

            # Log results
            total_characters = extraction_results.get('total_characters', 0)
            self.logger.info(f"🎭 Novel element extraction complete: {total_characters} characters identified")

            if self.debug and total_characters > 0:
                character_names = [char['name'] for char in extraction_results.get('characters', [])]
                print(f"📝 Characters found: {', '.join(character_names)}")

            return extraction_results

        except Exception as e:
            self.logger.error(f"Character identification failed: {e}")
            if self.debug:
                print(f"❌ Character identification error: {e}")

            # Return empty result on failure
            return {
                "characters": [],
                "total_characters": 0,
                "processing_stages": {
                    "error": f"Character identification failed: {str(e)}"
                },
                "metadata": {
                    "novel_title": game_metadata.get("book_title", "Unknown"),
                    "author": game_metadata.get("author", "Unknown"),
                    "error": "Character identification system unavailable"
                }
            }

    def _character_progress_callback(self, stage: str, status: str, details: Dict[str, Any]):
        """
        Progress callback for character identification stages

        Args:
            stage: Current stage (discovery, filtering, analysis)
            status: Status (active, completed, error)
            details: Stage-specific progress details
        """

        # Log progress with detailed information
        if stage == 'discovery':
            if 'current_chunk' in details:
                chunk_num = details['current_chunk']
                total_chunks = details['total_chunks']
                candidates = details.get('candidates_found', 0)
                self.logger.info(f"📖 Discovery: Processing chunk {chunk_num}/{total_chunks} - {candidates} candidates found")

        elif stage == 'filtering':
            if 'current_candidate' in details:
                processed = details.get('candidates_processed', 0)
                total = details.get('candidates_to_filter', 0)
                filtered = details.get('candidates_filtered', 0)
                ratio = details.get('filter_ratio', 0) * 100
                self.logger.info(f"🔍 Filtering: {processed}/{total} processed - {filtered} passed ({ratio:.1f}%)")

        elif stage == 'analysis':
            if 'current_character' in details:
                analyzed = details.get('candidates_analyzed', 0)
                total = details.get('candidates_to_analyze', 0)
                confirmed = details.get('characters_confirmed', 0)
                character = details.get('current_character', 'Unknown')

                # Handle batch processing information
                if 'batch_number' in details:
                    batch_num = details.get('batch_number', 0)
                    batch_size = details.get('batch_size', 0)
                    self.logger.info(f"🎯 Batch Analysis: Batch {batch_num} ({batch_size} characters) - {confirmed} confirmed total")
                else:
                    self.logger.info(f"🎯 Analysis: {analyzed}/{total} - {confirmed} confirmed - Current: {character}")

        # If debug mode, also print to console for immediate feedback
        if self.debug:
            if stage == 'discovery' and 'current_chunk' in details:
                print(f"🔄 Processing chunk {details['current_chunk']}/{details['total_chunks']} ({details.get('candidates_found', 0)} candidates)")
            elif stage == 'filtering' and status == 'completed':
                print(f"🔍 Filtering complete: {details.get('candidates_filtered', 0)} candidates passed")
            elif stage == 'analysis' and 'current_character' in details:
                if 'batch_number' in details:
                    batch_num = details.get('batch_number', 0)
                    batch_size = details.get('batch_size', 0)
                    print(f"🎯 Batch {batch_num}: Analyzing {batch_size} characters together")
                else:
                    print(f"🎯 Analyzing: {details.get('current_character', 'Unknown')}")
            elif status == 'completed':
                if stage == 'analysis' and 'total_batches' in details:
                    total_batches = details.get('total_batches', 0)
                    print(f"✅ Batch analysis completed: {total_batches} batches processed")
                else:
                    print(f"✅ {stage.title()} stage completed")

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
        edition = metadata.get("edition", "unknown")
        book = metadata.get("book_type", "core")
        content_type = metadata.get("content_type", "source_material")

        # Handle None values and clean up strings
        if edition is None or edition.lower() in ["unknown", "n/a", "none"]:
            edition = "unknown"
        else:
            edition = str(edition).replace(".", "").lower()

        if book is None:
            book = "core"
        else:
            book = str(book).lower()

        # Special handling for novels - they don't have meaningful editions
        if content_type == "novel":
            # For novels, use a simpler naming scheme: prefix_novel
            collection_name = f"{prefix}_novel"
            if self.debug:
                print(f"🔧 PDF Processor novel collection name: {collection_name} (prefix: {prefix})")
            return collection_name
        else:
            # For source material, use the traditional scheme
            collection_name = f"{prefix}_{edition}_{book}"
            if self.debug:
                print(f"🔧 PDF Processor source material collection name: {collection_name}")
            return collection_name

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

    def _build_complete_metadata(self, pdf_path: Path, game_metadata: Dict[str, Any], isbn_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Build complete metadata including file and AI-detected game information"""

        metadata = {
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

        # Add ISBN information if available
        if isbn_data:
            if isbn_data.get("isbn"):
                metadata["isbn"] = isbn_data["isbn"]
            if isbn_data.get("isbn_10"):
                metadata["isbn_10"] = isbn_data["isbn_10"]
            if isbn_data.get("isbn_13"):
                metadata["isbn_13"] = isbn_data["isbn_13"]
            if isbn_data.get("source"):
                metadata["isbn_source"] = isbn_data["source"]

        return metadata

    def _check_isbn_blacklist(self, isbn: str) -> Dict[str, Any]:
        """
        Check if an ISBN is in the blacklist (already processed)

        Args:
            isbn: ISBN number to check

        Returns:
            Dictionary with blacklist check results
        """
        try:
            # Import MongoDB manager here to avoid circular imports
            from .mongodb_manager import MongoDBManager

            mongodb_manager = MongoDBManager(debug=self.debug)
            if not mongodb_manager.connected:
                # If MongoDB is not available, allow processing
                return {
                    'is_duplicate': False,
                    'error': 'MongoDB not available for blacklist checking'
                }

            # Check blacklist collection
            blacklist_collection = mongodb_manager.database['rpger.extraction.blacklist']
            existing_entry = blacklist_collection.find_one({'isbn': isbn})

            if existing_entry:
                return {
                    'is_duplicate': True,
                    'extraction_date': existing_entry.get('extraction_date', 'Unknown'),
                    'total_patterns': existing_entry.get('total_patterns', 0),
                    'characters_processed': existing_entry.get('characters_processed', 0),
                    'title': existing_entry.get('title', 'Unknown'),
                    'existing_entry': existing_entry
                }
            else:
                return {
                    'is_duplicate': False,
                    'message': 'ISBN not found in blacklist - safe to process'
                }

        except Exception as e:
            # If there's an error checking the blacklist, log it but allow processing
            if self.debug:
                print(f"⚠️  Error checking ISBN blacklist: {e}")
            return {
                'is_duplicate': False,
                'error': f'Blacklist check failed: {str(e)}'
            }

    def _add_to_isbn_blacklist(self, isbn: str, metadata: Dict[str, Any], sections: List[Dict[str, Any]]) -> bool:
        """
        Add an ISBN to the blacklist after successful novel processing

        Args:
            isbn: ISBN number to add
            metadata: Complete extraction metadata
            sections: Extracted sections

        Returns:
            True if successfully added, False otherwise
        """
        try:
            # Import MongoDB manager here to avoid circular imports
            from .mongodb_manager import MongoDBManager

            mongodb_manager = MongoDBManager(debug=self.debug)
            if not mongodb_manager.connected:
                if self.debug:
                    print(f"⚠️  Cannot add ISBN {isbn} to blacklist - MongoDB not available")
                return False

            # Create blacklist entry
            blacklist_entry = {
                'isbn': isbn,
                'title': metadata.get('book_full_name', metadata.get('book_title', 'Unknown')),
                'author': metadata.get('author', 'Unknown'),
                'extraction_date': datetime.now().isoformat(),
                'extraction_session_id': f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'patterns_extracted': {
                    # For now, these will be 0 since pattern extraction isn't implemented yet
                    'physical_descriptions': 0,
                    'dialogue': 0,
                    'personality': 0,
                    'behavior': 0,
                    'voice': 0
                },
                'total_patterns': 0,
                'characters_processed': len(metadata.get('character_identification', {}).get('characters', [])),
                'characters_identified': [char['name'] for char in metadata.get('character_identification', {}).get('characters', [])],
                'extraction_options': ['basic_extraction'],  # Will be updated when pattern extraction is implemented
                'file_info': {
                    'filename': metadata.get('source_file', 'unknown.pdf'),
                    'file_size': metadata.get('file_size', 0),
                    'page_count': metadata.get('total_pages', 0)
                },
                'processing_time_seconds': 0,  # Will be tracked when full novel processing is implemented
                'status': 'completed',
                'notes': 'Basic extraction completed - pattern extraction not yet implemented',
                'content_type': metadata.get('content_type', 'novel'),
                'game_metadata': {
                    'game_type': metadata.get('game_type', 'Unknown'),
                    'edition': metadata.get('edition', 'Unknown'),
                    'book_type': metadata.get('book_type', 'Unknown'),
                    'collection_name': metadata.get('collection_name', 'Unknown')
                }
            }

            # Insert into blacklist collection
            blacklist_collection = mongodb_manager.database['rpger.extraction.blacklist']
            result = blacklist_collection.insert_one(blacklist_entry)

            if self.debug:
                print(f"✅ Added ISBN {isbn} to blacklist with ID: {result.inserted_id}")

            return True

        except Exception as e:
            if self.debug:
                print(f"❌ Error adding ISBN {isbn} to blacklist: {e}")
            return False

    def _extract_isbn(self, doc, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract ISBN numbers from PDF metadata and content

        This extracts both ISBN-10 and ISBN-13 numbers and validates them.
        It checks both PDF metadata and the first few pages of content.

        Args:
            doc: PyMuPDF document object
            pdf_path: Path to PDF file

        Returns:
            Dictionary with ISBN information
        """
        isbn_data = {
            "isbn_10": None,
            "isbn_13": None,
            "isbn": None,  # Primary ISBN (prefers ISBN-13 if available)
            "source": None  # Where the ISBN was found (metadata or content)
        }

        # First try to extract from PDF metadata
        if doc.metadata:
            # Look for standard metadata fields that might contain ISBN
            for field in ["subject", "keywords"]:
                if field in doc.metadata and doc.metadata[field]:
                    isbns = self._find_isbns_in_text(doc.metadata[field])
                    if isbns:
                        self._update_isbn_data(isbn_data, isbns, source="pdf_metadata")
                        break

        # If no ISBN found in metadata, try content of first few pages
        if not isbn_data["isbn"]:
            max_pages_to_check = min(5, len(doc))  # Check first 5 pages or all if less
            for page_num in range(max_pages_to_check):
                page = doc[page_num]
                text = page.get_text()
                isbns = self._find_isbns_in_text(text)
                if isbns:
                    self._update_isbn_data(isbn_data, isbns, source="content_page_" + str(page_num + 1))
                    break

        if isbn_data["isbn"]:
            self.logger.info(f"📚 ISBN: {isbn_data['isbn']} (source: {isbn_data['source']})")
        else:
            self.logger.info("No valid ISBN found in document")

        return isbn_data

    def _find_isbns_in_text(self, text: str) -> Dict[str, str]:
        """
        Find ISBN-10 and ISBN-13 numbers in text

        Args:
            text: Text content to search

        Returns:
            Dictionary with found ISBN-10 and ISBN-13
        """
        found_isbns = {}

        # More robust patterns for ISBN detection
        isbn_patterns = [
            # ISBN-10 with prefix
            r'ISBN(?:-10)?[:\s]+([\d][\d-]{8,}[\dXx])',

            # ISBN-13 with prefix (specifically capturing full 13-digit pattern)
            r'ISBN-13[:\s]+([\d][\d-]{11,}[\d])',

            # ISBN-10 without prefix (standalone)
            r'(?<!\d)([\d][\d-]{8,}[\dXx])(?!\d)',

            # ISBN-13 without prefix (standalone)
            r'(?<!\d)([\d][\d-]{11,}[\d])(?!\d)',
        ]

        for pattern in isbn_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean up the ISBN by removing spaces and hyphens
                raw_isbn = match.group(1).strip()
                clean_isbn = raw_isbn.replace('-', '').replace(' ', '')

                # Validate the ISBN format and checksum
                if len(clean_isbn) == 10 and self._validate_isbn_10(clean_isbn):
                    found_isbns["isbn_10"] = clean_isbn
                elif len(clean_isbn) == 13 and self._validate_isbn_13(clean_isbn):
                    found_isbns["isbn_13"] = clean_isbn

        return found_isbns

    def _update_isbn_data(self, isbn_data: Dict[str, str], new_isbns: Dict[str, str], source: str) -> None:
        """
        Update ISBN data dictionary with new ISBNs

        Args:
            isbn_data: Existing ISBN data dictionary to update
            new_isbns: New ISBNs found
            source: Source of the ISBNs
        """
        # Update ISBN-10 and ISBN-13 if found
        if "isbn_10" in new_isbns and new_isbns["isbn_10"]:
            isbn_data["isbn_10"] = new_isbns["isbn_10"]

        if "isbn_13" in new_isbns and new_isbns["isbn_13"]:
            isbn_data["isbn_13"] = new_isbns["isbn_13"]

        # Set the primary ISBN (prefer ISBN-13 over ISBN-10)
        if isbn_data["isbn_13"]:
            isbn_data["isbn"] = isbn_data["isbn_13"]
        elif isbn_data["isbn_10"]:
            isbn_data["isbn"] = isbn_data["isbn_10"]

        # Set the source if an ISBN was found
        if isbn_data["isbn"] and not isbn_data["source"]:
            isbn_data["source"] = source

    def _validate_isbn_10(self, isbn: str) -> bool:
        """
        Validate an ISBN-10 number

        Args:
            isbn: ISBN-10 string (digits only with possible 'X' at the end)

        Returns:
            True if valid, False otherwise
        """
        if len(isbn) != 10:
            return False

        # Check if all characters are digits or the last one is 'X'/'x'
        if not all(c.isdigit() for c in isbn[:-1]) or (isbn[-1].upper() != 'X' and not isbn[-1].isdigit()):
            return False

        # Calculate checksum
        checksum = 0
        for i in range(9):
            checksum += (10 - i) * int(isbn[i])

        # Handle the last digit/character
        if isbn[-1].upper() == 'X':
            checksum += 10
        else:
            checksum += int(isbn[-1])

        # Valid if checksum is divisible by 11
        return checksum % 11 == 0

    def _validate_isbn_13(self, isbn: str) -> bool:
        """
        Validate an ISBN-13 number

        Args:
            isbn: ISBN-13 string (digits only)

        Returns:
            True if valid, False otherwise
        """
        if len(isbn) != 13:
            return False

        # Check if all characters are digits
        if not isbn.isdigit():
            return False

        # Calculate checksum using ISBN-13 algorithm
        checksum = 0
        for i in range(12):
            checksum += int(isbn[i]) * (1 if i % 2 == 0 else 3)

        check_digit = (10 - (checksum % 10)) % 10

        # Valid if calculated check digit matches the last digit
        return check_digit == int(isbn[-1])

    def _build_extraction_summary(self, sections: List[Dict], game_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Build extraction summary with game context"""

        total_words = sum(s["word_count"] for s in sections)
        total_tables = sum(len(s["tables"]) for s in sections)

        # Category distribution
        categories = {}
        for section in sections:
            category = section["category"]
            categories[category] = categories.get(category, 0) + 1

        summary = {
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
            "average_words_per_page": total_words // len(sections) if sections else 0,
            "has_isbn": "isbn" in game_metadata
        }

        # Add ISBN information if present in game_metadata
        if "isbn" in game_metadata:
            summary["isbn"] = game_metadata["isbn"]
            if "isbn_10" in game_metadata:
                summary["isbn_10"] = game_metadata["isbn_10"]
            if "isbn_13" in game_metadata:
                summary["isbn_13"] = game_metadata["isbn_13"]

        return summary

    def save_extraction(self, extraction_data: Dict, output_dir: Path) -> Dict[str, Path]:
        """Save extraction in multiple formats with novel-specific handling"""

        output_dir.mkdir(parents=True, exist_ok=True)
        metadata = extraction_data["metadata"]

        # Generate base filename from collection name
        base_name = metadata["collection_name"]

        # Check if this is novel content
        is_novel = metadata.get("content_type") == "novel"

        if is_novel:
            # For novels, save novel-specific MongoDB format
            novel_mongodb_data = self._prepare_novel_mongodb_format(extraction_data)
            mongodb_file = output_dir / f"{base_name}_novel_mongodb.json"

            with open(mongodb_file, 'w', encoding='utf-8') as f:
                json.dump(novel_mongodb_data, f, indent=2, ensure_ascii=False)

            # Save ChromaDB format (still useful for semantic search)
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
                "mongodb": mongodb_file,  # Novel-specific MongoDB format
                "chromadb": chromadb_file,
                "raw": raw_file,
                "summary": summary_file
            }

        else:
            # Standard RPG source material processing
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

    def _prepare_novel_mongodb_format(self, extraction_data: Dict) -> Dict[str, Any]:
        """Prepare novel data in MongoDB format - completely different from RPG source material"""

        metadata = extraction_data["metadata"]
        novel_data = metadata.get("novel_data", {})

        # Create novel-specific MongoDB document
        novel_document = {
            "_id": f"novel_{metadata['collection_name']}",
            "content_type": "novel",

            # Basic novel information
            "title": novel_data.get("extraction_metadata", {}).get("title", "Unknown Novel"),
            "author": novel_data.get("extraction_metadata", {}).get("author", "Unknown Author"),
            "isbn": metadata.get("isbn") or metadata.get("isbn_13") or metadata.get("isbn_10"),

            # Narrative structure (what makes novels different from RPG books)
            "narrative_structure": novel_data.get("narrative_structure", {}),

            # Character information (the main value from novels)
            "characters": novel_data.get("character_identification", {}).get("characters", []),
            "character_count": len(novel_data.get("character_identification", {}).get("characters", [])),

            # Processing metadata
            "extraction_metadata": {
                "extraction_date": novel_data.get("extraction_metadata", {}).get("extraction_date"),
                "extraction_method": "novel_narrative_extraction",
                "processing_stages": novel_data.get("character_identification", {}).get("processing_stages", {}),
                "total_pages": novel_data.get("narrative_structure", {}).get("total_pages", 0),
                "total_words": novel_data.get("narrative_structure", {}).get("total_words", 0),
                "chapters_detected": novel_data.get("narrative_structure", {}).get("chapters_detected", 0),
                "estimated_reading_time": novel_data.get("narrative_structure", {}).get("estimated_reading_time", 0)
            },

            # Source file information
            "source_file": {
                "filename": metadata.get("source_file", "unknown.pdf"),
                "file_size": metadata.get("file_size", 0),
                "collection_name": metadata.get("collection_name"),
                "game_type": metadata.get("game_type"),  # For organization
                "edition": metadata.get("edition")
            },

            # Novel-specific tags for organization
            "tags": [
                "novel",
                "character_extraction",
                metadata.get("game_type", "").lower(),
                metadata.get("edition", "").lower()
            ],

            # Future pattern extraction placeholder
            "pattern_extraction": {
                "status": "not_implemented",
                "planned_patterns": [
                    "physical_descriptions",
                    "dialogue_patterns",
                    "personality_traits",
                    "behavior_patterns",
                    "voice_characteristics"
                ]
            },

            # Timestamps
            "created_at": self._get_current_timestamp(),
            "updated_at": self._get_current_timestamp()
        }

        return novel_document

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

            # Add ISBN information if available
            if "isbn" in metadata:
                doc_metadata["isbn"] = metadata["isbn"]
            if "isbn_10" in metadata:
                doc_metadata["isbn_10"] = metadata["isbn_10"]
            if "isbn_13" in metadata:
                doc_metadata["isbn_13"] = metadata["isbn_13"]

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
