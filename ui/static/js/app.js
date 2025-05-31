// AI-Powered Extraction v3 UI JavaScript

// Global variables
let currentFile = null;
let currentSessionId = null;
let openRouterModels = null;
let sessionTokens = 0;
let sessionApiCalls = 0;
let sessionCost = 0;
let currentContentType = 'source_material';
let savedSettings = {};

// Model memory and recent models management
const MODEL_MEMORY_KEY = 'last_selected_model';
const RECENT_MODELS_KEY = 'recent_models';
const MAX_RECENT_MODELS = 5;

// Model memory functions
function getLastSelectedModel() {
    try {
        return localStorage.getItem(MODEL_MEMORY_KEY);
    } catch (e) {
        console.warn('Failed to get last selected model from localStorage:', e);
        return null;
    }
}

function saveLastSelectedModel(modelId) {
    try {
        localStorage.setItem(MODEL_MEMORY_KEY, modelId);
        console.log('💾 Saved last selected model:', modelId);
    } catch (e) {
        console.warn('Failed to save last selected model to localStorage:', e);
    }
}

function getRecentModels() {
    try {
        const recent = localStorage.getItem(RECENT_MODELS_KEY);
        return recent ? JSON.parse(recent) : [];
    } catch (e) {
        console.warn('Failed to get recent models from localStorage:', e);
        return [];
    }
}

function addToRecentModels(modelId) {
    try {
        let recentModels = getRecentModels();

        // Remove if already exists
        recentModels = recentModels.filter(id => id !== modelId);

        // Add to beginning
        recentModels.unshift(modelId);

        // Keep only MAX_RECENT_MODELS
        recentModels = recentModels.slice(0, MAX_RECENT_MODELS);

        localStorage.setItem(RECENT_MODELS_KEY, JSON.stringify(recentModels));
        console.log('📋 Updated recent models:', recentModels);

        return recentModels;
    } catch (e) {
        console.warn('Failed to update recent models in localStorage:', e);
        return [];
    }
}

function recordModelUsage(modelId) {
    if (!modelId) return;

    console.log('📊 Recording model usage:', modelId);
    saveLastSelectedModel(modelId);
    addToRecentModels(modelId);

    // Reorder dropdown if it exists
    reorderModelDropdown();
}

function reorderModelDropdown() {
    const modelSelect = document.getElementById('main-ai-model');
    if (!modelSelect || !openRouterModels) return;

    console.log('🔄 Reordering model dropdown...');

    const recentModels = getRecentModels();
    const currentValue = modelSelect.value;

    // Clear existing options
    modelSelect.innerHTML = '';

    // Create arrays for different categories
    const recentOptions = [];
    const otherOptions = [];

    // Categorize models (only process option models, not headers)
    openRouterModels.forEach(model => {
        if (model.type === 'option') {
            if (recentModels.includes(model.value)) {
                recentOptions.push(model);
            } else {
                otherOptions.push(model);
            }
        }
    });

    // Sort recent options by their position in recentModels array
    recentOptions.sort((a, b) => {
        return recentModels.indexOf(a.value) - recentModels.indexOf(b.value);
    });

    // Add recent models section
    if (recentOptions.length > 0) {
        const recentGroup = document.createElement('optgroup');
        recentGroup.label = '🕒 Recently Used';

        recentOptions.forEach(model => {
            const option = document.createElement('option');
            option.value = model.value;
            option.textContent = model.label;
            option.setAttribute('data-description', model.description);
            option.setAttribute('data-provider', model.provider);
            if (model.pricing) {
                option.setAttribute('data-pricing', JSON.stringify(model.pricing));
            }
            recentGroup.appendChild(option);
        });

        modelSelect.appendChild(recentGroup);
    }

    // Add separator and other models
    if (otherOptions.length > 0) {
        const otherGroup = document.createElement('optgroup');
        otherGroup.label = '📋 All Models';

        otherOptions.forEach(model => {
            const option = document.createElement('option');
            option.value = model.value;
            option.textContent = model.label;
            option.setAttribute('data-description', model.description);
            option.setAttribute('data-provider', model.provider);
            if (model.pricing) {
                option.setAttribute('data-pricing', JSON.stringify(model.pricing));
            }
            otherGroup.appendChild(option);
        });

        modelSelect.appendChild(otherGroup);
    }

    // Restore selected value
    if (currentValue) {
        modelSelect.value = currentValue;
    }

    console.log('✅ Model dropdown reordered');
}

// Initialize session tracking from UI values
function initializeSessionTracking() {
    // Get current values from UI
    const sessionTokensElement = document.getElementById('session-tokens');
    const sessionApiCallsElement = document.getElementById('session-api-calls');

    if (sessionTokensElement) {
        const tokensText = sessionTokensElement.textContent;
        const tokensMatch = tokensText.match(/(\d+(?:,\d+)*)/);
        if (tokensMatch) {
            sessionTokens = parseInt(tokensMatch[1].replace(/,/g, ''));
            console.log('📊 Initialized session tokens from UI:', sessionTokens);
        }
    }

    if (sessionApiCallsElement) {
        const callsText = sessionApiCallsElement.textContent;
        const callsMatch = callsText.match(/(\d+)/);
        if (callsMatch) {
            sessionApiCalls = parseInt(callsMatch[1]);
            console.log('📊 Initialized session API calls from UI:', sessionApiCalls);
        }
    }

    // Calculate initial cost
    recalculateSessionCost();
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeFileUpload();
    initializeProgressTracking();
    initializeAIProviderManagement();
    initializeMainAIProvider(); // Initialize main AI provider
    loadSavedSettings();
    checkStatus();

    // Initialize session tracking after a short delay to ensure UI is loaded
    setTimeout(() => {
        initializeSessionTracking();
        updateSessionTracking();
    }, 500);

    // Initialize temperature slider
    const temperatureSlider = document.getElementById('ai-temperature');
    if (temperatureSlider) {
        temperatureSlider.addEventListener('input', function() {
            document.getElementById('temperature-value').textContent = this.value;
        });
    }

    // Initialize content type change handler
    const contentTypeSelect = document.getElementById('content-type');
    if (contentTypeSelect) {
        contentTypeSelect.addEventListener('change', onContentTypeChange);
    }
});

// Card collapse/expand functionality
function collapseCard(cardId) {
    const card = document.getElementById(cardId);
    if (card) {
        const cardBody = card.querySelector('.card-body');
        const cardHeader = card.querySelector('.card-header');

        if (cardBody && cardHeader) {
            // Add collapsed class and hide body
            card.classList.add('collapsed');
            cardBody.style.display = 'none';

            // Add collapse indicator to header
            let collapseIcon = cardHeader.querySelector('.collapse-icon');
            if (!collapseIcon) {
                collapseIcon = document.createElement('i');
                collapseIcon.className = 'fas fa-chevron-down collapse-icon ms-2';
                cardHeader.querySelector('h5').appendChild(collapseIcon);
            } else {
                collapseIcon.className = 'fas fa-chevron-down collapse-icon ms-2';
            }

            // Make header clickable to expand
            cardHeader.style.cursor = 'pointer';
            cardHeader.onclick = () => expandCard(cardId);
        }
    }
}

function expandCard(cardId) {
    const card = document.getElementById(cardId);
    if (card) {
        const cardBody = card.querySelector('.card-body');
        const cardHeader = card.querySelector('.card-header');

        if (cardBody && cardHeader) {
            // Remove collapsed class and show body
            card.classList.remove('collapsed');
            cardBody.style.display = 'block';

            // Update collapse indicator
            const collapseIcon = cardHeader.querySelector('.collapse-icon');
            if (collapseIcon) {
                collapseIcon.className = 'fas fa-chevron-up collapse-icon ms-2';
            }

            // Update click handler to collapse
            cardHeader.onclick = () => collapseCard(cardId);
        }
    }
}

