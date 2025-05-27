#!/usr/bin/env python3
"""
AI-Powered Extraction v3 Web UI
Modern web interface for PDF analysis and extraction
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import tempfile

# Add parent directory to path to import extraction modules
sys.path.append(str(Path(__file__).parent.parent))

from Modules.ai_game_detector import AIGameDetector
from Modules.ai_categorizer import AICategorizer
from Modules.pdf_processor import MultiGamePDFProcessor
from Modules.multi_collection_manager import MultiGameCollectionManager

app = Flask(__name__)
app.secret_key = 'extraction_v3_ui_secret_key_change_in_production'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max file size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching
app.config['UPLOAD_TIMEOUT'] = 300  # 5 minutes for upload timeout

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for session state
analysis_results = {}
extraction_results = {}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF file upload with improved timeout handling"""
    try:
        logger.info("📤 Upload request received")

        if 'file' not in request.files:
            logger.error("No file in request")
            return jsonify({'error': 'No file selected'}), 400

        file = request.files['file']
        if file.filename == '':
            logger.error("Empty filename")
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Only PDF files are allowed'}), 400

        # Check file size before saving
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        if file_size > app.config['MAX_CONTENT_LENGTH']:
            logger.error(f"File too large: {file_size} bytes")
            return jsonify({'error': f'File too large. Maximum size is {app.config["MAX_CONTENT_LENGTH"] // (1024*1024)}MB'}), 400

        # Save uploaded file temporarily with better error handling
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, filename)

        logger.info(f"💾 Saving file: {filename} ({file_size} bytes)")
        file.save(filepath)

        # Verify file was saved correctly
        if not os.path.exists(filepath):
            logger.error("File save failed")
            return jsonify({'error': 'Failed to save uploaded file'}), 500

        actual_size = os.path.getsize(filepath)
        if actual_size != file_size:
            logger.error(f"File size mismatch: expected {file_size}, got {actual_size}")
            return jsonify({'error': 'File upload corrupted'}), 500

        logger.info(f"✅ Upload successful: {filename}")
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'size': actual_size
        })

    except Exception as e:
        logger.error(f"Upload error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/analyze', methods=['POST'])
def analyze_pdf():
    """Analyze PDF content using AI"""
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        ai_provider = data.get('ai_provider', 'mock')

        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 400

        # Initialize AI detector with enhanced analysis
        ai_config = {
            'provider': ai_provider,
            'debug': True,
            'analysis_pages': 25,  # Analyze more pages for better book identification
            'max_tokens': 4000     # Stay within Claude's limits (4096 max)
        }

        detector = AIGameDetector(ai_config)

        # Analyze the PDF
        logger.info(f"Analyzing PDF: {filepath} with provider: {ai_provider}")

        # Extract content for analysis (to store for copy functionality)
        extracted_content = detector.extract_analysis_content(Path(filepath))

        # Perform AI analysis
        game_metadata = detector.analyze_game_metadata(Path(filepath))

        # Store results for later use
        session_id = str(hash(filepath))
        analysis_results[session_id] = {
            'filepath': filepath,
            'filename': os.path.basename(filepath),
            'game_metadata': game_metadata,
            'ai_provider': ai_provider,
            'analysis_time': datetime.now().isoformat(),
            'extracted_text': extracted_content.get('combined_text', '')  # Store extracted text for copy functionality
        }

        return jsonify({
            'success': True,
            'session_id': session_id,
            'analysis': game_metadata
        })

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/get_extracted_text/<session_id>', methods=['GET'])
def get_extracted_text(session_id):
    """Get the extracted text content for a session"""
    try:
        if session_id not in analysis_results:
            return jsonify({'error': 'Session not found'}), 404

        extracted_text = analysis_results[session_id].get('extracted_text', '')
        if not extracted_text:
            return jsonify({'error': 'No extracted text available'}), 404

        return jsonify({
            'success': True,
            'extracted_text': extracted_text,
            'filename': analysis_results[session_id].get('filename', 'unknown.pdf')
        })

    except Exception as e:
        logger.error(f"Error retrieving extracted text: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/extract', methods=['POST'])
def extract_pdf():
    """Extract content from analyzed PDF"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')

        if session_id not in analysis_results:
            return jsonify({'error': 'Analysis session not found'}), 400

        analysis = analysis_results[session_id]
        filepath = analysis['filepath']
        game_metadata = analysis['game_metadata']

        # Initialize PDF processor
        ai_config = {
            'provider': analysis['ai_provider'],
            'debug': True
        }

        processor = MultiGamePDFProcessor(debug=True, ai_config=ai_config)

        # Extract content
        logger.info(f"Extracting content from: {filepath}")
        extraction_result = processor.extract_pdf(Path(filepath))

        # Get sections and summary from result
        sections = extraction_result['sections']
        summary = extraction_result['extraction_summary']

        # Store extraction results
        extraction_results[session_id] = {
            'sections': sections,
            'summary': summary,
            'game_metadata': game_metadata,
            'extraction_time': datetime.now().isoformat()
        }

        return jsonify({
            'success': True,
            'summary': summary,
            'sections_count': len(sections),
            'ready_for_import': True
        })

    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/import_chroma', methods=['POST'])
def import_to_chroma():
    """Import extracted content to ChromaDB"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')

        if session_id not in extraction_results:
            return jsonify({'error': 'Extraction session not found'}), 400

        extraction = extraction_results[session_id]
        sections = extraction['sections']
        game_metadata = extraction['game_metadata']

        # Initialize collection manager
        manager = MultiGameCollectionManager()

        # Import to ChromaDB
        collection_name = game_metadata['collection_name']
        logger.info(f"Importing to ChromaDB collection: {collection_name}")

        # Convert sections to ChromaDB format
        documents = []
        metadatas = []
        ids = []

        for i, section in enumerate(sections):
            doc_id = f"{collection_name}_page_{section['page']}_{i}"
            documents.append(section['content'])
            metadatas.append({
                'title': section['title'],
                'page': section['page'],
                'category': section['category'],
                'game_type': game_metadata['game_type'],
                'edition': game_metadata['edition'],
                'book': game_metadata.get('book_type', 'Unknown'),
                'source': f"{game_metadata['game_type']} {game_metadata['edition']} Edition",
                'collection_name': collection_name
            })
            ids.append(doc_id)

        # Add to collection (use import method)
        success = manager.add_documents_to_collection(collection_name, documents, metadatas, ids)

        return jsonify({
            'success': True,
            'collection_name': collection_name,
            'documents_imported': len(documents),
            'message': f'Successfully imported {len(documents)} documents to ChromaDB'
        })

    except Exception as e:
        logger.error(f"ChromaDB import error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/import_mongodb', methods=['POST'])
def import_to_mongodb():
    """Import extracted content to MongoDB"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')

        if session_id not in extraction_results:
            return jsonify({'error': 'Extraction session not found'}), 400

        # For now, return a placeholder response
        # TODO: Implement MongoDB integration
        return jsonify({
            'success': True,
            'message': 'MongoDB import functionality coming soon',
            'note': 'Use MCP tools for monster data import'
        })

    except Exception as e:
        logger.error(f"MongoDB import error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_results/<session_id>')
def download_results(session_id):
    """Download extraction results as JSON"""
    try:
        if session_id not in extraction_results:
            return jsonify({'error': 'Session not found'}), 404

        extraction = extraction_results[session_id]

        # Create temporary file with results
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(extraction, temp_file, indent=2, default=str)
        temp_file.close()

        filename = f"extraction_results_{session_id[:8]}.json"

        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )

    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def system_status():
    """Get system status and configuration"""
    try:
        # Check ChromaDB connection
        try:
            manager = MultiGameCollectionManager()
            collections = manager.collections
            chroma_status = 'Connected'
            chroma_collections = len(collections)
        except Exception as e:
            chroma_status = f'Error: {str(e)}'
            chroma_collections = 0

        # Check AI providers
        ai_providers = {
            'mock': 'Available',
            'claude': 'Available' if os.getenv('ANTHROPIC_API_KEY') else 'API key not set',
            'openai': 'Available' if os.getenv('OPENAI_API_KEY') else 'API key not set',
            'local': 'Available' if os.getenv('LOCAL_LLM_URL') else 'URL not set'
        }

        return jsonify({
            'chroma_status': chroma_status,
            'chroma_collections': chroma_collections,
            'ai_providers': ai_providers,
            'active_sessions': len(analysis_results),
            'completed_extractions': len(extraction_results)
        })

    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
