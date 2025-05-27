#!/usr/bin/env python3
"""
AI-Powered Extraction v3 Web UI
Modern web interface for PDF analysis and extraction
"""

import os
import sys
import json
import logging
import requests
import shutil
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
from Modules.mongodb_manager import MongoDBManager

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
    """Analyze PDF content using AI with confidence testing"""
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        ai_provider = data.get('ai_provider', 'mock')
        run_confidence_test = data.get('run_confidence_test', True)

        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 400

        # Run confidence test first if requested
        confidence_results = None
        if run_confidence_test:
            try:
                sys.path.append(str(Path(__file__).parent.parent / 'archive'))
                from confidence_tester import run_quick_test

                logger.info("Running confidence test...")
                confidence_results = run_quick_test(filepath, pages_to_test=3)
                logger.info(f"Confidence test complete: {confidence_results['quick_confidence']:.1f}%")
            except Exception as e:
                logger.warning(f"Confidence test failed: {e}")
                confidence_results = {
                    'quick_confidence': 75.0,  # Default assumption
                    'recommended_method': 'text',
                    'text_confidence': 75.0,
                    'layout_confidence': 75.0,
                    'issues': [f'Confidence test unavailable: {str(e)}']
                }

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

        # Add confidence information to game metadata
        if confidence_results:
            game_metadata['extraction_confidence'] = confidence_results['quick_confidence']
            game_metadata['recommended_method'] = confidence_results['recommended_method']
            game_metadata['confidence_issues'] = confidence_results.get('issues', [])

        # Store results for later use
        session_id = str(hash(filepath))
        analysis_results[session_id] = {
            'filepath': filepath,
            'filename': os.path.basename(filepath),
            'game_metadata': game_metadata,
            'ai_provider': ai_provider,
            'analysis_time': datetime.now().isoformat(),
            'extracted_text': extracted_content.get('combined_text', ''),  # Store extracted text for copy functionality
            'confidence_results': confidence_results
        }

        return jsonify({
            'success': True,
            'session_id': session_id,
            'analysis': game_metadata,
            'confidence': confidence_results
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
        # Get any metadata overrides from the UI
        metadata_overrides = data.get('metadata_overrides', {})

        if session_id not in extraction_results:
            return jsonify({'error': 'Extraction session not found'}), 400

        extraction = extraction_results[session_id]
        sections = extraction['sections']
        game_metadata = extraction['game_metadata'].copy()

        # Apply any metadata overrides
        game_metadata.update(metadata_overrides)

        # Initialize collection manager
        manager = MultiGameCollectionManager()

        # Create hierarchical collection path: {game_type}.{edition}.{book_type}.{collection_name}
        game_type = game_metadata.get('game_type', 'unknown').lower().replace(' ', '_').replace('&', 'and')
        edition = game_metadata.get('edition', 'unknown').lower().replace(' ', '_').replace('&', 'and')
        book_type = game_metadata.get('book_type', 'unknown').lower().replace(' ', '_').replace('&', 'and')
        collection_base = game_metadata.get('collection_name', 'unknown')

        collection_name = f"{game_type}.{edition}.{book_type}.{collection_base}"
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
        split_sections = data.get('split_sections', False)  # New parameter
        # Get any metadata overrides from the UI
        metadata_overrides = data.get('metadata_overrides', {})

        if session_id not in extraction_results:
            return jsonify({'error': 'Extraction session not found'}), 400

        extraction = extraction_results[session_id]
        game_metadata = extraction['game_metadata'].copy()

        # Apply any metadata overrides
        game_metadata.update(metadata_overrides)

        # Initialize MongoDB manager
        mongodb_manager = MongoDBManager()

        # Check if MongoDB is available and connected
        if not mongodb_manager.connected:
            return jsonify({
                'success': False,
                'error': 'MongoDB not connected',
                'note': 'Check MongoDB configuration in .env file'
            }), 500

        # Option 1: Hierarchical collection names (current approach)
        # Creates separate collections: source_material.dand.1st_edition.core_rules.dmg
        use_hierarchical_collections = data.get('use_hierarchical_collections', True)

        if use_hierarchical_collections:
            # Create hierarchical collection path: rpger.source_material.{game_type}.{edition}.{book_type}.{collection_name}
            game_type = game_metadata.get('game_type', 'unknown').lower().replace(' ', '_').replace('&', 'and')
            edition = game_metadata.get('edition', 'unknown').lower().replace(' ', '_').replace('&', 'and')
            book_type = game_metadata.get('book_type', 'unknown').lower().replace(' ', '_').replace('&', 'and')
            collection_base = game_metadata.get('collection_name', 'unknown')

            collection_name = f"source_material.{game_type}.{edition}.{book_type}.{collection_base}"
        else:
            # Option 2: Single collection with hierarchical documents
            # All content goes in one collection with folder-like metadata
            collection_name = "source_material"

            # Add hierarchical metadata to each document
            hierarchical_path = {
                "game_type": game_metadata.get('game_type', 'unknown'),
                "edition": game_metadata.get('edition', 'unknown'),
                "book_type": game_metadata.get('book_type', 'unknown'),
                "collection_name": game_metadata.get('collection_name', 'unknown'),
                "full_path": f"{game_metadata.get('game_type', 'unknown')}/{game_metadata.get('edition', 'unknown')}/{game_metadata.get('book_type', 'unknown')}/{game_metadata.get('collection_name', 'unknown')}"
            }

            # Update extraction data to include hierarchical metadata
            extraction['hierarchical_path'] = hierarchical_path
        logger.info(f"Importing to MongoDB collection: {collection_name} (split_sections: {split_sections})")

        success, message = mongodb_manager.import_extracted_content(
            extraction,
            collection_name,
            split_sections=split_sections
        )

        if success:
            # Get MongoDB connection details for display
            mongodb_info = mongodb_manager.get_status()
            return jsonify({
                'success': True,
                'message': f'Successfully imported to MongoDB collection: {collection_name}',
                'collection': collection_name,
                'document_id': message.split(': ')[-1] if ': ' in message else message,
                'database_info': {
                    'host': mongodb_info.get('host', 'Unknown'),
                    'port': mongodb_info.get('port', 'Unknown'),
                    'database': mongodb_info.get('database', 'Unknown'),
                    'full_location': f"{mongodb_info.get('host', 'Unknown')}:{mongodb_info.get('port', 'Unknown')}/{mongodb_info.get('database', 'Unknown')}.{collection_name}"
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 500

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

        # Check MongoDB connection
        try:
            mongodb_manager = MongoDBManager()
            mongodb_info = mongodb_manager.get_status()
            mongodb_status = mongodb_info['status']
            mongodb_collections = mongodb_info.get('collections', 0)
        except Exception as e:
            mongodb_status = f'Error: {str(e)}'
            mongodb_collections = 0

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
            'mongodb_status': mongodb_status,
            'mongodb_collections': mongodb_collections,
            'ai_providers': ai_providers,
            'active_sessions': len(analysis_results),
            'completed_extractions': len(extraction_results)
        })

    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/browse_chromadb')
def browse_chromadb():
    """Browse ChromaDB collections and documents"""
    try:
        manager = MultiGameCollectionManager()
        collections = manager.collections

        # Get collection details
        collection_details = []
        for collection_name in collections:
            info = manager.get_collection_info(collection_name)
            if info:
                collection_details.append({
                    'name': collection_name,
                    'document_count': info.get('document_count', 0),
                    'game_type': manager.parse_collection_name(collection_name).get('game_type', 'Unknown')
                })

        return jsonify({
            'success': True,
            'collections': collection_details,
            'total_collections': len(collection_details)
        })

    except Exception as e:
        logger.error(f"ChromaDB browse error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/browse_chromadb/<collection_name>')
def browse_chromadb_collection(collection_name):
    """Browse specific ChromaDB collection documents"""
    try:
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))

        manager = MultiGameCollectionManager()

        # Get collection documents
        collection_uuid = manager._get_collection_uuid(collection_name)
        if not collection_uuid:
            return jsonify({'error': f'Collection {collection_name} not found'}), 404

        # Get documents from ChromaDB
        get_url = f"{manager.base_url}/collections/{collection_uuid}/get"
        params = {
            "limit": limit,
            "offset": offset
        }

        response = requests.post(get_url, json=params)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch documents'}), 500

        data = response.json()
        documents = data.get("documents", [])
        metadatas = data.get("metadatas", [])
        ids = data.get("ids", [])

        # Format documents for display
        formatted_docs = []
        for i, doc in enumerate(documents):
            formatted_docs.append({
                'id': ids[i] if i < len(ids) else f'doc_{i}',
                'content': doc[:200] + '...' if len(doc) > 200 else doc,  # Truncate for display
                'full_content': doc,
                'metadata': metadatas[i] if i < len(metadatas) else {},
                'word_count': len(doc.split()) if doc else 0
            })

        return jsonify({
            'success': True,
            'collection': collection_name,
            'documents': formatted_docs,
            'total_shown': len(formatted_docs),
            'offset': offset,
            'limit': limit
        })

    except Exception as e:
        logger.error(f"ChromaDB collection browse error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/browse_mongodb')
def browse_mongodb():
    """Browse MongoDB collections and documents"""
    try:
        mongodb_manager = MongoDBManager()

        if not mongodb_manager.connected:
            return jsonify({'error': 'MongoDB not connected'}), 500

        # Get collection names
        collection_names = mongodb_manager.database.list_collection_names()

        # Get collection details
        collection_details = []
        for collection_name in collection_names:
            try:
                collection = mongodb_manager.database[collection_name]
                doc_count = collection.count_documents({})

                # Get sample document to show structure
                sample_doc = collection.find_one()
                sample_fields = list(sample_doc.keys()) if sample_doc else []

                collection_details.append({
                    'name': collection_name,
                    'document_count': doc_count,
                    'sample_fields': sample_fields[:10]  # First 10 fields
                })
            except Exception as e:
                logger.warning(f"Error getting info for collection {collection_name}: {e}")

        return jsonify({
            'success': True,
            'collections': collection_details,
            'total_collections': len(collection_details),
            'database_info': mongodb_manager.get_status()
        })

    except Exception as e:
        logger.error(f"MongoDB browse error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/browse_mongodb/<collection_name>')
def browse_mongodb_collection(collection_name):
    """Browse specific MongoDB collection documents"""
    try:
        limit = int(request.args.get('limit', 10))
        skip = int(request.args.get('skip', 0))

        mongodb_manager = MongoDBManager()

        if not mongodb_manager.connected:
            return jsonify({'error': 'MongoDB not connected'}), 500

        collection = mongodb_manager.database[collection_name]

        # Get documents
        cursor = collection.find().skip(skip).limit(limit)
        documents = []

        for doc in cursor:
            # Convert ObjectId to string for JSON serialization
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])

            # Handle different content field names and structures
            content_text = ""

            # Check for various content fields
            if 'content' in doc:
                content_text = str(doc['content'])
            elif 'sections' in doc and isinstance(doc['sections'], list):
                # Extract content from sections array (AI extraction format)
                section_texts = []
                for section in doc['sections'][:3]:  # First 3 sections for preview
                    if isinstance(section, dict) and 'content' in section:
                        section_texts.append(str(section['content'])[:100])
                    elif isinstance(section, str):
                        section_texts.append(section[:100])
                content_text = " | ".join(section_texts)
            elif 'description' in doc:
                content_text = str(doc['description'])
            elif 'text' in doc:
                content_text = str(doc['text'])
            else:
                # Try to find any text-like field
                for key, value in doc.items():
                    if key not in ['_id', 'import_date', 'created_at', 'metadata'] and isinstance(value, str) and len(value) > 20:
                        content_text = str(value)
                        break

            # Truncate content for display
            if content_text and len(content_text) > 200:
                doc['content_preview'] = content_text[:200] + '...'
                doc['content_full'] = content_text
                doc['content'] = doc['content_preview']
            elif content_text:
                doc['content'] = content_text
            else:
                doc['content'] = "No content available"

            documents.append(doc)

        # Get total count
        total_count = collection.count_documents({})

        return jsonify({
            'success': True,
            'collection': collection_name,
            'documents': documents,
            'total_shown': len(documents),
            'total_count': total_count,
            'skip': skip,
            'limit': limit
        })

    except Exception as e:
        logger.error(f"MongoDB collection browse error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/query_game_edition', methods=['POST'])
def query_game_edition():
    """Query content across collections for a specific game/edition"""
    try:
        data = request.get_json()
        game_type = data.get('game_type')
        edition = data.get('edition')
        book_type = data.get('book_type')

        if not game_type:
            return jsonify({'error': 'game_type is required'}), 400

        mongodb_manager = MongoDBManager()

        if not mongodb_manager.connected:
            return jsonify({'error': 'MongoDB not connected'}), 500

        # Query across collections
        results = mongodb_manager.query_by_game_edition(game_type, edition, book_type)

        # Format results for display
        formatted_results = []
        for doc in results:
            # Convert ObjectId to string for JSON serialization
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])

            # Extract content preview
            content_preview = ""
            if 'content' in doc:
                content_preview = str(doc['content'])[:200] + '...' if len(str(doc['content'])) > 200 else str(doc['content'])
            elif 'sections' in doc and isinstance(doc['sections'], list) and doc['sections']:
                # Get content from first section
                first_section = doc['sections'][0]
                if isinstance(first_section, dict) and 'content' in first_section:
                    content_preview = str(first_section['content'])[:200] + '...'

            formatted_results.append({
                'id': doc.get('_id', 'unknown'),
                'source_collection': doc.get('_source_collection', 'unknown'),
                'collection_parts': doc.get('_collection_parts', {}),
                'content_preview': content_preview,
                'sections_count': len(doc.get('sections', [])) if 'sections' in doc else 0,
                'title': doc.get('title', 'Untitled'),
                'category': doc.get('category', 'Unknown')
            })

        return jsonify({
            'success': True,
            'query': {
                'game_type': game_type,
                'edition': edition,
                'book_type': book_type
            },
            'results': formatted_results,
            'total_results': len(formatted_results),
            'collections_searched': len(set(r['source_collection'] for r in formatted_results))
        })

    except Exception as e:
        logger.error(f"Game edition query error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_settings', methods=['GET'])
def get_settings():
    """Get current settings from .env file"""
    try:
        env_path = Path(__file__).parent.parent / '.env'
        env_sample_path = Path(__file__).parent.parent / '.env.sample'

        # If .env doesn't exist, copy from .env.sample
        if not env_path.exists() and env_sample_path.exists():
            shutil.copy2(env_sample_path, env_path)
            logger.info("Created .env file from .env.sample")

        settings = {}

        # Read .env file if it exists
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip('"\'')
                        settings[key.strip()] = value

        return jsonify({
            'success': True,
            'settings': settings
        })

    except Exception as e:
        logger.error(f"Settings load error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/save_settings', methods=['POST'])
def save_settings():
    """Save settings to .env file"""
    try:
        data = request.get_json()
        new_settings = data.get('settings', {})

        env_path = Path(__file__).parent.parent / '.env'
        env_sample_path = Path(__file__).parent.parent / '.env.sample'

        # If .env doesn't exist, copy from .env.sample
        if not env_path.exists() and env_sample_path.exists():
            shutil.copy2(env_sample_path, env_path)
            logger.info("Created .env file from .env.sample")

        # Read existing settings
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
        else:
            lines = []

        # Parse existing lines
        updated_lines = []
        updated_keys = set()

        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and '=' in stripped:
                key = stripped.split('=', 1)[0].strip()
                if key in new_settings:
                    # Update existing setting
                    value = new_settings[key]
                    # Add quotes if value contains spaces or special characters
                    if ' ' in value or any(char in value for char in ['$', '&', '|', ';']):
                        value = f'"{value}"'
                    updated_lines.append(f"{key}={value}\n")
                    updated_keys.add(key)
                else:
                    # Keep existing line
                    updated_lines.append(line)
            else:
                # Keep comments and empty lines
                updated_lines.append(line)

        # Add new settings that weren't in the file
        for key, value in new_settings.items():
            if key not in updated_keys and value:  # Only add non-empty values
                # Add quotes if value contains spaces or special characters
                if ' ' in value or any(char in value for char in ['$', '&', '|', ';']):
                    value = f'"{value}"'
                updated_lines.append(f"{key}={value}\n")

        # Write updated .env file
        with open(env_path, 'w') as f:
            f.writelines(updated_lines)

        logger.info("Settings saved to .env file")

        return jsonify({
            'success': True,
            'message': 'Settings saved successfully'
        })

    except Exception as e:
        logger.error(f"Settings save error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