function autoProgressWorkflow() {
    // Auto-collapse Step 1 and expand Step 2 after successful upload
    setTimeout(() => {
        collapseCard('upload-card');
        expandCard('analysis-card');

        // Smooth scroll to Step 2
        const analysisCard = document.getElementById('analysis-card');
        if (analysisCard) {
            analysisCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 500); // Small delay for smooth transition
}

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
            autoProgressWorkflow(); // Auto-collapse Step 1 and expand Step 2
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

// Handle main AI provider change
function onMainProviderChange() {
    const provider = document.getElementById('main-ai-provider').value;
    const modelContainer = document.getElementById('main-model-selection-container');

    // Save preference
    localStorage.setItem('preferred_ai_provider', provider);

    // Update hidden inputs for compatibility
    document.getElementById('ai-provider').value = provider;

    if (provider === 'openrouter') {
        modelContainer.style.display = 'block';
        loadMainOpenRouterModels();
    } else {
        modelContainer.style.display = 'none';
        document.getElementById('ai-model').value = '';
    }

    // Update system status to reflect new provider
    checkStatus();
}

// Handle AI provider change (legacy compatibility)
function onProviderChange() {
    // This function is kept for compatibility but now syncs with main provider
    const provider = document.getElementById('ai-provider').value;
    const mainProvider = document.getElementById('main-ai-provider');
    if (mainProvider && mainProvider.value !== provider) {
        mainProvider.value = provider;
        onMainProviderChange();
    }
}

// Load OpenRouter models
async function loadOpenRouterModels(forceRefresh = false) {
    const modelSelect = document.getElementById('ai-model');
    const modelDescription = document.getElementById('model-description');

    try {
        // Show loading state
        modelSelect.innerHTML = '<option value="">Loading models...</option>';
        modelDescription.textContent = 'Loading available models...';

        // Fetch models from API
        const response = await fetch(`/api/openrouter/models?refresh=${forceRefresh}&group=true`);
        const data = await response.json();

        if (data.success) {
            openRouterModels = data.models;
            populateModelDropdown(data.models, data.recommended);
            modelDescription.textContent = `${data.total_models} models available`;
            
            // Refresh token tracking if this was a forced refresh (API call made)
            if (forceRefresh) {
                setTimeout(refreshTokenTracking, 500);
            }
        } else {
            throw new Error(data.error || 'Failed to load models');
        }

    } catch (error) {
        console.error('Error loading OpenRouter models:', error);
        modelSelect.innerHTML = '<option value="">Error loading models</option>';
        modelDescription.textContent = 'Failed to load models. Check API key.';
        showToast('Failed to load OpenRouter models: ' + error.message, 'error');
    }
}

// Populate model dropdown with grouped options
function populateModelDropdown(models, recommended = []) {
    const modelSelect = document.getElementById('ai-model');
    modelSelect.innerHTML = '';

    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Select a model...';
    modelSelect.appendChild(defaultOption);

    // Add recommended section first
    if (recommended.length > 0) {
        const recommendedGroup = document.createElement('optgroup');
        recommendedGroup.label = '⭐ Recommended for Character Analysis';

        models.filter(model => model.type === 'option' && recommended.includes(model.value))
              .forEach(model => {
                  const option = document.createElement('option');
                  option.value = model.value;
                  option.textContent = model.label;
                  option.setAttribute('data-description', model.description);
                  option.setAttribute('data-provider', model.provider);
                  recommendedGroup.appendChild(option);
              });

        if (recommendedGroup.children.length > 0) {
            modelSelect.appendChild(recommendedGroup);
        }
    }

    // Add all models grouped by provider
    let currentGroup = null;
    models.forEach(model => {
        if (model.type === 'header') {
            currentGroup = document.createElement('optgroup');
            currentGroup.label = model.label;
            modelSelect.appendChild(currentGroup);
        } else if (model.type === 'option' && currentGroup) {
            const option = document.createElement('option');
            option.value = model.value;
            option.textContent = model.label;
            option.setAttribute('data-description', model.description);
            option.setAttribute('data-provider', model.provider);
            currentGroup.appendChild(option);
        }
    });

    // Add change event listener to show model description
    modelSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        const description = selectedOption.getAttribute('data-description') || 'No description available';
        const provider = selectedOption.getAttribute('data-provider') || '';

        const modelDescription = document.getElementById('model-description');
        if (this.value) {
            modelDescription.textContent = `${provider}: ${description}`;
        } else {
            modelDescription.textContent = 'Select a model for analysis';
        }
    });
}

// Load main OpenRouter models
async function loadMainOpenRouterModels(forceRefresh = false) {
    const modelSelect = document.getElementById('main-ai-model');
    const modelDescription = document.getElementById('main-model-description');

    try {
        // Show loading state
        modelSelect.innerHTML = '<option value="">Loading models...</option>';
        modelDescription.textContent = 'Loading available models...';

        // Fetch models from API
        const response = await fetch(`/api/openrouter/models?refresh=${forceRefresh}&group=true`);
        const data = await response.json();

        if (data.success) {
            openRouterModels = data.models;
            populateMainModelDropdown(data.models, data.recommended);
            modelDescription.textContent = `${data.total_models} models available`;

            // Restore last selected model
            const lastSelectedModel = getLastSelectedModel();
            if (lastSelectedModel && !forceRefresh) {
                const modelExists = data.models.some(m => m.value === lastSelectedModel);
                if (modelExists) {
                    modelSelect.value = lastSelectedModel;
                    console.log('🔄 Restored last selected model:', lastSelectedModel);

                    // Trigger change event to update description
                    modelSelect.dispatchEvent(new Event('change'));
                }
            }

            // Apply recent model ordering
            reorderModelDropdown();

            // Update hidden input for compatibility
            const selectedModel = modelSelect.value;
            document.getElementById('ai-model').value = selectedModel;
            
            // Refresh token tracking if this was a forced refresh (API call made)
            if (forceRefresh) {
                setTimeout(refreshTokenTracking, 500);
            }
        } else {
            throw new Error(data.error || 'Failed to load models');
        }

    } catch (error) {
        console.error('Error loading OpenRouter models:', error);
        modelSelect.innerHTML = '<option value="">Error loading models</option>';
        modelDescription.textContent = 'Failed to load models. Check API key.';
        showToast('Failed to load OpenRouter models: ' + error.message, 'error');
    }
}

// Populate main model dropdown
function populateMainModelDropdown(models, recommended = []) {
    const modelSelect = document.getElementById('main-ai-model');
    modelSelect.innerHTML = '';

    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Select a model...';
    modelSelect.appendChild(defaultOption);

    // Add recommended section first
    if (recommended.length > 0) {
        const recommendedGroup = document.createElement('optgroup');
        recommendedGroup.label = '⭐ Recommended for Character Analysis';

        models.filter(model => model.type === 'option' && recommended.includes(model.value))
              .forEach(model => {
                  const option = document.createElement('option');
                  option.value = model.value;
                  option.textContent = model.label;
                  option.setAttribute('data-description', model.description);
                  option.setAttribute('data-provider', model.provider);
                  if (model.pricing) {
                      option.setAttribute('data-pricing', JSON.stringify(model.pricing));
                  }
                  recommendedGroup.appendChild(option);
              });

        if (recommendedGroup.children.length > 0) {
            modelSelect.appendChild(recommendedGroup);
        }
    }

    // Add all models grouped by provider
    let currentGroup = null;
    models.forEach(model => {
        if (model.type === 'header') {
            currentGroup = document.createElement('optgroup');
            currentGroup.label = model.label;
            modelSelect.appendChild(currentGroup);
        } else if (model.type === 'option' && currentGroup) {
            const option = document.createElement('option');
            option.value = model.value;
            option.textContent = model.label;
            option.setAttribute('data-description', model.description);
            option.setAttribute('data-provider', model.provider);
            if (model.pricing) {
                option.setAttribute('data-pricing', JSON.stringify(model.pricing));
            }
            currentGroup.appendChild(option);
        }
    });

    // Add change event listener to show model description
    modelSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        const description = selectedOption.getAttribute('data-description') || 'No description available';
        const provider = selectedOption.getAttribute('data-provider') || '';
        const pricing = selectedOption.getAttribute('data-pricing');

        const modelDescription = document.getElementById('main-model-description');
        if (this.value) {
            let descriptionText = `${provider}: ${description}`;

            // Add pricing information if available
            if (pricing) {
                try {
                    const pricingData = JSON.parse(pricing);
                    if (pricingData.prompt && pricingData.completion) {
                        // OpenRouter pricing is per token, convert to per 1M tokens for display
                        const promptCostPerToken = parseFloat(pricingData.prompt);
                        const completionCostPerToken = parseFloat(pricingData.completion);
                        const promptCostPer1M = promptCostPerToken * 1000000;
                        const completionCostPer1M = completionCostPerToken * 1000000;

                        console.log('💰 Pricing debug - Raw:', pricingData, 'Per 1M:', promptCostPer1M, completionCostPer1M);

                        descriptionText += ` | $${promptCostPer1M.toFixed(3)}/$${completionCostPer1M.toFixed(3)} per 1M tokens`;
                    }
                } catch (e) {
                    console.warn('Failed to parse pricing data:', e);
                }
            }

            modelDescription.textContent = descriptionText;
        } else {
            modelDescription.textContent = 'Select a model for analysis';
        }

        // Update hidden input for compatibility
        document.getElementById('ai-model').value = this.value;

        // Record model usage for memory and recent models
        if (this.value) {
            recordModelUsage(this.value);
        }

        // Recalculate session cost when model changes
        recalculateSessionCost();
    });
}

