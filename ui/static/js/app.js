// AI-Powered Extraction v3 UI JavaScript

// Global variables
let currentFile = null;
let currentSessionId = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeFileUpload();
    checkStatus();
});

// File Upload Handling
function initializeFileUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');

    // Drag and drop functionality
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    // Click to upload - only on upload area, not button
    uploadArea.addEventListener('click', function(e) {
        // Don't trigger if clicking the button itself
        if (e.target === browseBtn || browseBtn.contains(e.target)) {
            return;
        }

        // Prevent multiple clicks during upload
        if (currentFile && currentFile.uploading) {
            console.log('Upload already in progress, ignoring click');
            return;
        }

        console.log('Upload area clicked, opening file dialog');
        fileInput.click();
    });

    // Browse button click handler
    browseBtn.addEventListener('click', function(e) {
        e.stopPropagation(); // Prevent event bubbling to upload area

        // Prevent multiple clicks during upload
        if (currentFile && currentFile.uploading) {
            console.log('Upload already in progress, ignoring button click');
            return;
        }

        console.log('Browse button clicked, opening file dialog');
        fileInput.click();
    });

    // File input change handler
    fileInput.addEventListener('change', function(e) {
        console.log('File input change event triggered');
        console.log('Files selected:', e.target.files.length);

        if (e.target.files.length > 0) {
            const selectedFile = e.target.files[0];
            console.log('File selected:', selectedFile.name, 'Size:', selectedFile.size, 'Type:', selectedFile.type);

            // Show immediate feedback
            showToast(`File selected: ${selectedFile.name}`, 'info');

            handleFileSelect(selectedFile);

            // Clear the input so the same file can be selected again if needed
            e.target.value = '';
        } else {
            console.log('No files selected');
        }
    });
}

// Handle file selection
function handleFileSelect(file) {
    console.log('=== handleFileSelect called ===');
    console.log('File name:', file.name);
    console.log('File size:', file.size, 'bytes');
    console.log('File type:', file.type);
    console.log('Current file state:', currentFile);

    // Prevent multiple uploads
    if (currentFile && currentFile.uploading) {
        console.log('Upload already in progress, aborting');
        showToast('Upload already in progress', 'warning');
        return;
    }

    // Validate file type
    if (!file.type.includes('pdf')) {
        console.log('Invalid file type:', file.type);
        showToast('Please select a PDF file', 'error');
        return;
    }

    // Validate file size
    if (file.size > 200 * 1024 * 1024) { // 200MB limit
        console.log('File too large:', file.size);
        showToast('File size must be less than 200MB', 'error');
        return;
    }

    console.log('File validation passed, starting upload...');
    // Upload the file
    uploadFile(file);
}

// Upload file to server with improved timeout handling
function uploadFile(file) {
    console.log('=== uploadFile called ===');
    console.log('File name:', file.name);
    console.log('File size:', file.size, 'bytes');
    console.log('File type:', file.type);

    // Set upload state
    currentFile = { uploading: true, name: file.name };
    console.log('Set currentFile state:', currentFile);

    // Update upload area visual state
    const uploadArea = document.getElementById('upload-area');
    uploadArea.classList.add('uploading');
    console.log('Added uploading class to upload area');

    // Create form data
    const formData = new FormData();
    formData.append('file', file);
    console.log('Created FormData and appended file');

    // Update UI
    showProgress('upload');
    showToast('Uploading file...', 'info');
    console.log('Updated UI for upload in progress');

    // Create AbortController for timeout handling
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
        console.log('Upload timeout reached, aborting');
        controller.abort();
    }, 300000); // 5 minute timeout
    console.log('Set upload timeout for 5 minutes');

    console.log('Starting fetch to /upload endpoint...');
    fetch('/upload', {
        method: 'POST',
        body: formData,
        signal: controller.signal
    })
    .then(response => {
        clearTimeout(timeoutId);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        const uploadArea = document.getElementById('upload-area');
        uploadArea.classList.remove('uploading');

        if (data.success) {
            console.log('Upload successful:', data);
            currentFile = data;
            currentFile.uploading = false; // Clear upload state
            displayFileInfo(data);
            updateProgress('upload', 'completed');
            showAnalysisCard();
            showToast('File uploaded successfully', 'success');
        } else {
            console.log('Upload failed:', data);
            currentFile = null; // Clear upload state
            updateProgress('upload', 'error');
            showToast(data.error || 'Upload failed', 'error');
        }
    })
    .catch(error => {
        clearTimeout(timeoutId);
        const uploadArea = document.getElementById('upload-area');
        uploadArea.classList.remove('uploading');
        currentFile = null; // Clear upload state
        updateProgress('upload', 'error');
        console.error('Upload error:', error);

        if (error.name === 'AbortError') {
            showToast('Upload timed out. Please try again with a smaller file.', 'error');
        } else if (error.message.includes('413')) {
            showToast('File too large. Maximum size is 200MB.', 'error');
        } else {
            showToast('Upload failed: ' + error.message, 'error');
        }
    });
}

