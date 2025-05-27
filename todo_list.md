# TODO List - PDF Extraction System

## 🔧 Database Content Enhancement Tool
**Priority: Medium**

Create a tool to retroactively enhance existing database content with text quality improvements.

### Features to Implement:
- **Content Quality Analysis**: Scan existing database collections to identify content with quality issues
- **Batch Enhancement**: Apply text quality enhancement to existing documents in batches
- **Quality Metrics**: Show before/after quality scores for enhanced content
- **Selective Enhancement**: Only enhance content below a quality threshold (e.g., < 75%)
- **Dry Run Mode**: Preview changes before applying them
- **Progress Reporting**: Show enhancement progress and statistics
- **Backup Integration**: Create backups before making changes

### Example Use Case:
```
Content like: "FIENDFOLIO\" Tomeof Creatures Malevolentand Benignisthefirstmajor"
Enhanced to: "FIEND FOLIO Tome of Creatures Malevolent and Benign is the first major"
```

### Technical Implementation:
- Create `enhance_existing_content.py` script
- Use existing `TextQualityEnhancer` class
- Integrate with `MongoDBManager` and `ChromaDBManager`
- Add command-line interface for batch operations
- Generate comprehensive enhancement reports

### Benefits:
- Improve readability of existing extracted content
- Fix OCR artifacts in previously processed documents
- Enhance spell checking for historical data
- Maintain data quality standards across entire database

---

## 📁 File Organization Tasks

### Move enhance_existing_content.py to Archive
**Priority: Low**

The `enhance_existing_content.py` file should be moved to the `archive/` folder since it's not integral to the core application functionality.

**Rationale:**
- Non-integral tools should be placed in archive folder rather than app root
- Keeps main directory clean and focused on core functionality
- Archive folder is appropriate for utility scripts and tools

### ISBN Extraction from PDFs
**Priority: Medium**

Implement ISBN number extraction from PDFs to prevent duplicate imports using the unique ISBN identifier.

**Features to Implement:**
- **ISBN Detection**: Extract ISBN-10 and ISBN-13 numbers from PDF metadata and content
- **Duplicate Prevention**: Check existing database for ISBN before importing
- **ISBN Validation**: Validate ISBN format and checksum
- **Metadata Storage**: Store ISBN in document metadata for future reference
- **Import Blocking**: Prevent re-import of documents with existing ISBNs

**Technical Implementation:**
- Add ISBN extraction to `pdf_processor.py`
- Use regex patterns to find ISBN in text content
- Check PDF metadata fields for ISBN information
- Integrate with database import workflow
- Add ISBN field to MongoDB and ChromaDB schemas

**Benefits:**
- Prevent accidental duplicate imports
- Maintain data integrity across collections
- Enable ISBN-based document identification
- Support library management workflows

### Content Type Selection (Novel vs Source Material)
**Priority: High**

Add dropdown selection in Web UI to specify content type after PDF selection, enabling different extraction approaches for novels vs source material.

**Current State:**
- System currently extracts all PDFs as "source material" (rulebooks, supplements, etc.)
- Uses AI detection for game type, edition, book type identification
- Optimized for structured RPG content extraction

**Proposed Enhancement:**
- **Content Type Dropdown**: Add selection after PDF upload with options:
  - **Source Material** (current default) - Rulebooks, supplements, adventures
  - **Novel** - Fiction books, campaign novels, lore books
- **Different Extraction Modes**:
  - Source Material: Current structured extraction (rules, tables, mechanics)
  - Novel: Narrative-focused extraction (chapters, characters, plot elements)

**UI Implementation:**
- Add content type selector in Step 2 (after PDF upload, before AI analysis)
- Update workflow: Upload PDF → Select Content Type → Run AI Analysis → Extract Content
- Modify AI analysis prompts based on content type selection
- Update metadata schema to include content_type field

**Future Novel Extraction Features** (to be implemented later):
- **Chapter Detection**: Automatic chapter/section identification
- **Character Extraction**: Named entity recognition for characters
- **Plot Summary**: AI-generated plot summaries and themes
- **Dialogue Analysis**: Speaker identification and dialogue extraction
- **Setting Detection**: Location and world-building element extraction
- **Timeline Extraction**: Event sequencing and chronology

**Technical Implementation:**
- Add content_type field to extraction workflow
- Update AI prompts to handle novel vs source material differently
- Modify database schemas to support novel-specific metadata
- Create novel-specific categorization system
- Add content type to hierarchical collection naming

**Benefits:**
- **Flexible Content Handling**: Support both RPG source material and fiction
- **Optimized Extraction**: Different approaches for different content types
- **Future Expansion**: Foundation for novel-specific features
- **User Control**: Clear content type specification before processing
- **Better Organization**: Separate handling and storage for different content types

---

## 🎯 Future Enhancements

### Text Quality Improvements
- [ ] Add more RPG-specific dictionaries (Pathfinder, Call of Cthulhu, etc.)
- [ ] Implement confidence scoring for spell corrections
- [ ] Add support for multiple languages

### UI/UX Improvements
- [ ] Add progress bars for long-running operations
- [ ] Implement real-time quality preview during extraction
- [ ] Add bulk operations interface

### Database Features
- [ ] Implement content versioning for enhanced documents
- [ ] Add rollback functionality for enhancement changes
- [ ] Create quality metrics dashboard

### Integration Features
- [ ] Add API endpoints for external quality enhancement
- [ ] Implement webhook notifications for quality improvements
- [ ] Create scheduled enhancement jobs
