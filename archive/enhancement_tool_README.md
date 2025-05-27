# Database Content Enhancement Tool

A tool to retroactively enhance existing database content with text quality improvements.

## 📋 Overview

This tool scans MongoDB and ChromaDB collections for documents with text quality issues, enhances their content, and updates the documents in the database. It provides detailed reports of text quality before and after enhancement.

## ✨ Features

- **Content Quality Analysis**: Scan collections to identify content with quality issues
- **Batch Enhancement**: Apply text quality enhancement to existing documents in batches
- **Quality Metrics**: Show before/after quality scores for enhanced content
- **Selective Enhancement**: Only enhance content below a quality threshold (e.g., < 75%)
- **Dry Run Mode**: Preview changes before applying them
- **Progress Reporting**: Show enhancement progress and statistics
- **Backup Integration**: Create backups before making changes

## 🔧 Installation

Make sure you have the required dependencies installed:

```bash
pip install pymongo>=4.6.0 nltk>=3.8.1
```

NLTK data is downloaded automatically on first run.

## 📊 Quality Analysis Features

The tool analyzes text quality using the following metrics:

- **Run-on Words**: Detects words that should be separated
- **Missing Spaces**: Identifies missing spaces between words
- **Inconsistent Spacing**: Finds whitespace issues
- **OCR Artifacts**: Detects common OCR misrecognition patterns

## 🚀 Usage

### Basic Usage

```bash
python enhance_existing_content.py
```

This will scan all collections in both MongoDB and ChromaDB, analyze content quality, and enhance documents with quality below 75% in dry run mode (no changes applied).

### Common Options

```bash
# Target specific database
python enhance_existing_content.py --database mongodb

# Target specific collection(s)
python enhance_existing_content.py --collections add_dmg add_phb

# Set quality threshold
python enhance_existing_content.py --threshold 80

# Apply changes (not just preview)
python enhance_existing_content.py --dry-run=False

# Create backups before making changes
python enhance_existing_content.py --backup

# Limit number of documents to process
python enhance_existing_content.py --limit 500

# Set batch size for processing
python enhance_existing_content.py --batch-size 50
```

### Full Options

```
usage: enhance_existing_content.py [-h] [--database {mongodb,chromadb,both}]
                                   [--collections COLLECTIONS [COLLECTIONS ...]]
                                   [--threshold THRESHOLD] [--limit LIMIT]
                                   [--batch-size BATCH_SIZE] [--dry-run]
                                   [--backup] [--output-dir OUTPUT_DIR]
                                   [--debug]

options:
  -h, --help            show this help message and exit
  --database {mongodb,chromadb,both}, -d {mongodb,chromadb,both}
                        Target database(s) to enhance
  --collections COLLECTIONS [COLLECTIONS ...], -c COLLECTIONS [COLLECTIONS ...]
                        Specific collections to scan (omit to scan all)
  --threshold THRESHOLD, -t THRESHOLD
                        Quality threshold percentage (default: 75)
  --limit LIMIT, -l LIMIT
                        Maximum documents to process (default: 100)
  --batch-size BATCH_SIZE, -b BATCH_SIZE
                        Batch size for enhancement (default: 10)
  --dry-run             Preview changes without applying them
  --backup              Create backups before enhancement
  --output-dir OUTPUT_DIR, -o OUTPUT_DIR
                        Output directory for reports and backups (default: ./output)
  --debug               Enable debug output
```

## 📝 Example Workflow

1. **Scan and analyze without changes**:
   ```bash
   python enhance_existing_content.py --dry-run
   ```

2. **Review the scan report** in the output directory

3. **Test enhancement on a small batch**:
   ```bash
   python enhance_existing_content.py --collections add_dmg --limit 10 --backup
   ```

4. **Enhance all content in specific collections**:
   ```bash
   python enhance_existing_content.py --collections add_dmg add_phb --limit 1000 --backup --dry-run=False
   ```

## 📊 Output Reports

The tool generates detailed JSON reports with:

- Overall scan results
- Collection-specific statistics
- Document-level detail with before/after content
- Quality scores before and after enhancement

Reports are saved to the specified output directory (default: `./output`).

## ⚠️ Important Notes

- **Always run with `--dry-run` first** to review potential changes
- **Always use `--backup` when applying changes** to enable rollback if needed
- MongoDB documents are updated in-place
- ChromaDB documents require delete-and-reinsert for updates (use caution)

## 🔄 Expected Performance

- Text quality improvements typically range from 5-20%
- Processing speed varies by document size (approximately 100-300 docs/minute)
- Memory usage scales with batch size (default batch size is conservative)

## 🛠️ Advanced Usage

### Text Quality Enhancement Only

You can use the TextQualityEnhancer class independently for text quality enhancement:

```python
from enhance_existing_content import TextQualityEnhancer

enhancer = TextQualityEnhancer(debug=True)
enhanced_text, metrics = enhancer.enhance_text("YourTextWith QualityIssues")
print(f"Enhanced: {enhanced_text}")
print(f"Quality improvement: {metrics}")
```