// Display file information
function displayFileInfo(fileData) {
    document.getElementById('filename').textContent = fileData.filename;
    document.getElementById('filesize').textContent = formatFileSize(fileData.size);
    document.getElementById('file-info').style.display = 'block';
}

// Show analysis card
function showAnalysisCard() {
    document.getElementById('analysis-card').style.display = 'block';
    document.getElementById('analysis-card').scrollIntoView({ behavior: 'smooth' });
}

// Analyze PDF with AI
function analyzePDF() {
    if (!currentFile) {
        showToast('Please upload a file first', 'error');
        return;
    }

    const aiProvider = document.getElementById('ai-provider').value;

    document.getElementById('analyze-btn').disabled = true;
    document.getElementById('analysis-progress').style.display = 'block';
    updateProgress('analyze', 'active');

    fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filepath: currentFile.filepath,
            ai_provider: aiProvider
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('analysis-progress').style.display = 'none';
        document.getElementById('analyze-btn').disabled = false;

        if (data.success) {
            currentSessionId = data.session_id;
            displayAnalysisResults(data.analysis);
            updateProgress('analyze', 'completed');
            showExtractionCard();
            showToast('Analysis completed successfully', 'success');
        } else {
            showToast(data.error || 'Analysis failed', 'error');
        }
    })
    .catch(error => {
        console.error('Analysis error:', error);
        document.getElementById('analysis-progress').style.display = 'none';
        document.getElementById('analyze-btn').disabled = false;
        showToast('Analysis failed: ' + error.message, 'error');
    });
}

// Store current analysis data for metadata editing
let currentAnalysisData = null;

// Display analysis results
function displayAnalysisResults(analysis) {
    // Store analysis data for metadata editing
    currentAnalysisData = analysis;

    const confidence = analysis.confidence || 0;
    const confidenceClass = confidence > 0.8 ? 'confidence-high' :
                           confidence > 0.5 ? 'confidence-medium' : 'confidence-low';

    const resultsHtml = `
        <div class="analysis-detail">
            <span class="analysis-label">Game Type:</span>
            <span class="analysis-value">${analysis.game_type || 'Unknown'}</span>
        </div>
        <div class="analysis-detail">
            <span class="analysis-label">Edition:</span>
            <span class="analysis-value">${analysis.edition || 'Unknown'}</span>
        </div>
        <div class="analysis-detail">
            <span class="analysis-label">Book Type:</span>
            <span class="analysis-value">${analysis.book_type || 'Unknown'}</span>
        </div>
        <div class="analysis-detail">
            <span class="analysis-label">Book Title:</span>
            <span class="analysis-value">${analysis.book_full_name || analysis.book_title || 'Unknown'}</span>
        </div>
        <div class="analysis-detail">
            <span class="analysis-label">Collection:</span>
            <span class="analysis-value">${analysis.collection_name || 'Unknown'}</span>
        </div>
        <div class="analysis-detail">
            <span class="analysis-label">Confidence:</span>
            <span class="confidence-badge ${confidenceClass}">
                ${Math.round(confidence * 100)}%
            </span>
        </div>
    `;

    document.getElementById('analysis-details').innerHTML = resultsHtml;
    document.getElementById('analysis-results').style.display = 'block';

    // Populate metadata review section
    populateMetadataReview(analysis);
}