// Refresh main models
function refreshMainModels() {
    const provider = document.getElementById('main-ai-provider').value;
    if (provider === 'openrouter') {
        loadMainOpenRouterModels(true);
    }
}

// Refresh models (legacy compatibility)
function refreshModels() {
    refreshMainModels();
}

// Initialize main AI provider configuration
function initializeMainAIProvider() {
    // Set default provider
    const mainProvider = document.getElementById('main-ai-provider');
    if (mainProvider) {
        // Check for saved preference or use default
        const savedProvider = localStorage.getItem('preferred_ai_provider') || 'mock';
        mainProvider.value = savedProvider;

        // Sync with hidden input
        document.getElementById('ai-provider').value = savedProvider;

        // Initialize model selection if OpenRouter
        if (savedProvider === 'openrouter') {
            onMainProviderChange();
        }
    }
}

// Calculate cost for tokens based on current model
function calculateTokenCost(tokens, modelId = null) {
    console.log('🔍 Calculating cost for', tokens, 'tokens, modelId:', modelId);

    if (!modelId) {
        const provider = document.getElementById('main-ai-provider')?.value || 'mock';
        console.log('🔍 Current provider:', provider);

        if (provider !== 'openrouter') {
            console.log('🔍 Non-OpenRouter provider, returning 0 cost');
            return 0; // No cost for non-OpenRouter providers
        }
        modelId = document.getElementById('main-ai-model')?.value;
        console.log('🔍 Selected model ID:', modelId);
    }

    if (!modelId) {
        console.log('🔍 No model ID, returning 0 cost');
        return 0;
    }

    if (!openRouterModels) {
        console.log('🔍 No cached models, returning 0 cost');
        return 0;
    }

    // Find the model in our cached models
    const model = openRouterModels.find(m => m.value === modelId);
    console.log('🔍 Found model:', model);

    if (!model || !model.pricing) {
        console.log('🔍 No model or pricing data, returning 0 cost');
        return 0;
    }

    // OpenRouter pricing is per token (not per 1M tokens)
    const promptCostPerToken = parseFloat(model.pricing.prompt) || 0;
    const completionCostPerToken = parseFloat(model.pricing.completion) || 0;

    console.log('🔍 Pricing - Prompt per token:', promptCostPerToken, 'Completion per token:', completionCostPerToken);

    // Use average of prompt and completion cost for estimation
    const avgCostPerToken = (promptCostPerToken + completionCostPerToken) / 2;
    const totalCost = tokens * avgCostPerToken;

    console.log('🔍 Calculated cost:', totalCost, 'for', tokens, 'tokens');

    return totalCost;
}

// Reset session tracking
function resetSessionTracking() {
    sessionTokens = 0;
    sessionApiCalls = 0;
    sessionCost = 0;
    updateSessionTracking();
}

// Recalculate session cost based on current model
function recalculateSessionCost() {
    if (sessionTokens > 0) {
        console.log('🔄 Recalculating session cost for', sessionTokens, 'tokens');
        sessionCost = calculateTokenCost(sessionTokens);
        console.log('💰 Recalculated session cost:', sessionCost);
        updateSessionTracking();
    }
    
    // Also refresh token tracking from server to get latest data
    refreshTokenTracking();
}

// Update session tracking display
function updateSessionTracking() {
    const sessionTokensElement = document.getElementById('session-tokens');
    const sessionApiCallsElement = document.getElementById('session-api-calls');
    const sessionCostElement = document.getElementById('session-cost');

    console.log('📊 Updating display - Tokens:', sessionTokens, 'Cost:', sessionCost, 'API Calls:', sessionApiCalls);

    if (sessionTokensElement) {
        sessionTokensElement.textContent = sessionTokens.toLocaleString();
    }

    if (sessionApiCallsElement) {
        sessionApiCallsElement.textContent = sessionApiCalls;
    }

    if (sessionCostElement) {
        sessionCostElement.textContent = `$${sessionCost.toFixed(4)}`;
    }
}

// Refresh token tracking from server
function refreshTokenTracking() {
    if (!currentSessionId) return;

    fetch(`/status?session_id=${currentSessionId}`)
    .then(response => response.json())
    .then(data => {
        if (data.token_tracking && (data.token_tracking.total_tokens > 0 || data.token_tracking.total_api_calls > 0)) {
            console.log('🔄 Refreshed token tracking:', data.token_tracking);
            sessionTokens = data.token_tracking.total_tokens;
            sessionApiCalls = data.token_tracking.total_api_calls;
            sessionCost = data.token_tracking.total_cost;
            updateSessionTracking();
        }
    })
    .catch(error => {
        console.error('Token tracking refresh error:', error);
    });
}

// Analyze PDF with AI
function analyzePDF() {
    if (!currentFile) {
        showToast('Please upload a file first', 'error');
        return;
    }

    // Get AI provider from main configuration
    const aiProvider = document.getElementById('main-ai-provider').value;
    const contentType = document.getElementById('content-type').value;

    // Update hidden inputs for compatibility
    document.getElementById('ai-provider').value = aiProvider;

    // Get selected model for OpenRouter
    let selectedModel = null;
    if (aiProvider === 'openrouter') {
        selectedModel = document.getElementById('main-ai-model').value;
        if (!selectedModel) {
            showToast('Please select a model for OpenRouter', 'error');
            return;
        }
        // Update hidden input for compatibility
        document.getElementById('ai-model').value = selectedModel;
    }

    document.getElementById('analyze-btn').disabled = true;
    document.getElementById('analysis-progress').style.display = 'block';
    updateProgress('analyze', 'active');

    // Prepare request body
    const requestBody = {
        filepath: currentFile.filepath,
        ai_provider: aiProvider,
        content_type: contentType
    };

    // Add model selection for OpenRouter
    if (selectedModel) {
        requestBody.ai_model = selectedModel;
        // Record model usage when starting analysis
        recordModelUsage(selectedModel);
    }

    fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
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

            // Update session tracking
            sessionApiCalls += 1;

            if (data.tokens_used) {
                console.log('📊 Adding', data.tokens_used, 'tokens to session');
                sessionTokens += data.tokens_used;

                // Calculate and add cost
                const tokenCost = calculateTokenCost(data.tokens_used);
                console.log('💰 Calculated cost:', tokenCost);
                sessionCost += tokenCost;

                console.log('📊 Session totals - Tokens:', sessionTokens, 'Cost:', sessionCost, 'API Calls:', sessionApiCalls);
            }

            updateSessionTracking();
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

    // Start progress polling for novel extraction
    if (currentContentType === 'novel') {
        startProgressPolling(currentSessionId);
    }

    // Text enhancement disabled - will be handled post-extraction in MongoDB
    const enableTextEnhancement = false;
    const aggressiveCleanup = false;

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
    .then(response => {
        // Handle different response status codes
        if (response.status === 409) {
            // ISBN duplicate error
            return response.json().then(data => {
                throw new Error(`ISBN_DUPLICATE:${JSON.stringify(data)}`);
            });
        }
        return response.json();
    })
    .then(data => {
        // Stop progress polling
        stopProgressPolling();

        document.getElementById('extraction-progress').style.display = 'none';
        document.getElementById('extract-btn').disabled = false;

        if (data.success) {
            displayExtractionResults(data);
            updateProgress('extract', 'completed');
            showImportCard();
            showToast('Content extracted successfully', 'success');

            // Update session tracking with extraction token usage
            if (data.token_usage) {
                console.log('📊 Extraction token usage:', data.token_usage);
                sessionTokens += data.token_usage.total_tokens;
                sessionApiCalls += data.token_usage.total_api_calls;
                sessionCost += data.token_usage.total_cost;

                console.log('📊 Updated session totals - Tokens:', sessionTokens, 'Cost:', sessionCost, 'API Calls:', sessionApiCalls);
                updateSessionTracking();
            }

            // Refresh token tracking from server to ensure accuracy
            setTimeout(refreshTokenTracking, 1000);
        } else {
            showToast(data.error || 'Extraction failed', 'error');
        }
    })
    .catch(error => {
        console.error('Extraction error:', error);

        // Stop progress polling on error
        stopProgressPolling();

        document.getElementById('extraction-progress').style.display = 'none';
        document.getElementById('extract-btn').disabled = false;

        // Check if this is an ISBN duplicate error
        if (error.message.startsWith('ISBN_DUPLICATE:')) {
            const duplicateData = JSON.parse(error.message.replace('ISBN_DUPLICATE:', ''));
            showISBNDuplicateModal(duplicateData);
        } else {
            showToast('Extraction failed: ' + error.message, 'error');
        }
    });
}

