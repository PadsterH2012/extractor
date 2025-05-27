// AI-Powered Extraction v3 UI JavaScript

// Global variables
let currentFile = null;
let currentSessionId = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeFileUpload();
    checkStatus();

    // Initialize temperature slider
    const temperatureSlider = document.getElementById('ai-temperature');
    if (temperatureSlider) {
        temperatureSlider.addEventListener('input', function() {
            document.getElementById('temperature-value').textContent = this.value;
        });
    }
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
    const contentType = document.getElementById('content-type').value;

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
            ai_provider: aiProvider,
            content_type: contentType
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('analysis-progress').style.display = 'none';
        document.getElementById('analyze-btn').disabled = false;

        if (data.success) {
            currentSessionId = data.session_id;
            displayAnalysisResults(data.analysis, data.confidence);
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
function displayAnalysisResults(analysis, confidence) {
    // Store analysis data for metadata editing
    currentAnalysisData = analysis;

    const aiConfidence = analysis.confidence || 0;
    const confidenceClass = aiConfidence > 0.8 ? 'confidence-high' :
                           aiConfidence > 0.5 ? 'confidence-medium' : 'confidence-low';

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
        ${analysis.isbn || analysis.isbn_13 || analysis.isbn_10 ? `
        <div class="analysis-detail">
            <span class="analysis-label">ISBN:</span>
            <span class="analysis-value">${analysis.isbn || analysis.isbn_13 || analysis.isbn_10}</span>
        </div>
        ` : ''}
        <div class="analysis-detail">
            <span class="analysis-label">AI Confidence:</span>
            <span class="confidence-badge ${confidenceClass}">
                ${Math.round(aiConfidence * 100)}%
            </span>
        </div>
    `;

    document.getElementById('analysis-details').innerHTML = resultsHtml;
    document.getElementById('analysis-results').style.display = 'block';

    // Populate metadata review section with confidence data
    populateMetadataReview(analysis, confidence);
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

    // Get text quality settings
    const enableTextEnhancement = document.getElementById('enableTextEnhancement')?.checked ?? true;
    const aggressiveCleanup = document.getElementById('aggressiveCleanup')?.checked ?? false;

    fetch('/extract', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: currentSessionId,
            enable_text_enhancement: enableTextEnhancement,
            aggressive_cleanup: aggressiveCleanup
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
    const textQuality = data.text_quality_metrics;

    let resultsHtml = `
        <div class="extraction-summary">
            <div class="summary-stat">Pages: ${summary.total_pages || 0}</div>
            <div class="summary-stat">Words: ${(summary.total_words || 0).toLocaleString()}</div>
            <div class="summary-stat">Sections: ${data.sections_count || 0}</div>
            ${summary.isbn ? `<div class="summary-stat">ISBN: ${summary.isbn}</div>` : ''}
        </div>
    `;

    // Add text quality metrics if available
    if (textQuality && textQuality.enabled) {
        const qualityBadgeClass = getQualityBadgeClass(textQuality.grade_after || 'F');
        resultsHtml += `
            <div class="text-quality-summary mt-3">
                <h6><i class="fas fa-magic"></i> Text Quality Enhancement</h6>
                <div class="quality-metrics">
                    <div class="quality-stat">
                        <span class="quality-label">Quality:</span>
                        <span class="quality-value">
                            ${textQuality.average_before || 0}% → ${textQuality.average_after || 0}%
                            <span class="badge ${qualityBadgeClass} ms-1">${textQuality.grade_before || 'F'} → ${textQuality.grade_after || 'F'}</span>
                        </span>
                    </div>
                    <div class="quality-stat">
                        <span class="quality-label">Improvement:</span>
                        <span class="quality-value">+${textQuality.improvement || 0}%</span>
                    </div>
                    <div class="quality-stat">
                        <span class="quality-label">Corrections:</span>
                        <span class="quality-value">${textQuality.total_corrections || 0}</span>
                    </div>
                    ${textQuality.aggressive_mode ? '<div class="quality-stat"><span class="badge bg-warning">Aggressive Mode</span></div>' : ''}
                </div>
            </div>
        `;
    } else if (textQuality && !textQuality.enabled) {
        resultsHtml += `
            <div class="text-quality-summary mt-3">
                <h6><i class="fas fa-info-circle"></i> Text Quality Enhancement</h6>
                <div class="alert alert-info small mb-0">
                    ${textQuality.message || 'Text enhancement was not enabled for this extraction.'}
                </div>
            </div>
        `;
    }

    // Add category distribution
    if (summary.category_distribution) {
        resultsHtml += generateCategoryDistribution(summary.category_distribution);
    }

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
function populateMetadataReview(analysis, confidence) {
    document.getElementById('display-content-type').textContent = 
        analysis.content_type ? (analysis.content_type === 'novel' ? 'Novel' : 'Source Material') : 'Source Material';
    document.getElementById('display-game-type').textContent = analysis.game_type || 'Unknown';
    document.getElementById('display-edition').textContent = analysis.edition || 'Unknown';
    document.getElementById('display-book-type').textContent = analysis.book_type || 'Unknown';
    document.getElementById('display-book-title').textContent = analysis.book_full_name || analysis.book_title || 'Unknown';
    document.getElementById('display-collection').textContent = analysis.collection_name || 'Unknown';
    document.getElementById('display-isbn').textContent = analysis.isbn || analysis.isbn_13 || analysis.isbn_10 || 'Not found';

    // Set the dropdown to match the content type
    if (document.getElementById('edit-content-type')) {
        document.getElementById('edit-content-type').value = analysis.content_type || 'source_material';
    }

    // Update confidence display
    if (confidence) {
        const confidenceValue = confidence.quick_confidence || 75;
        const grade = getConfidenceGrade(confidenceValue);
        const badgeClass = getConfidenceBadgeClass(confidenceValue);

        document.getElementById('extraction-confidence-value').textContent = `${confidenceValue.toFixed(1)}%`;
        document.getElementById('extraction-confidence-grade').textContent = grade;
        document.getElementById('extraction-confidence-grade').className = `badge ms-2 ${badgeClass}`;

        // Update detailed confidence info
        document.getElementById('text-confidence').textContent = (confidence.text_confidence || 75).toFixed(1);
        document.getElementById('layout-confidence').textContent = (confidence.layout_confidence || 75).toFixed(1);
        document.getElementById('recommended-method').textContent = confidence.recommended_method || 'text';

        // Show details if confidence is low
        if (confidenceValue < 80) {
            document.getElementById('confidence-details').style.display = 'block';
        }
    }

    // Update path preview
    updatePathPreview();

    // Show metadata review section
    document.getElementById('metadata-review').style.display = 'block';
}

// Get confidence grade letter
function getConfidenceGrade(confidence) {
    if (confidence >= 90) return 'A';
    if (confidence >= 80) return 'B';
    if (confidence >= 70) return 'C';
    if (confidence >= 60) return 'D';
    return 'F';
}

// Get confidence badge CSS class
function getConfidenceBadgeClass(confidence) {
    if (confidence >= 90) return 'bg-success';
    if (confidence >= 80) return 'bg-primary';
    if (confidence >= 70) return 'bg-warning';
    if (confidence >= 60) return 'bg-danger';
    return 'bg-dark';
}

// Get quality badge CSS class
function getQualityBadgeClass(grade) {
    switch(grade) {
        case 'A': return 'bg-success';
        case 'B': return 'bg-primary';
        case 'C': return 'bg-warning';
        case 'D': return 'bg-danger';
        case 'F': return 'bg-dark';
        default: return 'bg-secondary';
    }
}

// Update path preview
function updatePathPreview() {
    const contentType = (document.getElementById('edit-content-type') ? 
                         document.getElementById('edit-content-type').value : 
                         (currentAnalysisData?.content_type || 'source_material'));
    
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
        const path = `${contentType}.${gameType}.${edition}.${bookType}.${collection}`;
        pathTypeElement.textContent = 'Collection:';
        pathPreviewElement.textContent = path;
    } else {
        // Single collection with folder metadata approach
        const folderPath = `${contentType}/${gameType}/${edition}/${bookType}/${collection}`;
        pathTypeElement.textContent = 'Collection: rpger, Folder:';
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
    document.getElementById('edit-content-type').value = currentAnalysisData?.content_type || 'source_material';
    document.getElementById('edit-game-type').value = document.getElementById('display-game-type').textContent;
    document.getElementById('edit-edition').value = document.getElementById('display-edition').textContent;
    document.getElementById('edit-book-type').value = document.getElementById('display-book-type').textContent;
    document.getElementById('edit-book-title').value = document.getElementById('display-book-title').textContent;
    document.getElementById('edit-collection').value = document.getElementById('display-collection').textContent;
    document.getElementById('edit-isbn').value = document.getElementById('display-isbn').textContent;

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
    document.getElementById('display-content-type').textContent = 
        document.getElementById('edit-content-type').value === 'novel' ? 'Novel' : 'Source Material';
    document.getElementById('display-game-type').textContent = document.getElementById('edit-game-type').value;
    document.getElementById('display-edition').textContent = document.getElementById('edit-edition').value;
    document.getElementById('display-book-type').textContent = document.getElementById('edit-book-type').value;
    document.getElementById('display-book-title').textContent = document.getElementById('edit-book-title').value;
    document.getElementById('display-collection').textContent = document.getElementById('edit-collection').value;
    document.getElementById('display-isbn').textContent = document.getElementById('edit-isbn').value;

    // Update stored analysis data
    if (currentAnalysisData) {
        currentAnalysisData.content_type = document.getElementById('edit-content-type').value;
        currentAnalysisData.game_type = document.getElementById('edit-game-type').value;
        currentAnalysisData.edition = document.getElementById('edit-edition').value;
        currentAnalysisData.book_type = document.getElementById('edit-book-type').value;
        currentAnalysisData.book_full_name = document.getElementById('edit-book-title').value;
        currentAnalysisData.collection_name = document.getElementById('edit-collection').value;
        currentAnalysisData.isbn = document.getElementById('edit-isbn').value;
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
        content_type: currentAnalysisData.content_type || 'source_material',
        game_type: currentAnalysisData.game_type,
        edition: currentAnalysisData.edition,
        book_type: currentAnalysisData.book_type,
        book_full_name: currentAnalysisData.book_full_name,
        collection_name: currentAnalysisData.collection_name,
        isbn: currentAnalysisData.isbn
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
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${dbType} Collections Browser</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-0">
                        <div class="row g-0" style="min-height: 600px;">
                            <div class="col-md-4">
                                <div class="collections-sidebar">
                                    <div class="collections-header">
                                        <h6 class="mb-0">Collections</h6>
                                        <span class="collections-count">${collections.length}</span>
                                    </div>

                                    <div class="collection-search">
                                        <input type="text" class="form-control" placeholder="Search collections..."
                                               id="collection-search-input" onkeyup="filterCollections()">
                                        <i class="fas fa-search search-icon"></i>
                                    </div>

                                    <div id="collections-list" style="max-height: 450px; overflow-y: auto;">
                                        ${generateCollectionItems(collections, dbKey)}
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-8">
                                <div class="documents-panel">
                                    <div id="collection-details">
                                        <div class="documents-empty">
                                            <i class="fas fa-database"></i>
                                            <h6>Select a Collection</h6>
                                            <p class="mb-0">Choose a collection from the sidebar to view its documents</p>
                                        </div>
                                    </div>
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

    // Store collections data for filtering
    window.currentCollections = collections;
    window.currentDbKey = dbKey;

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('databaseBrowserModal'));
    modal.show();
}

// Generate collection items HTML
function generateCollectionItems(collections, dbKey) {
    return collections.map(col => {
        const collectionType = getCollectionType(col.name);
        const icon = getCollectionIcon(collectionType);
        const hierarchicalPath = getHierarchicalPath(col.name);

        return `
            <div class="collection-item" data-name="${col.name.toLowerCase()}"
                 onclick="selectCollection(this, '${dbKey}', '${col.name}')">
                <div class="p-3">
                    <div class="collection-header">
                        <div class="collection-name">
                            <div class="collection-icon ${collectionType}">
                                <i class="fas ${icon}"></i>
                            </div>
                            ${formatCollectionName(col.name)}
                        </div>
                        <span class="collection-count">${col.document_count || 0}</span>
                    </div>

                    <div class="collection-meta">
                        ${col.game_type ? `<div><strong>Game:</strong> ${col.game_type}</div>` : ''}
                        ${col.sample_fields ? `<div><strong>Fields:</strong> ${col.sample_fields.slice(0,3).join(', ')}</div>` : ''}
                        <div class="collection-path">${hierarchicalPath}</div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Get collection type from name
function getCollectionType(name) {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('monster')) return 'monsters';
    if (lowerName.includes('spell')) return 'spells';
    if (lowerName.includes('item')) return 'items';
    if (lowerName.includes('character')) return 'characters';
    if (lowerName.includes('npc')) return 'npcs';
    if (lowerName.includes('source_material')) return 'source_material';
    return 'default';
}

// Get icon for collection type
function getCollectionIcon(type) {
    const icons = {
        monsters: 'fa-dragon',
        spells: 'fa-magic',
        items: 'fa-gem',
        characters: 'fa-user',
        npcs: 'fa-users',
        source_material: 'fa-book',
        default: 'fa-database'
    };
    return icons[type] || icons.default;
}

// Format collection name for display
function formatCollectionName(name) {
    // Remove prefixes and make more readable
    return name.replace(/^source_material\./, '')
               .replace(/\./g, ' › ')
               .replace(/_/g, ' ')
               .split(' ')
               .map(word => word.charAt(0).toUpperCase() + word.slice(1))
               .join(' ');
}

// Get hierarchical path
function getHierarchicalPath(name) {
    if (name.startsWith('source_material.')) {
        return `rpger.${name}`;
    }
    return `rpger.${name}`;
}

// Filter collections based on search
function filterCollections() {
    const searchTerm = document.getElementById('collection-search-input').value.toLowerCase();
    const collectionItems = document.querySelectorAll('.collection-item');

    collectionItems.forEach(item => {
        const name = item.dataset.name;
        const isVisible = name.includes(searchTerm);
        item.style.display = isVisible ? 'block' : 'none';
    });
}

// Select collection
function selectCollection(element, dbKey, collectionName) {
    // Remove active class from all items
    document.querySelectorAll('.collection-item').forEach(item => {
        item.classList.remove('active');
    });

    // Add active class to selected item
    element.classList.add('active');

    // Show loading state
    showCollectionLoading(collectionName);

    // Browse collection
    browseCollection(dbKey, collectionName);
}

// Show loading state for collection
function showCollectionLoading(collectionName) {
    const detailsDiv = document.getElementById('collection-details');
    detailsDiv.innerHTML = `
        <div class="documents-header">
            <h6 class="documents-title">
                <i class="fas fa-spinner fa-spin"></i>
                Loading ${formatCollectionName(collectionName)}
            </h6>
        </div>
        <div class="loading-content">
            ${Array(5).fill(0).map(() => `
                <div class="document-card">
                    <div class="document-card-body">
                        <div class="loading-skeleton" style="width: 60%; height: 16px;"></div>
                        <div class="loading-skeleton" style="width: 100%; height: 12px;"></div>
                        <div class="loading-skeleton" style="width: 100%; height: 12px;"></div>
                        <div class="loading-skeleton" style="width: 80%; height: 12px;"></div>
                        <div style="display: flex; gap: 8px; margin-top: 8px;">
                            <div class="loading-skeleton" style="width: 60px; height: 20px;"></div>
                            <div class="loading-skeleton" style="width: 80px; height: 20px;"></div>
                            <div class="loading-skeleton" style="width: 50px; height: 20px;"></div>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
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
        <div class="documents-header">
            <h6 class="documents-title">
                <i class="fas fa-file-alt"></i>
                ${formatCollectionName(data.collection)}
            </h6>
            <div class="documents-stats">
                Showing ${data.total_shown} of ${data.total_count || data.documents.length} documents
            </div>
        </div>

        <div class="documents-list" style="max-height: 450px; overflow-y: auto;">
            ${data.documents.length > 0 ? data.documents.map((doc, index) => `
                <div class="document-card">
                    <div class="document-card-body">
                        <div class="document-title">
                            <i class="fas fa-file-text"></i>
                            ${doc.id || doc._id || `Document ${index + 1}`}
                        </div>

                        <div class="document-content">
                            ${doc.content || 'No content available'}
                        </div>

                        <div class="document-meta">
                            ${doc.game_metadata ? `
                                <span class="meta-tag game">
                                    ${doc.game_metadata.game_type || 'Unknown'}
                                    ${doc.game_metadata.edition || ''}
                                    ${doc.game_metadata.book_type || ''}
                                </span>
                            ` : ''}

                            ${doc.source_file ? `
                                <span class="meta-tag source">
                                    <i class="fas fa-file"></i> ${doc.source_file}
                                </span>
                            ` : ''}

                            ${doc.isbn || doc.isbn_13 || doc.isbn_10 ? `
                                <span class="meta-tag isbn">
                                    <i class="fas fa-barcode"></i> ISBN: ${doc.isbn || doc.isbn_13 || doc.isbn_10}
                                </span>
                            ` : ''}

                            ${doc.page ? `
                                <span class="meta-tag page">
                                    <i class="fas fa-bookmark"></i> Page ${doc.page}
                                </span>
                            ` : ''}

                            ${doc.word_count ? `
                                <span class="meta-tag words">
                                    <i class="fas fa-font"></i> ${doc.word_count} words
                                </span>
                            ` : ''}

                            ${doc.sections && Array.isArray(doc.sections) ? `
                                <span class="meta-tag">
                                    <i class="fas fa-list"></i> ${doc.sections.length} sections
                                </span>
                            ` : ''}

                            ${doc.import_date ? `
                                <span class="meta-tag">
                                    <i class="fas fa-calendar"></i> ${new Date(doc.import_date).toLocaleDateString()}
                                </span>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `).join('') : `
                <div class="documents-empty">
                    <i class="fas fa-inbox"></i>
                    <h6>No Documents Found</h6>
                    <p class="mb-0">This collection appears to be empty</p>
                </div>
            `}
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

// Settings Management
function openSettings() {
    // Load current settings
    loadSettings();

    // Show modal
    const settingsModal = new bootstrap.Modal(document.getElementById('settingsModal'));
    settingsModal.show();
}

function loadSettings() {
    fetch('/get_settings')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const settings = data.settings;

                // AI Configuration
                document.getElementById('anthropic-api-key').value = settings.ANTHROPIC_API_KEY || '';
                document.getElementById('openai-api-key').value = settings.OPENAI_API_KEY || '';
                document.getElementById('local-llm-url').value = settings.LOCAL_LLM_URL || 'http://localhost:11434';

                // Database Configuration
                document.getElementById('chromadb-host').value = settings.CHROMADB_HOST || '10.202.28.49';
                document.getElementById('chromadb-port').value = settings.CHROMADB_PORT || '8000';
                document.getElementById('mongodb-host').value = settings.MONGODB_HOST || '10.202.28.46';
                document.getElementById('mongodb-port').value = settings.MONGODB_PORT || '27017';
                document.getElementById('mongodb-database').value = settings.MONGODB_DATABASE || 'rpger';

                // Advanced Settings
                const temperature = parseFloat(settings.AI_TEMPERATURE || '0.3');
                document.getElementById('ai-temperature').value = temperature;
                document.getElementById('temperature-value').textContent = temperature;
                document.getElementById('ai-max-tokens').value = settings.AI_MAX_TOKENS || '4000';
                document.getElementById('ai-timeout').value = settings.AI_TIMEOUT || '60';
                document.getElementById('ai-retries').value = settings.AI_RETRIES || '3';
            } else {
                showToast('Failed to load settings: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Settings load error:', error);
            showToast('Failed to load settings', 'error');
        });
}

function saveSettings() {
    const settings = {
        // AI Configuration
        ANTHROPIC_API_KEY: document.getElementById('anthropic-api-key').value,
        OPENAI_API_KEY: document.getElementById('openai-api-key').value,
        LOCAL_LLM_URL: document.getElementById('local-llm-url').value,

        // Database Configuration
        CHROMADB_HOST: document.getElementById('chromadb-host').value,
        CHROMADB_PORT: document.getElementById('chromadb-port').value,
        MONGODB_HOST: document.getElementById('mongodb-host').value,
        MONGODB_PORT: document.getElementById('mongodb-port').value,
        MONGODB_DATABASE: document.getElementById('mongodb-database').value,

        // Advanced Settings
        AI_TEMPERATURE: document.getElementById('ai-temperature').value,
        AI_MAX_TOKENS: document.getElementById('ai-max-tokens').value,
        AI_TIMEOUT: document.getElementById('ai-timeout').value,
        AI_RETRIES: document.getElementById('ai-retries').value
    };

    fetch('/save_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ settings: settings })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Settings saved successfully!', 'success');

            // Close modal
            const settingsModal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
            settingsModal.hide();

            // Refresh status to show updated connections
            setTimeout(() => {
                checkStatus();
            }, 1000);
        } else {
            showToast('Failed to save settings: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Settings save error:', error);
        showToast('Failed to save settings', 'error');
    });
}

function togglePasswordVisibility(fieldId) {
    const field = document.getElementById(fieldId);
    const button = field.nextElementSibling.querySelector('i');

    if (field.type === 'password') {
        field.type = 'text';
        button.className = 'fas fa-eye-slash';
    } else {
        field.type = 'password';
        button.className = 'fas fa-eye';
    }
}

// Utility function to format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