// Show extraction card
function showExtractionCard() {
    document.getElementById('extraction-card').style.display = 'block';
    document.getElementById('extraction-card').scrollIntoView({ behavior: 'smooth' });
}

// Extract content from PDF
function extractContent() {
    if (!currentSessionId) {
        showToast('Please analyze the PDF first', 'error');
        return;
    }

    document.getElementById('extract-btn').disabled = true;
    document.getElementById('extraction-progress').style.display = 'block';
    updateProgress('extract', 'active');

    fetch('/extract', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: currentSessionId
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('extraction-progress').style.display = 'none';
        document.getElementById('extract-btn').disabled = false;

        if (data.success) {
            displayExtractionResults(data);
            updateProgress('extract', 'completed');
            showImportCard();
            showToast('Content extracted successfully', 'success');
        } else {
            showToast(data.error || 'Extraction failed', 'error');
        }
    })
    .catch(error => {
        console.error('Extraction error:', error);
        document.getElementById('extraction-progress').style.display = 'none';
        document.getElementById('extract-btn').disabled = false;
        showToast('Extraction failed: ' + error.message, 'error');
    });
}

// Display extraction results
function displayExtractionResults(data) {
    const summary = data.summary;
    const resultsHtml = `
        <div class="extraction-summary">
            <div class="summary-stat">Pages: ${summary.total_pages || 0}</div>
            <div class="summary-stat">Words: ${(summary.total_words || 0).toLocaleString()}</div>
            <div class="summary-stat">Sections: ${data.sections_count || 0}</div>
        </div>
        ${summary.category_distribution ? generateCategoryDistribution(summary.category_distribution) : ''}
    `;

    document.getElementById('extraction-details').innerHTML = resultsHtml;
    document.getElementById('extraction-results').style.display = 'block';
}

// Generate category distribution display
function generateCategoryDistribution(categories) {
    let html = '<div class="mt-3"><strong>Category Distribution:</strong><br>';
    for (const [category, count] of Object.entries(categories)) {
        html += `
            <div class="category-item">
                <span>${category}</span>
                <span class="category-count">${count}</span>
            </div>
        `;
    }
    html += '</div>';
    return html;
}

// Show import card
function showImportCard() {
    document.getElementById('import-card').style.display = 'block';
    document.getElementById('import-card').scrollIntoView({ behavior: 'smooth' });
}

// Populate metadata review section
function populateMetadataReview(analysis) {
    document.getElementById('display-game-type').textContent = analysis.game_type || 'Unknown';
    document.getElementById('display-edition').textContent = analysis.edition || 'Unknown';
    document.getElementById('display-book-type').textContent = analysis.book_type || 'Unknown';
    document.getElementById('display-book-title').textContent = analysis.book_full_name || analysis.book_title || 'Unknown';
    document.getElementById('display-collection').textContent = analysis.collection_name || 'Unknown';

    // Update path preview
    updatePathPreview();

    // Show metadata review section
    document.getElementById('metadata-review').style.display = 'block';
}

// Update path preview
function updatePathPreview() {
    const gameType = (document.getElementById('edit-game-type').value ||
                     document.getElementById('display-game-type').textContent || 'unknown')
                     .toLowerCase().replace(/\s+/g, '_').replace(/&/g, 'and');
    const edition = (document.getElementById('edit-edition').value ||
                    document.getElementById('display-edition').textContent || 'unknown')
                    .toLowerCase().replace(/\s+/g, '_').replace(/&/g, 'and');
    const bookType = (document.getElementById('edit-book-type').value ||
                     document.getElementById('display-book-type').textContent || 'unknown')
                     .toLowerCase().replace(/\s+/g, '_').replace(/&/g, 'and');
    const collection = document.getElementById('edit-collection').value ||
                      document.getElementById('display-collection').textContent || 'unknown';

    const organizationStyle = document.getElementById('organization-style').value;
    const pathTypeElement = document.getElementById('path-type');
    const pathPreviewElement = document.getElementById('path-preview');

    if (organizationStyle === 'separate') {
        // Separate collections approach
        const path = `source_material.${gameType}.${edition}.${bookType}.${collection}`;
        pathTypeElement.textContent = 'Collection:';
        pathPreviewElement.textContent = path;
    } else {
        // Single collection with folder metadata approach
        const folderPath = `${gameType}/${edition}/${bookType}/${collection}`;
        pathTypeElement.textContent = 'Collection: source_material, Folder:';
        pathPreviewElement.textContent = folderPath;
    }
}