// Display extraction results
function displayExtractionResults(data) {
    const summary = data.summary;
    const textQuality = data.text_quality_metrics;
    const characterData = data.character_identification;

    let resultsHtml = `
        <div class="extraction-summary">
            <div class="summary-stat">Pages: ${summary.total_pages || 0}</div>
            <div class="summary-stat">Words: ${(summary.total_words || 0).toLocaleString()}</div>
            <div class="summary-stat">Sections: ${data.sections_count || 0}</div>
            ${summary.isbn ? `<div class="summary-stat">ISBN: ${summary.isbn}</div>` : ''}
            ${characterData ? `<div class="summary-stat">Characters: ${characterData.total_characters || 0}</div>` : ''}
        </div>
    `;

    // Add character identification results for novels
    if (characterData && characterData.total_characters > 0) {
        resultsHtml += `
            <div class="character-identification mt-3">
                <h6><i class="fas fa-users"></i> Character Identification Results</h6>
                <div class="character-summary mb-2">
                    <span class="badge bg-primary">${characterData.total_characters} characters identified</span>
                </div>
                <div class="character-list">
                    ${characterData.characters.map(char => `
                        <div class="character-item">
                            <div class="character-header">
                                <div class="character-name">
                                    <i class="fas fa-user"></i> <strong>${char.name}</strong>
                                    <span class="character-type badge bg-secondary ms-2">${char.role || char.character_type || 'unknown'}</span>
                                    ${char.age && char.age !== 'unknown' ? `<span class="character-age badge bg-info ms-1">${char.age}</span>` : ''}
                                </div>
                                <div class="character-confidence">
                                    <small>Confidence: ${Math.round((char.confidence || 0) * 100)}%</small>
                                </div>
                            </div>

                            ${char.physical_description && char.physical_description !== 'Not specified' && char.physical_description !== 'Not specified in fallback analysis' ? `
                                <div class="character-description">
                                    <strong>Description:</strong> <span class="text-muted">${char.physical_description}</span>
                                </div>
                            ` : ''}

                            ${char.personality && char.personality !== 'Not specified' && char.personality !== 'Not specified in fallback analysis' ? `
                                <div class="character-personality">
                                    <strong>Personality:</strong> <span class="text-muted">${char.personality}</span>
                                </div>
                            ` : ''}

                            ${char.relationships && char.relationships.length > 0 ? `
                                <div class="character-relationships">
                                    <strong>Relationships:</strong>
                                    <div class="relationship-tags">
                                        ${char.relationships.map(rel => `<span class="badge bg-light text-dark me-1">${rel}</span>`).join('')}
                                    </div>
                                </div>
                            ` : ''}

                            ${char.background && char.background !== 'Not specified' ? `
                                <div class="character-background">
                                    <strong>Background:</strong> <span class="text-muted">${char.background}</span>
                                </div>
                            ` : ''}

                            ${char.character_arc && char.character_arc !== 'Not analyzed in fallback mode' ? `
                                <div class="character-arc">
                                    <strong>Character Arc:</strong> <span class="text-muted">${char.character_arc}</span>
                                </div>
                            ` : ''}

                            <div class="character-meta">
                                <small class="text-muted">
                                    ${char.importance ? `Importance: ${char.importance}` : ''}
                                    ${char.mentions ? ` | Mentions: ${char.mentions}` : ''}
                                    ${char.enhanced ? ' | Enhanced Profile' : ''}
                                </small>
                            </div>
                        </div>
                    `).join('')}
                </div>
                ${characterData.processing_stages ? `
                    <div class="character-processing-info mt-2">
                        <small class="text-muted">
                            <i class="fas fa-info-circle"></i>
                            Processing: ${characterData.processing_stages.discovery?.status || 'unknown'} →
                            ${characterData.processing_stages.validation?.status || 'unknown'}
                        </small>
                    </div>
                ` : ''}
            </div>
        `;
    } else if (characterData && characterData.total_characters === 0) {
        resultsHtml += `
            <div class="character-identification mt-3">
                <h6><i class="fas fa-users"></i> Character Identification Results</h6>
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i> No characters were identified in this novel.
                    ${characterData.processing_stages?.error ?
                        `<br><small>Error: ${characterData.processing_stages.error}</small>` :
                        '<br><small>This may be due to the content type or text structure.</small>'
                    }
                </div>
            </div>
        `;
    }

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
    // Include session ID if available for token tracking
    const url = currentSessionId ? `/status?session_id=${currentSessionId}` : '/status';

    fetch(url)
    .then(response => response.json())
    .then(data => {
        displaySystemStatus(data);

        // Update token tracking if available
        if (data.token_tracking && (data.token_tracking.total_tokens > 0 || data.token_tracking.total_api_calls > 0)) {
            console.log('📊 Real-time token tracking:', data.token_tracking);
            sessionTokens = data.token_tracking.total_tokens;
            sessionApiCalls = data.token_tracking.total_api_calls;
            sessionCost = data.token_tracking.total_cost;
            updateSessionTracking();
        }
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

    const statusHtml = `
        <div class="mb-2">
            <span class="status-indicator ${chromaStatusClass}"></span>
            <strong>ChromaDB:</strong> ${status.chroma_status}
            <br><small class="text-muted">Collections: ${status.chroma_collections}</small>
        </div>
        <div class="mb-2">
            <span class="status-indicator ${mongoStatusClass}"></span>
            <strong>MongoDB:</strong> ${status.mongodb_status}
            <br><small class="text-muted">Collections: ${status.mongodb_collections}</small>
        </div>
        <div class="mb-2">
            <strong>Sessions:</strong>
            <div class="small text-muted">
                Active: ${status.active_sessions} | Completed: ${status.completed_extractions}
            </div>
        </div>
        <div class="mt-2 pt-2 border-top">
            <strong>Version:</strong>
            <div class="small text-muted">
                ${status.version.version} (${status.version.environment})
            </div>
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
        const isProtected = isProtectedCollection(col.name);

        return `
            <div class="collection-item" data-name="${col.name.toLowerCase()}">
                <div class="p-3">
                    <div class="collection-header">
                        <div class="collection-name" onclick="selectCollection(this.closest('.collection-item'), '${dbKey}', '${col.name}')">
                            <div class="collection-icon ${collectionType}">
                                <i class="fas ${icon}"></i>
                            </div>
                            ${formatCollectionName(col.name)}
                        </div>
                        <div class="collection-actions">
                            <span class="collection-count">${col.document_count || 0}</span>
                            ${dbKey === 'mongodb' && !isProtected ? `
                                <button type="button" class="btn btn-sm btn-outline-danger collection-delete-btn"
                                        onclick="event.stopPropagation(); showCollectionDeletionModal('${col.name}')"
                                        title="Delete Collection">
                                    <i class="fas fa-trash"></i>
                                </button>
                            ` : ''}
                        </div>
                    </div>

                    <div class="collection-meta">
                        ${col.game_type ? `<div><strong>Game:</strong> ${col.game_type}</div>` : ''}
                        ${col.sample_fields ? `<div><strong>Fields:</strong> ${col.sample_fields.slice(0,3).join(', ')}</div>` : ''}
                        <div class="collection-path">${hierarchicalPath}</div>
                        ${isProtected ? '<div class="text-muted"><i class="fas fa-shield-alt"></i> Protected Collection</div>' : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Check if collection is protected from deletion
function isProtectedCollection(collectionName) {
    const protectedCollections = [
        'rpger.system.config',
        'rpger.system.users',
        'rpger.system.audit_log'
    ];
    return protectedCollections.includes(collectionName);
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
    loadCollectionPage(dbType, collectionName, 0, 5);
}

// Toggle deployment mode UI
function toggleDeploymentMode() {
    const containerMode = document.getElementById('mode-containers').checked;
    const containerSettings = document.getElementById('container-db-settings');
    const externalSettings = document.getElementById('external-db-settings');
    
    if (containerMode) {
        containerSettings.style.display = 'block';
        externalSettings.style.display = 'none';
    } else {
        containerSettings.style.display = 'none';
        externalSettings.style.display = 'block';
    }
}

// Test database connections
function testDatabaseConnections() {
    const testButton = document.querySelector('button[onclick="testDatabaseConnections()"]');
    const originalText = testButton.innerHTML;
    
    testButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    testButton.disabled = true;
    
    // Get current deployment mode
    const isContainerMode = document.getElementById('mode-containers').checked;
    
    let testData = {
        deployment_mode: isContainerMode ? 'containers' : 'external'
    };
    
    // Add external database settings if in external mode
    if (!isContainerMode) {
        testData.chromadb_host = document.getElementById('chromadb-host').value;
        testData.chromadb_port = document.getElementById('chromadb-port').value;
        testData.mongodb_host = document.getElementById('mongodb-host').value;
        testData.mongodb_port = document.getElementById('mongodb-port').value;
        testData.mongodb_database = document.getElementById('mongodb-database').value;
        testData.mongodb_username = document.getElementById('mongodb-username').value;
        testData.mongodb_password = document.getElementById('mongodb-password').value;
    }
    
    fetch('/api/test_connections', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(testData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Database connections successful', 'success');
            
            // Show detailed results
            let resultText = 'Connection Test Results:\n';
            if (data.mongodb) {
                resultText += `MongoDB: ${data.mongodb.connected ? '✅ Connected' : '❌ Failed'}\n`;
                if (data.mongodb.message) resultText += `  ${data.mongodb.message}\n`;
            }
            if (data.chromadb) {
                resultText += `ChromaDB: ${data.chromadb.connected ? '✅ Connected' : '❌ Failed'}\n`;
                if (data.chromadb.message) resultText += `  ${data.chromadb.message}\n`;
            }
            
            console.log(resultText);
        } else {
            showToast(`Connection test failed: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Connection test error:', error);
        showToast('Connection test failed: ' + error.message, 'error');
    })
    .finally(() => {
        testButton.innerHTML = originalText;
        testButton.disabled = false;
    });
}

// Load collection page with pagination
function loadCollectionPage(dbType, collectionName, skip = 0, limit = 5) {
    // Show loading state
    const detailsDiv = document.getElementById('collection-details');
    detailsDiv.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading documents...</div>';

    // Properly encode collection name for URL
    const encodedCollectionName = encodeURIComponent(collectionName);
    const endpoint = dbType === 'chromadb' ?
        `/browse_chromadb/${encodedCollectionName}` :
        `/browse_mongodb/${encodedCollectionName}`;

    console.log(`Loading collection page: ${collectionName} (skip: ${skip}, limit: ${limit})`);

    fetch(`${endpoint}?limit=${limit}&skip=${skip}`)
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            displayCollectionDocuments(data, dbType);
        } else {
            console.error('Collection browse failed:', data);
            showToast('Failed to browse collection: ' + (data.error || 'Unknown error'), 'error');

            // Show error in the collection details panel
            detailsDiv.innerHTML = `
                <div class="documents-empty">
                    <i class="fas fa-exclamation-triangle text-warning"></i>
                    <h6>Error Loading Collection</h6>
                    <p class="mb-0">${data.error || 'Unknown error occurred'}</p>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Collection browse error:', error);
        showToast('Collection browse failed: ' + error.message, 'error');

        // Show error in the collection details panel
        detailsDiv.innerHTML = `
            <div class="documents-empty">
                <i class="fas fa-exclamation-triangle text-danger"></i>
                <h6>Connection Error</h6>
                <p class="mb-0">Failed to load collection: ${error.message}</p>
            </div>
        `;
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

        ${data.total_count > data.limit ? `
            <div class="pagination-controls">
                <div class="pagination-info">
                    Page ${Math.floor(data.skip / data.limit) + 1} of ${Math.ceil(data.total_count / data.limit)}
                </div>
                <div class="pagination-buttons">
                    <button class="btn btn-sm btn-outline-light"
                            onclick="loadCollectionPage('${dbType}', '${data.collection}', ${Math.max(0, data.skip - data.limit)}, ${data.limit})"
                            ${data.skip === 0 ? 'disabled' : ''}>
                        <i class="fas fa-chevron-left"></i> Previous
                    </button>
                    <button class="btn btn-sm btn-outline-light"
                            onclick="loadCollectionPage('${dbType}', '${data.collection}', ${data.skip + data.limit}, ${data.limit})"
                            ${data.skip + data.limit >= data.total_count ? 'disabled' : ''}>
                        Next <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
        ` : ''}

        <div class="documents-list" style="max-height: 450px; overflow-y: auto; overflow-x: hidden;">
            ${data.documents.length > 0 ? data.documents.map((doc, index) => `
                <div class="document-card">
                    <div class="document-card-body">
                        <div class="document-title">
                            <i class="fas fa-file-text"></i>
                            ${doc.id || doc._id || `Document ${index + 1}`}
                            <button class="btn btn-sm btn-outline-primary ms-2" onclick="expandDocument(${index}, '${dbType}')">
                                <i class="fas fa-expand-alt"></i> Explore
                            </button>
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

    // Store documents data for expansion
    window.currentDocuments = data.documents;
    window.currentDbType = dbType;
}

// Expand document for detailed exploration
function expandDocument(index, dbType) {
    const doc = window.currentDocuments[index];
    if (!doc) {
        showToast('Document not found', 'error');
        return;
    }

    showDocumentExplorer(doc, dbType);
}

// Show comprehensive document explorer modal
function showDocumentExplorer(doc, dbType) {
    const docId = doc.id || doc._id || 'Unknown';

    const modalHtml = `
        <div class="modal fade" id="documentExplorerModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-search"></i>
                            Document Explorer: ${docId}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-4">
                                <div class="document-fields-panel">
                                    <h6 class="mb-3">
                                        <i class="fas fa-list"></i>
                                        Document Fields
                                    </h6>
                                    <div id="document-fields-tree">
                                        ${generateFieldsTree(doc)}
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-8">
                                <div class="document-content-panel">
                                    <div class="d-flex justify-content-between align-items-center mb-3">
                                        <h6 class="mb-0">
                                            <i class="fas fa-eye"></i>
                                            Field Content
                                        </h6>
                                        <div class="btn-group btn-group-sm">
                                            <button class="btn btn-outline-secondary" onclick="toggleViewMode('formatted')" id="btn-formatted">
                                                <i class="fas fa-align-left"></i> Formatted
                                            </button>
                                            <button class="btn btn-outline-secondary" onclick="toggleViewMode('json')" id="btn-json">
                                                <i class="fas fa-code"></i> JSON
                                            </button>
                                        </div>
                                    </div>
                                    <div id="document-content-viewer">
                                        <div class="content-placeholder">
                                            <i class="fas fa-hand-pointer"></i>
                                            <p>Select a field from the left panel to view its content</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" onclick="copyDocumentJSON()">
                            <i class="fas fa-copy"></i> Copy Full JSON
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if present
    const existingModal = document.getElementById('documentExplorerModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Store document data for viewer
    window.currentExplorerDoc = doc;
    window.currentViewMode = 'formatted';

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('documentExplorerModal'));
    modal.show();
}

// Generate fields tree for document exploration
function generateFieldsTree(doc, prefix = '', level = 0) {
    let html = '';
    const maxLevel = 3; // Prevent infinite recursion

    if (level > maxLevel) {
        return '<div class="text-muted">... (max depth reached)</div>';
    }

    for (const [key, value] of Object.entries(doc)) {
        const fullPath = prefix ? `${prefix}.${key}` : key;
        const fieldType = getFieldType(value);
        const fieldIcon = getFieldIcon(fieldType);
        const hasChildren = fieldType === 'object' || fieldType === 'array';

        html += `
            <div class="field-item" style="margin-left: ${level * 15}px;">
                <div class="field-header" onclick="selectField('${fullPath}', '${fieldType}')"
                     data-path="${fullPath}" data-type="${fieldType}">
                    ${hasChildren ? `<i class="fas fa-chevron-right field-toggle" onclick="event.stopPropagation(); toggleField('${fullPath}')"></i>` : ''}
                    <i class="fas ${fieldIcon} field-icon"></i>
                    <span class="field-name">${key}</span>
                    <span class="field-type">${fieldType}</span>
                    ${fieldType === 'array' ? `<span class="field-count">[${value.length}]</span>` : ''}
                </div>
                <div class="field-children" id="children-${fullPath.replace(/\./g, '-')}" style="display: none;">
                    ${hasChildren && level < maxLevel ? generateFieldsTree(
                        fieldType === 'array' ?
                            Object.fromEntries(value.slice(0, 5).map((item, i) => [i, item])) :
                            value,
                        fullPath,
                        level + 1
                    ) : ''}
                </div>
            </div>
        `;
    }

    return html;
}

// Get field type for display
function getFieldType(value) {
    if (value === null) return 'null';
    if (Array.isArray(value)) return 'array';
    if (typeof value === 'object') return 'object';
    if (typeof value === 'string') return 'string';
    if (typeof value === 'number') return 'number';
    if (typeof value === 'boolean') return 'boolean';
    return 'unknown';
}

// Get icon for field type
function getFieldIcon(type) {
    const icons = {
        'string': 'fa-quote-right',
        'number': 'fa-hashtag',
        'boolean': 'fa-toggle-on',
        'array': 'fa-list',
        'object': 'fa-folder',
        'null': 'fa-ban',
        'unknown': 'fa-question'
    };
    return icons[type] || 'fa-question';
}

// Toggle field expansion
function toggleField(path) {
    const childrenId = `children-${path.replace(/\./g, '-')}`;
    const childrenDiv = document.getElementById(childrenId);
    const toggle = document.querySelector(`[data-path="${path}"] .field-toggle`);

    if (childrenDiv && toggle) {
        if (childrenDiv.style.display === 'none') {
            childrenDiv.style.display = 'block';
            toggle.classList.remove('fa-chevron-right');
            toggle.classList.add('fa-chevron-down');
        } else {
            childrenDiv.style.display = 'none';
            toggle.classList.remove('fa-chevron-down');
            toggle.classList.add('fa-chevron-right');
        }
    }
}

// Select field for viewing
function selectField(path, type) {
    // Remove previous selection
    document.querySelectorAll('.field-header').forEach(header => {
        header.classList.remove('selected');
    });

    // Add selection to current field
    const fieldHeader = document.querySelector(`[data-path="${path}"]`);
    if (fieldHeader) {
        fieldHeader.classList.add('selected');
    }

    // Get field value
    const value = getFieldValue(window.currentExplorerDoc, path);

    // Display field content
    displayFieldContent(path, value, type);
}

// Get field value by path
function getFieldValue(obj, path) {
    return path.split('.').reduce((current, key) => {
        return current && current[key] !== undefined ? current[key] : null;
    }, obj);
}

// Display field content in viewer
function displayFieldContent(path, value, type) {
    const viewer = document.getElementById('document-content-viewer');
    const viewMode = window.currentViewMode || 'formatted';

    let content = '';

    if (viewMode === 'json') {
        content = `
            <div class="json-viewer">
                <div class="field-path-header">
                    <strong>Path:</strong> ${path}
                    <span class="badge bg-secondary ms-2">${type}</span>
                </div>
                <pre><code class="language-json">${JSON.stringify(value, null, 2)}</code></pre>
            </div>
        `;
    } else {
        content = `
            <div class="formatted-viewer">
                <div class="field-path-header">
                    <strong>Path:</strong> ${path}
                    <span class="badge bg-secondary ms-2">${type}</span>
                </div>
                <div class="field-content">
                    ${formatFieldContent(value, type)}
                </div>
            </div>
        `;
    }

    viewer.innerHTML = content;
}

// Format field content for display
function formatFieldContent(value, type) {
    if (value === null || value === undefined) {
        return '<span class="text-muted">null</span>';
    }

    switch (type) {
        case 'string':
            return `<div class="string-content">${escapeHtml(value)}</div>`;
        case 'number':
            return `<div class="number-content">${value}</div>`;
        case 'boolean':
            return `<div class="boolean-content">${value ? 'true' : 'false'}</div>`;
        case 'array':
            return `
                <div class="array-content">
                    <div class="array-info">Array with ${value.length} items:</div>
                    <ol class="array-items">
                        ${value.slice(0, 10).map(item => `
                            <li>${typeof item === 'object' ? JSON.stringify(item) : escapeHtml(String(item))}</li>
                        `).join('')}
                        ${value.length > 10 ? `<li class="text-muted">... and ${value.length - 10} more items</li>` : ''}
                    </ol>
                </div>
            `;
        case 'object':
            const keys = Object.keys(value);
            return `
                <div class="object-content">
                    <div class="object-info">Object with ${keys.length} properties:</div>
                    <ul class="object-properties">
                        ${keys.slice(0, 10).map(key => `
                            <li><strong>${key}:</strong> ${typeof value[key] === 'object' ? '[Object]' : escapeHtml(String(value[key]))}</li>
                        `).join('')}
                        ${keys.length > 10 ? `<li class="text-muted">... and ${keys.length - 10} more properties</li>` : ''}
                    </ul>
                </div>
            `;
        default:
            return `<div class="unknown-content">${escapeHtml(String(value))}</div>`;
    }
}

// Toggle view mode between formatted and JSON
function toggleViewMode(mode) {
    window.currentViewMode = mode;

    // Update button states
    document.getElementById('btn-formatted').classList.toggle('active', mode === 'formatted');
    document.getElementById('btn-json').classList.toggle('active', mode === 'json');

    // Re-display current field if one is selected
    const selectedField = document.querySelector('.field-header.selected');
    if (selectedField) {
        const path = selectedField.getAttribute('data-path');
        const type = selectedField.getAttribute('data-type');
        const value = getFieldValue(window.currentExplorerDoc, path);
        displayFieldContent(path, value, type);
    }
}

// Copy full document JSON to clipboard
function copyDocumentJSON() {
    const json = JSON.stringify(window.currentExplorerDoc, null, 2);
    navigator.clipboard.writeText(json).then(() => {
        showToast('Document JSON copied to clipboard', 'success');
    }).catch(err => {
        console.error('Failed to copy JSON:', err);
        showToast('Failed to copy JSON to clipboard', 'error');
    });
}

// Escape HTML for safe display
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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

// Show ISBN duplicate modal
function showISBNDuplicateModal(duplicateData) {
    const modalHtml = `
        <div class="modal fade" id="isbnDuplicateModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-warning text-dark">
                        <h5 class="modal-title">
                            <i class="fas fa-exclamation-triangle"></i> ${duplicateData.title || 'Novel Already Processed'}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-warning">
                            <strong>Duplicate Detection:</strong> ${duplicateData.details || 'This novel has already been processed.'}
                        </div>

                        <div class="duplicate-info">
                            <h6><i class="fas fa-info-circle"></i> Processing Details:</h6>
                            <p>${duplicateData.message || 'No additional details available.'}</p>
                        </div>

                        <div class="mt-3">
                            <small class="text-muted">
                                <strong>Why this happens:</strong> Each novel can only be extracted once to prevent duplicate patterns
                                in the database. This ensures the quality and uniqueness of the pattern library.
                            </small>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times"></i> Close
                        </button>
                        <button type="button" class="btn btn-primary" onclick="browseMongoDB(); bootstrap.Modal.getInstance(document.getElementById('isbnDuplicateModal')).hide();">
                            <i class="fas fa-database"></i> View Database
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if any
    const existingModal = document.getElementById('isbnDuplicateModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('isbnDuplicateModal'));
    modal.show();

    // Show warning toast as well
    showToast('Novel already processed - ISBN duplicate detected', 'warning');
}

// Utility function to format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ===== ENHANCED PROGRESS TRACKING =====

function initializeProgressTracking() {
    // Initialize collapsible progress steps
    const progressSteps = document.querySelectorAll('.progress-step[data-toggle="collapse"]');
    progressSteps.forEach(step => {
        step.addEventListener('click', function() {
            const target = this.getAttribute('data-target');
            const collapse = document.querySelector(target);
            if (collapse) {
                const isExpanded = this.getAttribute('aria-expanded') === 'true';
                this.setAttribute('aria-expanded', !isExpanded);
                collapse.classList.toggle('show');
            }
        });
    });

    // Initialize token tracking
    updateTokenDisplay();
}

function onContentTypeChange() {
    const contentType = document.getElementById('content-type').value;
    currentContentType = contentType;

    // Show appropriate progress track
    const sourceProgress = document.getElementById('source-progress');
    const novelProgress = document.getElementById('novel-progress');

    if (contentType === 'novel') {
        sourceProgress.style.display = 'none';
        novelProgress.style.display = 'block';
        document.body.classList.add('novel-processing');
    } else {
        sourceProgress.style.display = 'block';
        novelProgress.style.display = 'none';
        document.body.classList.remove('novel-processing');
    }

    // Reset progress
    resetProgress();
}

function updateNovelProgress(stage, status, details = {}) {
    const stepId = `novel-step-${stage}`;
    const step = document.getElementById(stepId);

    if (!step) return;

    // Update step status
    step.classList.remove('active', 'completed', 'error');
    step.classList.add(status);

    // Update step details based on stage
    switch (stage) {
        case 'discovery':
            updateDiscoveryProgress(details);
            break;
        case 'filtering':
            updateFilteringProgress(details);
            break;
        case 'analysis':
            updateAnalysisProgress(details);
            break;
    }
}

function updateDiscoveryProgress(details) {
    if (details.chunks_processed !== undefined) {
        document.getElementById('chunks-processed').textContent = details.chunks_processed;
    }
    if (details.total_chunks !== undefined) {
        document.getElementById('total-chunks').textContent = details.total_chunks;
    }
    if (details.candidates_found !== undefined) {
        document.getElementById('candidates-found').textContent = details.candidates_found;
    }
}

function updateFilteringProgress(details) {
    if (details.candidates_filtered !== undefined) {
        document.getElementById('candidates-filtered').textContent = details.candidates_filtered;
    }
    if (details.filter_ratio !== undefined) {
        document.getElementById('filter-ratio').textContent = Math.round(details.filter_ratio * 100) + '%';
    }
}

function updateAnalysisProgress(details) {
    if (details.current_character !== undefined) {
        document.getElementById('current-character').textContent = details.current_character;
    }
    if (details.characters_confirmed !== undefined) {
        document.getElementById('characters-confirmed').textContent = details.characters_confirmed;
    }
}

function updateTokenDisplay() {
    document.getElementById('session-tokens').textContent = sessionTokens.toLocaleString();
    document.getElementById('session-api-calls').textContent = sessionApiCalls;
}

function addTokenUsage(tokens, apiCalls = 1) {
    sessionTokens += tokens;
    sessionApiCalls += apiCalls;
    updateTokenDisplay();
}

// ===== REAL-TIME PROGRESS POLLING =====

let progressPollingInterval = null;

function startProgressPolling(sessionId) {
    console.log(`Starting progress polling for session: ${sessionId}`);

    // Clear any existing polling
    if (progressPollingInterval) {
        clearInterval(progressPollingInterval);
    }

    // Poll every 1 second
    progressPollingInterval = setInterval(() => {
        fetchProgress(sessionId);
    }, 1000);
}

function stopProgressPolling() {
    if (progressPollingInterval) {
        clearInterval(progressPollingInterval);
        progressPollingInterval = null;
        console.log('Progress polling stopped');
    }
}

function fetchProgress(sessionId) {
    fetch(`/progress/${sessionId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateProgressFromData(data.progress);
            }
        })
        .catch(error => {
            console.error('Progress polling error:', error);
            // Don't stop polling on error, just log it
        });
}

function updateProgressFromData(progressData) {
    // Update novel progress based on received data
    for (const [stage, stageData] of Object.entries(progressData)) {
        const status = stageData.status;
        const details = stageData.details;

        // Update the appropriate progress indicators
        if (stage === 'discovery') {
            updateNovelProgress('discovery', status, details);
        } else if (stage === 'filtering') {
            updateNovelProgress('filtering', status, details);
        } else if (stage === 'analysis') {
            updateNovelProgress('analysis', status, details);
        }

        // Update token usage if available
        if (details.api_calls_made) {
            addTokenUsage(0, details.api_calls_made);
        }
    }
}

function resetProgress() {
    // Reset all progress steps
    const allSteps = document.querySelectorAll('.progress-step');
    allSteps.forEach(step => {
        step.classList.remove('active', 'completed', 'error');
    });

    // Reset token counters for new session
    sessionTokens = 0;
    sessionApiCalls = 0;
    updateTokenDisplay();

    // Reset progress details
    document.getElementById('chunks-processed').textContent = '0';
    document.getElementById('total-chunks').textContent = '0';
    document.getElementById('candidates-found').textContent = '0';
    document.getElementById('candidates-filtered').textContent = '0';
    document.getElementById('filter-ratio').textContent = '0%';
    document.getElementById('current-character').textContent = '-';
    document.getElementById('characters-confirmed').textContent = '0';
}

// ===== AI PROVIDER MANAGEMENT =====

function initializeAIProviderManagement() {
    // Filter AI providers to only show those with API keys
    filterAvailableProviders();

    // Set up provider change handler
    const providerSelect = document.getElementById('ai-provider');
    if (providerSelect) {
        providerSelect.addEventListener('change', onProviderChangeEnhanced);
    }
}

async function filterAvailableProviders() {
    try {
        const response = await fetch('/api/providers/available');
        const data = await response.json();

        if (data.success) {
            const providerSelect = document.getElementById('ai-provider');
            const currentOptions = Array.from(providerSelect.options);

            // Remove providers that don't have API keys
            currentOptions.forEach(option => {
                if (option.value && !data.available_providers.includes(option.value)) {
                    option.remove();
                }
            });

            // Auto-select last used provider if available
            if (savedSettings.lastProvider && data.available_providers.includes(savedSettings.lastProvider)) {
                providerSelect.value = savedSettings.lastProvider;
                onProviderChangeEnhanced();
            }
        }
    } catch (error) {
        console.error('Error filtering providers:', error);
    }
}

function onProviderChangeEnhanced() {
    const provider = document.getElementById('ai-provider').value;
    const modelContainer = document.getElementById('model-selection-container');

    // Save provider preference
    savedSettings.lastProvider = provider;
    saveSettings();

    if (provider === 'openrouter') {
        modelContainer.style.display = 'block';
        loadOpenRouterModelsEnhanced();
    } else {
        modelContainer.style.display = 'none';
    }
}

async function loadOpenRouterModelsEnhanced(forceRefresh = false) {
    const modelSelect = document.getElementById('ai-model');
    const modelDescription = document.getElementById('model-description');

    try {
        // Show loading state
        modelSelect.innerHTML = '<option value="">Loading models...</option>';
        modelDescription.textContent = 'Loading available models...';

        // Fetch models from API
        const response = await fetch(`/api/openrouter/models?refresh=${forceRefresh}&group=true`);
        const data = await response.json();

        if (data.success) {
            openRouterModels = data.models;
            populateModelDropdownEnhanced(data.models, data.recommended);
            modelDescription.textContent = `${data.total_models} models available`;

            // Auto-select last used model if available
            if (savedSettings.lastModel) {
                modelSelect.value = savedSettings.lastModel;
                // Trigger change event to update description
                modelSelect.dispatchEvent(new Event('change'));
            }
            
            // Refresh token tracking if this was a forced refresh (API call made)
            if (forceRefresh) {
                setTimeout(refreshTokenTracking, 500);
            }
        } else {
            throw new Error(data.error || 'Failed to load models');
        }

    } catch (error) {
        console.error('Error loading OpenRouter models:', error);
        modelSelect.innerHTML = '<option value="">Error loading models</option>';
        modelDescription.textContent = 'Failed to load models. Check API key.';
        showToast('Failed to load OpenRouter models: ' + error.message, 'error');
    }
}

function populateModelDropdownEnhanced(models, recommended = []) {
    const modelSelect = document.getElementById('ai-model');
    modelSelect.innerHTML = '';

    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Select a model...';
    modelSelect.appendChild(defaultOption);

    // Add recommended section first
    if (recommended.length > 0) {
        const recommendedGroup = document.createElement('optgroup');
        recommendedGroup.label = '⭐ Recommended for Character Analysis';

        models.filter(model => model.type === 'option' && recommended.includes(model.value))
              .forEach(model => {
                  const option = document.createElement('option');
                  option.value = model.value;
                  option.textContent = model.label;
                  option.setAttribute('data-description', model.description);
                  option.setAttribute('data-provider', model.provider);
                  recommendedGroup.appendChild(option);
              });

        if (recommendedGroup.children.length > 0) {
            modelSelect.appendChild(recommendedGroup);
        }
    }

    // Add all models grouped by provider
    let currentGroup = null;
    models.forEach(model => {
        if (model.type === 'header') {
            currentGroup = document.createElement('optgroup');
            currentGroup.label = model.label;
            modelSelect.appendChild(currentGroup);
        } else if (model.type === 'option' && currentGroup) {
            const option = document.createElement('option');
            option.value = model.value;
            option.textContent = model.label;
            option.setAttribute('data-description', model.description);
            option.setAttribute('data-provider', model.provider);
            currentGroup.appendChild(option);
        }
    });

    // Add change event listener to show model description and save preference
    modelSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        const description = selectedOption.getAttribute('data-description') || 'No description available';
        const provider = selectedOption.getAttribute('data-provider') || '';

        const modelDescription = document.getElementById('model-description');
        if (this.value) {
            modelDescription.textContent = `${provider}: ${description}`;
            // Save model preference
            savedSettings.lastModel = this.value;
            saveSettings();
        } else {
            modelDescription.textContent = 'Select a model for analysis';
        }
    });
}

// ===== SETTINGS MANAGEMENT =====

function loadSavedSettings() {
    try {
        const saved = localStorage.getItem('extractorSettings');
        if (saved) {
            savedSettings = JSON.parse(saved);
        }
    } catch (error) {
        console.error('Error loading saved settings:', error);
        savedSettings = {};
    }
}

function saveSettings() {
    try {
        localStorage.setItem('extractorSettings', JSON.stringify(savedSettings));
    } catch (error) {
        console.error('Error saving settings:', error);
    }
}

// ===== CHUNK MANAGEMENT UI =====

function showChunkManagementModal() {
    // TODO: Implement chunk management modal
    // This would show saved text chunks with options to delete them
    showToast('Chunk management feature coming soon', 'info');
}

// ===== COLLECTION DELETION FUNCTIONALITY =====

let currentDeletionCollection = null;

// Initialize collection deletion modal handlers
document.addEventListener('DOMContentLoaded', function() {
    initializeCollectionDeletion();
});

function initializeCollectionDeletion() {
    // Step navigation handlers
    document.getElementById('proceedToConfirmation')?.addEventListener('click', function() {
        showDeletionStep(2);
    });

    document.getElementById('backToStep1')?.addEventListener('click', function() {
        showDeletionStep(1);
    });

    // Confirmation input handler
    document.getElementById('confirmationInput')?.addEventListener('input', function() {
        const confirmBtn = document.getElementById('confirmDeletion');
        const isValid = this.value === currentDeletionCollection;
        confirmBtn.disabled = !isValid;

        if (isValid) {
            confirmBtn.classList.remove('btn-danger');
            confirmBtn.classList.add('btn-danger');
        }
    });

    // Final deletion handler
    document.getElementById('confirmDeletion')?.addEventListener('click', function() {
        performCollectionDeletion();
    });

    // Modal reset handler
    document.getElementById('deleteCollectionModal')?.addEventListener('hidden.bs.modal', function() {
        resetDeletionModal();
    });
}

function showCollectionDeletionModal(collectionName) {
    currentDeletionCollection = collectionName;

    // Reset modal to step 1
    showDeletionStep(1);

    // Load collection information
    loadCollectionDeletionInfo(collectionName);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('deleteCollectionModal'));
    modal.show();
}

async function loadCollectionDeletionInfo(collectionName) {
    try {
        const response = await fetch(`/api/mongodb/collections/${encodeURIComponent(collectionName)}/deletion-info`);
        const data = await response.json();

        if (data.success) {
            populateCollectionInfo(data);
        } else {
            showToast('Failed to load collection information: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error loading collection deletion info:', error);
        showToast('Failed to load collection information', 'error');
    }
}

function populateCollectionInfo(data) {
    const info = data.collection_info;
    const safety = data.safety_check;

    // Populate basic info
    document.getElementById('delete-collection-name').textContent = info.name;
    document.getElementById('delete-document-count').textContent = info.document_count.toLocaleString();
    document.getElementById('delete-collection-size').textContent = formatFileSize(info.size_bytes);
    document.getElementById('delete-storage-size').textContent = formatFileSize(info.storage_size);
    document.getElementById('delete-index-count').textContent = info.indexes;
    document.getElementById('delete-backup-size').textContent = formatFileSize(data.estimated_backup_size);

    // Set confirmation collection name
    document.getElementById('confirmation-collection-name').textContent = info.name;

    // Show safety warnings
    const warningsContainer = document.getElementById('safety-warnings');
    warningsContainer.innerHTML = '';

    if (!safety.safe_to_delete) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger';
        alert.innerHTML = `
            <h6><i class="fas fa-ban me-2"></i>Deletion Blocked</h6>
            <p class="mb-0">${safety.reason}</p>
        `;
        warningsContainer.appendChild(alert);

        // Disable proceed button
        document.getElementById('proceedToConfirmation').disabled = true;
    } else if (safety.warning) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-warning';
        alert.innerHTML = `
            <h6><i class="fas fa-exclamation-triangle me-2"></i>Warning</h6>
            <p class="mb-0">${safety.reason}</p>
        `;
        warningsContainer.appendChild(alert);
    }
}

function showDeletionStep(step) {
    // Hide all steps
    for (let i = 1; i <= 4; i++) {
        const stepElement = document.getElementById(`deletion-step-${i}`);
        if (stepElement) {
            stepElement.style.display = 'none';
        }
    }

    // Show target step
    const targetStep = document.getElementById(`deletion-step-${step}`);
    if (targetStep) {
        targetStep.style.display = 'block';
    }

    // Reset confirmation input when going to step 2
    if (step === 2) {
        document.getElementById('confirmationInput').value = '';
        document.getElementById('confirmDeletion').disabled = true;
    }
}

async function performCollectionDeletion() {
    showDeletionStep(3);

    const createBackup = document.getElementById('createBackupCheck').checked;
    const confirmationName = document.getElementById('confirmationInput').value;
    const adminPassword = document.getElementById('adminPasswordInput').value;

    try {
        // Update progress
        updateDeletionProgress(25, 'Validating request...');

        const response = await fetch(`/api/mongodb/collections/${encodeURIComponent(currentDeletionCollection)}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                confirmation_name: confirmationName,
                create_backup: createBackup,
                admin_password: adminPassword
            })
        });

        updateDeletionProgress(50, 'Processing deletion...');

        const data = await response.json();

        updateDeletionProgress(75, 'Finalizing...');

        // Small delay for UX
        await new Promise(resolve => setTimeout(resolve, 500));

        updateDeletionProgress(100, 'Complete');

        // Show results
        showDeletionResults(data);

    } catch (error) {
        console.error('Deletion error:', error);
        showDeletionResults({
            success: false,
            error: 'Network error: ' + error.message
        });
    }
}

function updateDeletionProgress(percentage, status) {
    const progressBar = document.querySelector('#deletion-progress .progress-bar');
    const statusText = document.getElementById('deletion-status');

    if (progressBar) {
        progressBar.style.width = percentage + '%';
    }

    if (statusText) {
        statusText.textContent = status;
    }
}

function showDeletionResults(data) {
    showDeletionStep(4);

    const resultContainer = document.getElementById('deletion-result');

    if (data.success) {
        resultContainer.innerHTML = `
            <div class="alert alert-success">
                <h6><i class="fas fa-check-circle me-2"></i>Collection Deleted Successfully</h6>
                <p class="mb-2">${data.message}</p>
                <ul class="mb-0">
                    <li>Documents deleted: ${data.documents_deleted.toLocaleString()}</li>
                    ${data.backup_created ? `<li>Backup created: ${data.backup_path}</li>` : '<li>No backup created</li>'}
                </ul>
            </div>
        `;

        // Refresh database browser if open
        if (document.getElementById('database-browser-content').innerHTML.trim()) {
            browseMongoDB();
        }

        showToast('Collection deleted successfully', 'success');
    } else {
        resultContainer.innerHTML = `
            <div class="alert alert-danger">
                <h6><i class="fas fa-times-circle me-2"></i>Deletion Failed</h6>
                <p class="mb-0">${data.error}</p>
            </div>
        `;

        showToast('Collection deletion failed: ' + data.error, 'error');
    }
}

function resetDeletionModal() {
    currentDeletionCollection = null;

    // Reset all form inputs
    document.getElementById('confirmationInput').value = '';
    document.getElementById('adminPasswordInput').value = '';
    document.getElementById('createBackupCheck').checked = true;

    // Reset progress
    updateDeletionProgress(0, 'Preparing deletion...');

    // Clear warnings
    document.getElementById('safety-warnings').innerHTML = '';

    // Re-enable proceed button
    document.getElementById('proceedToConfirmation').disabled = false;

    // Reset to step 1
    showDeletionStep(1);
}