// Toggle metadata editing mode
function toggleMetadataEdit() {
    const displays = document.querySelectorAll('.metadata-display');
    const edits = document.querySelectorAll('.metadata-edit');
    const editBtn = document.getElementById('edit-metadata-btn');
    const saveBtn = document.getElementById('save-metadata-btn');
    const cancelBtn = document.getElementById('cancel-metadata-btn');

    // Hide displays, show edits
    displays.forEach(display => display.style.display = 'none');
    edits.forEach(edit => edit.style.display = 'block');

    // Populate edit fields with current values
    document.getElementById('edit-game-type').value = document.getElementById('display-game-type').textContent;
    document.getElementById('edit-edition').value = document.getElementById('display-edition').textContent;
    document.getElementById('edit-book-type').value = document.getElementById('display-book-type').textContent;
    document.getElementById('edit-book-title').value = document.getElementById('display-book-title').textContent;
    document.getElementById('edit-collection').value = document.getElementById('display-collection').textContent;

    // Update button visibility
    editBtn.style.display = 'none';
    saveBtn.style.display = 'inline-block';
    cancelBtn.style.display = 'inline-block';

    // Add event listeners for real-time path preview
    edits.forEach(edit => {
        edit.addEventListener('input', updatePathPreview);
    });
}

// Save metadata changes
function saveMetadataChanges() {
    // Update display values
    document.getElementById('display-game-type').textContent = document.getElementById('edit-game-type').value;
    document.getElementById('display-edition').textContent = document.getElementById('edit-edition').value;
    document.getElementById('display-book-type').textContent = document.getElementById('edit-book-type').value;
    document.getElementById('display-book-title').textContent = document.getElementById('edit-book-title').value;
    document.getElementById('display-collection').textContent = document.getElementById('edit-collection').value;

    // Update stored analysis data
    if (currentAnalysisData) {
        currentAnalysisData.game_type = document.getElementById('edit-game-type').value;
        currentAnalysisData.edition = document.getElementById('edit-edition').value;
        currentAnalysisData.book_type = document.getElementById('edit-book-type').value;
        currentAnalysisData.book_full_name = document.getElementById('edit-book-title').value;
        currentAnalysisData.collection_name = document.getElementById('edit-collection').value;
    }

    // Exit edit mode
    cancelMetadataEdit();

    showToast('Metadata updated successfully', 'success');
}

// Cancel metadata editing
function cancelMetadataEdit() {
    const displays = document.querySelectorAll('.metadata-display');
    const edits = document.querySelectorAll('.metadata-edit');
    const editBtn = document.getElementById('edit-metadata-btn');
    const saveBtn = document.getElementById('save-metadata-btn');
    const cancelBtn = document.getElementById('cancel-metadata-btn');

    // Show displays, hide edits
    displays.forEach(display => display.style.display = 'block');
    edits.forEach(edit => edit.style.display = 'none');

    // Update button visibility
    editBtn.style.display = 'inline-block';
    saveBtn.style.display = 'none';
    cancelBtn.style.display = 'none';

    // Update path preview with current display values
    updatePathPreview();
}

// Get current metadata (including any edits)
function getCurrentMetadata() {
    if (!currentAnalysisData) return {};

    return {
        game_type: currentAnalysisData.game_type,
        edition: currentAnalysisData.edition,
        book_type: currentAnalysisData.book_type,
        book_full_name: currentAnalysisData.book_full_name,
        collection_name: currentAnalysisData.collection_name
    };
}

// Get organization preferences
function getOrganizationPreferences() {
    const organizationStyle = document.getElementById('organization-style').value;
    return {
        use_hierarchical_collections: organizationStyle === 'separate'
    };
}

// Import to ChromaDB
function importToChroma() {
    if (!currentSessionId) {
        showToast('Please extract content first', 'error');
        return;
    }

    fetch('/import_chroma', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: currentSessionId,
            metadata_overrides: getCurrentMetadata()
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayImportResult('ChromaDB', data, 'success');
            updateProgress('import', 'completed');
            showToast('Successfully imported to ChromaDB', 'success');
        } else {
            displayImportResult('ChromaDB', data, 'error');
            showToast(data.error || 'ChromaDB import failed', 'error');
        }
    })
    .catch(error => {
        console.error('ChromaDB import error:', error);
        displayImportResult('ChromaDB', {error: error.message}, 'error');
        showToast('ChromaDB import failed: ' + error.message, 'error');
    });
}

// Import to MongoDB
function importToMongoDB(splitSections = false) {
    if (!currentSessionId) {
        showToast('Please extract content first', 'error');
        return;
    }

    const importType = splitSections ? 'Split Sections (v1/v2 style)' : 'Single Document (v3 style)';
    showToast(`Importing to MongoDB: ${importType}`, 'info');

    fetch('/import_mongodb', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: currentSessionId,
            split_sections: splitSections,
            metadata_overrides: getCurrentMetadata(),
            ...getOrganizationPreferences()
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Enhanced MongoDB result display with hierarchical collection info
            const enhancedData = {
                ...data,
                location_info: data.database_info ?
                    `Location: ${data.database_info.full_location}` :
                    `Collection: ${data.collection}`,
                hierarchical_path: data.collection ?
                    `Path: rpger.${data.collection}` :
                    'Path: Not available'
            };
            displayImportResult('MongoDB', enhancedData, 'info');
            showToast(data.message, 'info');
        } else {
            displayImportResult('MongoDB', data, 'error');
            showToast(data.error || 'MongoDB import failed', 'error');
        }
    })
    .catch(error => {
        console.error('MongoDB import error:', error);
        displayImportResult('MongoDB', {error: error.message}, 'error');
        showToast('MongoDB import failed: ' + error.message, 'error');
    });
}

// Display import result
function displayImportResult(database, data, type) {
    const resultClass = type === 'success' ? 'import-success' :
                       type === 'error' ? 'import-error' : 'alert alert-info';

    let message = '';
    if (data.success) {
        message = data.message || `Successfully imported to ${database}`;
        if (data.documents_imported) {
            message += ` (${data.documents_imported} documents)`;
        }
        if (data.collection_name) {
            message += ` in collection: ${data.collection_name}`;
        }
        if (data.location_info) {
            message += `<br><small>${data.location_info}</small>`;
        }
        if (data.hierarchical_path) {
            message += `<br><small>${data.hierarchical_path}</small>`;
        }
        if (data.document_id) {
            message += `<br><small>Document ID: ${data.document_id}</small>`;
        }
    } else {
        message = data.error || `Failed to import to ${database}`;
    }

    const resultHtml = `
        <div class="${resultClass}">
            <strong>${database} Import:</strong> ${message}
        </div>
    `;

    document.getElementById('import-results').innerHTML += resultHtml;
    document.getElementById('import-results').style.display = 'block';
}

// Download results
function downloadResults() {
    if (!currentSessionId) {
        showToast('No results to download', 'error');
        return;
    }

    window.open(`/download_results/${currentSessionId}`, '_blank');
    showToast('Download started', 'info');
}

// Copy extracted text to clipboard
function copyExtractedText() {
    if (!currentSessionId) {
        showToast('No analysis session found', 'error');
        return;
    }

    // Disable button and show loading state
    const copyBtn = document.getElementById('copy-text-btn');
    const originalText = copyBtn.innerHTML;
    copyBtn.disabled = true;
    copyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';

    fetch(`/get_extracted_text/${currentSessionId}`)
    .then(response => response.json())
    .then(data => {
        copyBtn.disabled = false;
        copyBtn.innerHTML = originalText;

        if (data.success) {
            // Copy to clipboard
            navigator.clipboard.writeText(data.extracted_text).then(() => {
                showToast('Extracted text copied to clipboard!', 'success');

                // Temporarily change button text to show success
                copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(() => {
                    copyBtn.innerHTML = originalText;
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
                // Fallback: create a textarea and select the text
                fallbackCopyText(data.extracted_text);
            });
        } else {
            showToast(data.error || 'Failed to get extracted text', 'error');
        }
    })
    .catch(error => {
        console.error('Error fetching extracted text:', error);
        copyBtn.disabled = false;
        copyBtn.innerHTML = originalText;
        showToast('Failed to fetch extracted text', 'error');
    });
}

// Fallback copy method for older browsers
function fallbackCopyText(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand('copy');
        showToast('Extracted text copied to clipboard!', 'success');

        // Update button to show success
        const copyBtn = document.getElementById('copy-text-btn');
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
        }, 2000);
    } catch (err) {
        console.error('Fallback copy failed: ', err);
        showToast('Failed to copy text to clipboard', 'error');
    }

    document.body.removeChild(textArea);
}

// Check system status
function checkStatus() {
    fetch('/status')
    .then(response => response.json())
    .then(data => {
        displaySystemStatus(data);
    })
    .catch(error => {
        console.error('Status check error:', error);
        document.getElementById('status-content').innerHTML =
            '<p class="text-danger">Failed to check system status</p>';
    });
}

// Display system status
function displaySystemStatus(status) {
    const chromaStatusClass = status.chroma_status === 'Connected' ? 'status-connected' : 'status-error';
    const mongoStatusClass = status.mongodb_status === 'Connected' ? 'status-connected' : 'status-error';

    let providersHtml = '';
    for (const [provider, providerStatus] of Object.entries(status.ai_providers)) {
        const statusClass = providerStatus === 'Available' ? 'provider-available' : 'provider-unavailable';
        providersHtml += `
            <div class="provider-status">
                <span>${provider.toUpperCase()}</span>
                <span class="${statusClass}">${providerStatus}</span>
            </div>
        `;
    }

    const statusHtml = `
        <div class="mb-2">
            <span class="status-indicator ${chromaStatusClass}"></span>
            <strong>ChromaDB:</strong> ${status.chroma_status}
        </div>
        <div class="mb-2">
            <small class="text-muted">Collections: ${status.chroma_collections}</small>
        </div>
        <div class="mb-2">
            <span class="status-indicator ${mongoStatusClass}"></span>
            <strong>MongoDB:</strong> ${status.mongodb_status}
        </div>
        <div class="mb-2">
            <small class="text-muted">Collections: ${status.mongodb_collections}</small>
        </div>
        <div class="mb-3">
            <strong>AI Providers:</strong>
            ${providersHtml}
        </div>
        <div class="small text-muted">
            Active Sessions: ${status.active_sessions}<br>
            Completed: ${status.completed_extractions}
        </div>
    `;

    document.getElementById('status-content').innerHTML = statusHtml;
}

// Browse ChromaDB collections
function browseChromaDB() {
    fetch('/browse_chromadb')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayDatabaseBrowser('ChromaDB', data.collections, 'chromadb');
        } else {
            showToast('Failed to browse ChromaDB: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('ChromaDB browse error:', error);
        showToast('ChromaDB browse failed: ' + error.message, 'error');
    });
}

// Browse MongoDB collections
function browseMongoDB() {
    fetch('/browse_mongodb')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayDatabaseBrowser('MongoDB', data.collections, 'mongodb');
        } else {
            showToast('Failed to browse MongoDB: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('MongoDB browse error:', error);
        showToast('MongoDB browse failed: ' + error.message, 'error');
    });
}

// Display database browser
function displayDatabaseBrowser(dbType, collections, dbKey) {
    const modalHtml = `
        <div class="modal fade" id="databaseBrowserModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${dbType} Collections Browser</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-4">
                                <h6>Collections (${collections.length})</h6>
                                <div class="list-group" id="collections-list">
                                    ${collections.map(col => `
                                        <a href="#" class="list-group-item list-group-item-action"
                                           onclick="browseCollection('${dbKey}', '${col.name}')">
                                            <div class="d-flex w-100 justify-content-between">
                                                <h6 class="mb-1">${col.name}</h6>
                                                <small>${col.document_count} docs</small>
                                            </div>
                                            ${col.game_type ? `<small class="text-muted">Game: ${col.game_type}</small>` : ''}
                                            ${col.sample_fields ? `<small class="text-muted">Fields: ${col.sample_fields.slice(0,3).join(', ')}</small>` : ''}
                                        </a>
                                    `).join('')}
                                </div>
                            </div>
                            <div class="col-md-8">
                                <div id="collection-details">
                                    <p class="text-muted">Select a collection to view documents</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if any
    const existingModal = document.getElementById('databaseBrowserModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('databaseBrowserModal'));
    modal.show();
}

// Browse specific collection
function browseCollection(dbType, collectionName) {
    const endpoint = dbType === 'chromadb' ?
        `/browse_chromadb/${collectionName}` :
        `/browse_mongodb/${collectionName}`;

    fetch(endpoint + '?limit=5')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayCollectionDocuments(data, dbType);
        } else {
            showToast('Failed to browse collection: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Collection browse error:', error);
        showToast('Collection browse failed: ' + error.message, 'error');
    });
}

// Display collection documents
function displayCollectionDocuments(data, dbType) {
    const detailsDiv = document.getElementById('collection-details');

    const documentsHtml = `
        <h6>${data.collection} Documents</h6>
        <p class="text-muted">Showing ${data.total_shown} of ${data.total_count || data.documents.length} documents</p>
        <div class="documents-list" style="max-height: 400px; overflow-y: auto;">
            ${data.documents.map((doc, index) => `
                <div class="card mb-2">
                    <div class="card-body p-2">
                        <h6 class="card-title">${doc.id || doc._id || `Document ${index + 1}`}</h6>
                        <p class="card-text small">${doc.content || 'No content available'}</p>
                        ${doc.game_metadata ? `<small class="text-muted"><strong>Game:</strong> ${doc.game_metadata.game_type || 'Unknown'} ${doc.game_metadata.edition || ''} ${doc.game_metadata.book_type || ''}</small><br>` : ''}
                        ${doc.source_file ? `<small class="text-muted"><strong>Source:</strong> ${doc.source_file}</small><br>` : ''}
                        ${doc.sections && Array.isArray(doc.sections) ? `<small class="text-muted"><strong>Sections:</strong> ${doc.sections.length}</small><br>` : ''}
                        ${doc.metadata ? `<small class="text-muted"><strong>Metadata:</strong> ${JSON.stringify(doc.metadata).substring(0, 100)}...</small><br>` : ''}
                        ${doc.word_count ? `<small class="text-muted"><strong>Words:</strong> ${doc.word_count}</small>` : ''}
                        ${doc.page ? `<small class="text-muted"> | <strong>Page:</strong> ${doc.page}</small>` : ''}
                        ${doc.import_date ? `<br><small class="text-muted"><strong>Imported:</strong> ${new Date(doc.import_date).toLocaleDateString()}</small>` : ''}
                    </div>
                </div>
            `).join('')}
        </div>
    `;

    detailsDiv.innerHTML = documentsHtml;
}

// Update progress indicator
function updateProgress(step, state) {
    const stepElement = document.getElementById(`step-${step}`);
    const icon = stepElement.querySelector('i');

    // Reset classes
    stepElement.classList.remove('active', 'completed', 'error');
    icon.classList.remove('fa-circle', 'fa-check-circle', 'fa-spinner', 'fa-pulse', 'fa-exclamation-circle');

    if (state === 'active') {
        stepElement.classList.add('active');
        icon.classList.add('fa-spinner', 'fa-pulse');
    } else if (state === 'completed') {
        stepElement.classList.add('completed');
        icon.classList.add('fa-check-circle');
    } else if (state === 'error') {
        stepElement.classList.add('error');
        icon.classList.add('fa-exclamation-circle');
    } else {
        icon.classList.add('fa-circle');
    }
}

// Show progress for a step
function showProgress(step) {
    updateProgress(step, 'active');
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastBody = document.getElementById('toast-body');

    // Set toast type
    toast.className = `toast toast-${type}`;
    toastBody.textContent = message;

    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// Utility function to format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
