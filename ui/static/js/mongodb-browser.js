/**
 * MongoDB Browser Component
 * Provides a hierarchical tree view and document browser for MongoDB collections
 */

class MongoDBBrowser {
    constructor() {
        this.currentCollection = null;
        this.currentPage = 1;
        this.documentsPerPage = 20;
        this.treeNodeState = {}; // Keeps track of expanded/collapsed nodes
        this.searchTerm = '';
    }
    
    /**
     * Initialize the browser
     */
    async initialize() {
        try {
            // Create modal if it doesn't exist
            if (!document.getElementById('mongoDBBrowserModal')) {
                this.createBrowserModal();
            }
            
            // Load and render collections
            await this.loadCollections();
            
            // Show the modal
            const modalElement = document.getElementById('mongoDBBrowserModal');
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        } catch (error) {
            console.error('Error initializing MongoDB browser:', error);
            showToast('Failed to initialize MongoDB browser: ' + error.message, 'error');
        }
    }
    
    /**
     * Create the browser modal HTML
     */
    createBrowserModal() {
        const modalHtml = `
            <div class="modal fade" id="mongoDBBrowserModal" tabindex="-1" aria-labelledby="mongoDBBrowserModalLabel">
                <div class="modal-dialog modal-xl modal-dialog-scrollable">
                    <div class="modal-content">
                        <div class="modal-header bg-light">
                            <h5 class="modal-title" id="mongoDBBrowserModalLabel">
                                <i class="fas fa-leaf me-2"></i> MongoDB Collections Browser
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body p-0">
                            <div class="row g-0" style="min-height: 600px;">
                                <!-- Collections Tree View -->
                                <div class="col-md-4 border-end">
                                    <div class="collections-sidebar">
                                        <div class="collections-header">
                                            <h6 class="mb-0">Collections</h6>
                                            <span class="collections-count" id="mongodb-collections-count">0</span>
                                        </div>
                                        
                                        <!-- Search Box -->
                                        <div class="collection-search">
                                            <input type="text" class="form-control" id="mongodb-collection-search"
                                                placeholder="Search collections..." onkeyup="mongoDBBrowser.filterCollections()">
                                            <i class="fas fa-search search-icon"></i>
                                        </div>
                                        
                                        <!-- Tree View -->
                                        <div id="mongodb-collections-tree" class="collections-tree">
                                            <div class="loading">
                                                <i class="fas fa-spinner fa-spin"></i> Loading collections...
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Document Viewer -->
                                <div class="col-md-8">
                                    <div class="document-viewer">
                                        <!-- Collection Info Panel -->
                                        <div id="mongodb-collection-info" class="collection-info-panel">
                                            <div class="empty-state">
                                                <div class="empty-state-icon">
                                                    <i class="fas fa-database"></i>
                                                </div>
                                                <h5>Select a Collection</h5>
                                                <p>Choose a collection from the tree to view its documents</p>
                                            </div>
                                        </div>
                                        
                                        <!-- Documents List -->
                                        <div id="mongodb-documents-list" class="documents-list" style="display: none;">
                                            <!-- Document search -->
                                            <div class="document-search-container">
                                                <div class="input-group">
                                                    <input type="text" class="form-control" id="document-search-input" 
                                                        placeholder="Search documents...">
                                                    <button class="btn btn-outline-secondary" type="button" id="document-search-button"
                                                        onclick="mongoDBBrowser.searchDocuments()">
                                                        <i class="fas fa-search"></i>
                                                    </button>
                                                </div>
                                            </div>
                                            
                                            <!-- Documents container -->
                                            <div id="documents-container" class="documents-container">
                                                <div class="loading">
                                                    <i class="fas fa-spinner fa-spin"></i> Loading documents...
                                                </div>
                                            </div>
                                            
                                            <!-- Pagination -->
                                            <div id="documents-pagination" class="documents-pagination">
                                                <!-- Pagination will be inserted here -->
                                            </div>
                                        </div>
                                        
                                        <!-- Document Detail View -->
                                        <div id="mongodb-document-detail" class="document-detail" style="display: none;">
                                            <div class="document-detail-header">
                                                <button class="btn btn-sm btn-outline-secondary" onclick="mongoDBBrowser.closeDocumentDetail()">
                                                    <i class="fas fa-arrow-left"></i> Back to List
                                                </button>
                                                <h6 id="document-detail-title">Document Detail</h6>
                                            </div>
                                            <div id="document-detail-content" class="document-detail-content">
                                                <!-- Document detail will be inserted here -->
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
        
        // Inject modal into body
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        document.body.appendChild(modalContainer.firstElementChild);
    }
    
    /**
     * Load MongoDB collections
     */
    async loadCollections() {
        try {
            const response = await fetch('/api/mongodb/collections');
            const data = await response.json();
            
            if (data.success) {
                this.renderCollectionsTree(data.collections);
                document.getElementById('mongodb-collections-count').innerText = data.total_collections;
            } else {
                throw new Error(data.error || 'Failed to load collections');
            }
        } catch (error) {
            console.error('Error loading collections:', error);
            document.getElementById('mongodb-collections-tree').innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>${error.message || 'Failed to load collections'}</p>
                </div>
            `;
        }
    }
    
    /**
     * Render collections as a hierarchical tree
     */
    renderCollectionsTree(collections) {
        // Group collections by hierarchy
        const hierarchyTree = this.buildCollectionHierarchy(collections);
        
        // Render the tree
        const treeHtml = this.generateTreeHtml(hierarchyTree);
        document.getElementById('mongodb-collections-tree').innerHTML = treeHtml;
        
        // Set up expand/collapse handlers
        this.setupTreeEventHandlers();
    }
    
    /**
     * Build a hierarchical tree from flat collection list
     */
    buildCollectionHierarchy(collections) {
        const tree = { name: 'root', children: {}, isRoot: true };
        
        collections.forEach(collection => {
            // Split the collection name on dots
            const parts = collection.name.split('.');
            
            // Start at the root
            let currentNode = tree;
            
            // Build path through the tree
            for (let i = 0; i < parts.length; i++) {
                const part = parts[i];
                const isLeaf = i === parts.length - 1;
                
                // Create node if it doesn't exist
                if (!currentNode.children[part]) {
                    currentNode.children[part] = {
                        name: part,
                        path: parts.slice(0, i + 1).join('.'),
                        displayName: this.formatPathPart(part),
                        children: {},
                        isLeaf: isLeaf
                    };
                }
                
                // Move to this node
                currentNode = currentNode.children[part];
                
                // If this is the leaf node, store the collection data
                if (isLeaf) {
                    currentNode.collection = collection;
                }
            }
        });
        
        return tree;
    }
    
    /**
     * Generate HTML for the tree
     */
    generateTreeHtml(node) {
        if (node.isRoot) {
            // Root node - just process children
            let html = '<ul class="tree-root">';
            
            // Sort children by name
            const sortedChildren = Object.values(node.children).sort((a, b) => 
                a.name.localeCompare(b.name)
            );
            
            for (const child of sortedChildren) {
                html += this.generateTreeNodeHtml(child);
            }
            
            html += '</ul>';
            return html;
        }
        
        return '';
    }
    
    /**
     * Generate HTML for a single tree node
     */
    generateTreeNodeHtml(node) {
        const hasChildren = Object.keys(node.children).length > 0;
        const nodeId = `tree-node-${node.path.replace(/\./g, '-')}`;
        const isExpanded = this.treeNodeState[nodeId] === true;
        const expandClass = isExpanded ? 'expanded' : 'collapsed';
        
        let html = `<li class="tree-node ${expandClass}" id="${nodeId}" data-path="${node.path}">`;
        
        // Node content
        html += '<div class="tree-node-content">';
        
        // Expand/collapse icon or leaf icon
        if (hasChildren) {
            html += `<span class="tree-node-toggle" onclick="mongoDBBrowser.toggleTreeNode('${nodeId}')">
                <i class="fas ${isExpanded ? 'fa-caret-down' : 'fa-caret-right'}"></i>
            </span>`;
        } else {
            html += '<span class="tree-node-icon">';
            
            // Choose icon based on collection type
            if (node.collection) {
                const type = this.getCollectionType(node.path);
                html += `<i class="fas ${this.getCollectionIcon(type)}"></i>`;
            } else {
                html += '<i class="fas fa-folder"></i>';
            }
            
            html += '</span>';
        }
        
        // Node label
        if (node.isLeaf) {
            html += `<span class="tree-node-label" onclick="mongoDBBrowser.selectCollection('${node.path}')">${node.displayName}</span>`;
            if (node.collection) {
                html += `<span class="tree-node-count">${node.collection.document_count}</span>`;
            }
        } else {
            html += `<span class="tree-node-label" onclick="mongoDBBrowser.toggleTreeNode('${nodeId}')">${node.displayName}</span>`;
        }
        
        html += '</div>';
        
        // Children
        if (hasChildren) {
            html += `<ul class="tree-node-children" ${isExpanded ? '' : 'style="display: none;"'}>`;
            
            // Sort children by name
            const sortedChildren = Object.values(node.children).sort((a, b) => 
                a.name.localeCompare(b.name)
            );
            
            for (const child of sortedChildren) {
                html += this.generateTreeNodeHtml(child);
            }
            
            html += '</ul>';
        }
        
        html += '</li>';
        return html;
    }
    
    /**
     * Set up event handlers for the tree
     */
    setupTreeEventHandlers() {
        // Nothing to do here, we're using inline onclick handlers
    }
    
    /**
     * Toggle tree node expansion
     */
    toggleTreeNode(nodeId) {
        const node = document.getElementById(nodeId);
        if (!node) return;
        
        const childrenContainer = node.querySelector('.tree-node-children');
        if (!childrenContainer) return;
        
        const isExpanded = node.classList.contains('expanded');
        const toggleIcon = node.querySelector('.tree-node-toggle i');
        
        if (isExpanded) {
            // Collapse
            childrenContainer.style.display = 'none';
            node.classList.remove('expanded');
            node.classList.add('collapsed');
            if (toggleIcon) toggleIcon.classList.replace('fa-caret-down', 'fa-caret-right');
            this.treeNodeState[nodeId] = false;
        } else {
            // Expand
            childrenContainer.style.display = '';
            node.classList.remove('collapsed');
            node.classList.add('expanded');
            if (toggleIcon) toggleIcon.classList.replace('fa-caret-right', 'fa-caret-down');
            this.treeNodeState[nodeId] = true;
        }
    }
    
    /**
     * Format a path part for display
     */
    formatPathPart(part) {
        return part.replace(/_/g, ' ')
                  .split(' ')
                  .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                  .join(' ');
    }
    
    /**
     * Filter collections based on search term
     */
    filterCollections() {
        const searchTerm = document.getElementById('mongodb-collection-search').value.toLowerCase();
        this.searchTerm = searchTerm;
        
        // Get all leaf nodes
        const leafNodes = document.querySelectorAll('.tree-node[data-path]');
        
        leafNodes.forEach(node => {
            const path = node.dataset.path.toLowerCase();
            const isVisible = path.includes(searchTerm);
            
            // Show/hide based on search
            if (isVisible) {
                // Show this node
                node.style.display = '';
                
                // Show all parent nodes
                let parent = node.parentElement;
                while (parent && !parent.classList.contains('tree-root')) {
                    if (parent.classList.contains('tree-node-children')) {
                        parent.style.display = '';
                        
                        // Expand parent node
                        const parentNode = parent.parentElement;
                        if (parentNode && parentNode.classList.contains('tree-node')) {
                            parentNode.classList.remove('collapsed');
                            parentNode.classList.add('expanded');
                            
                            const toggleIcon = parentNode.querySelector('.tree-node-toggle i');
                            if (toggleIcon) {
                                toggleIcon.classList.replace('fa-caret-right', 'fa-caret-down');
                            }
                            
                            this.treeNodeState[parentNode.id] = true;
                        }
                    }
                    parent = parent.parentElement;
                }
            } else {
                // Hide if we're searching and it doesn't match
                if (searchTerm) {
                    node.style.display = 'none';
                } else {
                    node.style.display = '';
                }
            }
        });
    }
    
    /**
     * Get collection type (for icon selection)
     */
    getCollectionType(name) {
        if (name.includes('monsters') || name.includes('bestiary')) {
            return 'monsters';
        } else if (name.includes('spells') || name.includes('magic')) {
            return 'spells';
        } else if (name.includes('items') || name.includes('equipment')) {
            return 'items';
        } else if (name.includes('characters')) {
            return 'characters';
        } else if (name.includes('npcs')) {
            return 'npcs';
        } else if (name.includes('source_material')) {
            return 'source_material';
        } else {
            return 'default';
        }
    }
    
    /**
     * Get icon for collection type
     */
    getCollectionIcon(type) {
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
    
    /**
     * Select a collection to view
     */
    async selectCollection(collectionPath) {
        try {
            this.currentCollection = collectionPath;
            this.currentPage = 1;
            
            // Reset search
            document.getElementById('document-search-input').value = '';
            
            // Show loading state
            this.showCollectionLoading();
            
            // Get collection info
            const infoResponse = await fetch(`/api/mongodb/collections/${collectionPath}`);
            const infoData = await infoResponse.json();
            
            if (!infoData.success) {
                throw new Error(infoData.error || 'Failed to get collection info');
            }
            
            // Get documents for first page
            const docsResponse = await fetch(
                `/api/mongodb/collections/${collectionPath}/documents?page=1&limit=${this.documentsPerPage}`
            );
            const docsData = await docsResponse.json();
            
            if (!docsData.success) {
                throw new Error(docsData.error || 'Failed to get documents');
            }
            
            // Display collection info and documents
            this.displayCollectionInfo(infoData.collection_info);
            this.displayDocuments(docsData.documents, docsData.pagination);
            
        } catch (error) {
            console.error('Error selecting collection:', error);
            document.getElementById('mongodb-collection-info').innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>${error.message || 'Failed to load collection'}</p>
                </div>
            `;
            
            // Hide documents list
            document.getElementById('mongodb-documents-list').style.display = 'none';
        }
    }
    
    /**
     * Show loading state for collection
     */
    showCollectionLoading() {
        // Show loading in collection info panel
        document.getElementById('mongodb-collection-info').innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i> Loading collection info...
            </div>
        `;
        
        // Show loading in documents list
        document.getElementById('mongodb-documents-list').style.display = 'none';
        document.getElementById('mongodb-document-detail').style.display = 'none';
    }
    
    /**
     * Display collection information
     */
    displayCollectionInfo(info) {
        if (!info) {
            document.getElementById('mongodb-collection-info').innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>No information available for this collection</p>
                </div>
            `;
            return;
        }
        
        // Format collection name for display
        const displayName = info.name.split('.').map(part => 
            part.replace(/_/g, ' ')
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ')
        ).join(' › ');
        
        // Create info panel HTML
        const infoHtml = `
            <div class="collection-info-header">
                <h5 class="collection-name">${displayName}</h5>
                <div class="collection-actions">
                    <div class="dropdown">
                        <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" 
                                data-bs-toggle="dropdown" aria-expanded="false">
                            <i class="fas fa-download"></i> Export
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><a class="dropdown-item" href="/api/mongodb/collections/${info.name}/export?format=json" target="_blank">
                                <i class="fas fa-file-code"></i> Export as JSON
                            </a></li>
                            <li><a class="dropdown-item" href="/api/mongodb/collections/${info.name}/export?format=csv" target="_blank">
                                <i class="fas fa-file-csv"></i> Export as CSV
                            </a></li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="collection-stats">
                <div class="stat-item">
                    <div class="stat-label">Documents</div>
                    <div class="stat-value">${info.document_count}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Size</div>
                    <div class="stat-value">${this.formatBytes(info.size || 0)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Avg Doc Size</div>
                    <div class="stat-value">${this.formatBytes(info.avg_document_size || 0)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Indexes</div>
                    <div class="stat-value">${info.indexes || 0}</div>
                </div>
            </div>
        `;
        
        // Update info panel
        document.getElementById('mongodb-collection-info').innerHTML = infoHtml;
        
        // Show documents list
        document.getElementById('mongodb-documents-list').style.display = 'block';
    }
    
    /**
     * Display documents list
     */
    displayDocuments(documents, pagination) {
        const documentsContainer = document.getElementById('documents-container');
        const paginationContainer = document.getElementById('documents-pagination');
        
        if (!documents || documents.length === 0) {
            documentsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">
                        <i class="fas fa-file-alt"></i>
                    </div>
                    <h5>No Documents Found</h5>
                    <p>This collection is empty or no documents match your search</p>
                </div>
            `;
            paginationContainer.innerHTML = '';
            return;
        }
        
        // Generate documents HTML
        let documentsHtml = '';
        
        documents.forEach(doc => {
            const id = doc._id;
            const title = this.getDocumentTitle(doc);
            const preview = this.getDocumentPreview(doc);
            
            documentsHtml += `
                <div class="document-card" onclick="mongoDBBrowser.viewDocument('${this.currentCollection}', '${id}')">
                    <div class="document-title">${title}</div>
                    <div class="document-preview">${preview}</div>
                    <div class="document-meta">
                        <span class="document-id">${id}</span>
                        ${doc.import_date ? 
                            `<span class="document-date">${new Date(doc.import_date).toLocaleDateString()}</span>` : ''}
                    </div>
                </div>
            `;
        });
        
        // Update documents container
        documentsContainer.innerHTML = documentsHtml;
        
        // Generate pagination HTML
        this.renderPagination(pagination, paginationContainer);
    }
    
    /**
     * Render pagination controls
     */
    renderPagination(pagination, container) {
        if (!pagination || pagination.total_pages <= 1) {
            container.innerHTML = '';
            return;
        }
        
        const current = pagination.current_page;
        const total = pagination.total_pages;
        
        let paginationHtml = `
            <div class="pagination-info">
                Showing page ${current} of ${total} 
                (${pagination.total_documents} documents total)
            </div>
            <div class="pagination-controls">
        `;
        
        // Previous button
        paginationHtml += `
            <button class="btn btn-sm btn-outline-secondary ${!pagination.has_prev ? 'disabled' : ''}"
                ${pagination.has_prev ? `onclick="mongoDBBrowser.goToPage(${current - 1})"` : 'disabled'}>
                <i class="fas fa-chevron-left"></i>
            </button>
        `;
        
        // Page number buttons
        const maxButtons = 5; // Max number of page buttons to show
        const startPage = Math.max(1, current - Math.floor(maxButtons / 2));
        const endPage = Math.min(total, startPage + maxButtons - 1);
        
        if (startPage > 1) {
            paginationHtml += `
                <button class="btn btn-sm btn-outline-secondary" onclick="mongoDBBrowser.goToPage(1)">1</button>
                ${startPage > 2 ? '<span class="pagination-ellipsis">...</span>' : ''}
            `;
        }
        
        for (let page = startPage; page <= endPage; page++) {
            paginationHtml += `
                <button class="btn btn-sm ${page === current ? 'btn-primary' : 'btn-outline-secondary'}"
                    onclick="mongoDBBrowser.goToPage(${page})">
                    ${page}
                </button>
            `;
        }
        
        if (endPage < total) {
            paginationHtml += `
                ${endPage < total - 1 ? '<span class="pagination-ellipsis">...</span>' : ''}
                <button class="btn btn-sm btn-outline-secondary" onclick="mongoDBBrowser.goToPage(${total})">${total}</button>
            `;
        }
        
        // Next button
        paginationHtml += `
            <button class="btn btn-sm btn-outline-secondary ${!pagination.has_next ? 'disabled' : ''}"
                ${pagination.has_next ? `onclick="mongoDBBrowser.goToPage(${current + 1})"` : 'disabled'}>
                <i class="fas fa-chevron-right"></i>
            </button>
        `;
        
        paginationHtml += '</div>';
        
        // Update pagination container
        container.innerHTML = paginationHtml;
    }
    
    /**
     * Go to a specific page
     */
    async goToPage(page) {
        if (!this.currentCollection) return;
        
        try {
            // Show loading
            document.getElementById('documents-container').innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i> Loading documents...
                </div>
            `;
            
            // Get search term if any
            const searchTerm = document.getElementById('document-search-input').value;
            
            // Get documents for the page
            const response = await fetch(
                `/api/mongodb/collections/${this.currentCollection}/documents?` +
                `page=${page}&limit=${this.documentsPerPage}` +
                (searchTerm ? `&search=${encodeURIComponent(searchTerm)}` : '')
            );
            
            const data = await response.json();
            
            if (data.success) {
                this.currentPage = page;
                this.displayDocuments(data.documents, data.pagination);
            } else {
                throw new Error(data.error || 'Failed to get documents');
            }
            
        } catch (error) {
            console.error('Error changing page:', error);
            document.getElementById('documents-container').innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>${error.message || 'Failed to load documents'}</p>
                </div>
            `;
        }
    }
    
    /**
     * Search documents
     */
    async searchDocuments() {
        if (!this.currentCollection) return;
        
        const searchTerm = document.getElementById('document-search-input').value;
        
        try {
            // Show loading
            document.getElementById('documents-container').innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i> Searching documents...
                </div>
            `;
            
            // Get documents matching search
            const response = await fetch(
                `/api/mongodb/collections/${this.currentCollection}/documents?` +
                `page=1&limit=${this.documentsPerPage}` +
                `&search=${encodeURIComponent(searchTerm)}`
            );
            
            const data = await response.json();
            
            if (data.success) {
                this.currentPage = 1;
                this.displayDocuments(data.documents, data.pagination);
            } else {
                throw new Error(data.error || 'Failed to search documents');
            }
            
        } catch (error) {
            console.error('Error searching documents:', error);
            document.getElementById('documents-container').innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>${error.message || 'Failed to search documents'}</p>
                </div>
            `;
        }
    }
    
    /**
     * View a specific document
     */
    async viewDocument(collectionName, documentId) {
        try {
            // Show loading
            document.getElementById('mongodb-document-detail').style.display = 'block';
            document.getElementById('mongodb-documents-list').style.display = 'none';
            
            document.getElementById('document-detail-content').innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i> Loading document...
                </div>
            `;
            
            // Get document details
            const response = await fetch(`/api/mongodb/collections/${collectionName}/documents/${documentId}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayDocumentDetail(data.document);
            } else {
                throw new Error(data.error || 'Failed to get document');
            }
            
        } catch (error) {
            console.error('Error viewing document:', error);
            document.getElementById('document-detail-content').innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>${error.message || 'Failed to load document'}</p>
                </div>
            `;
        }
    }
    
    /**
     * Display document detail
     */
    displayDocumentDetail(document) {
        if (!document) {
            document.getElementById('document-detail-content').innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Document not found</p>
                </div>
            `;
            return;
        }
        
        // Set title
        document.getElementById('document-detail-title').textContent = this.getDocumentTitle(document);
        
        // Format document as pretty JSON
        const formattedJson = JSON.stringify(document, null, 2);
        
        // Create HTML
        const detailHtml = `
            <div class="document-properties">
                <div class="property-row">
                    <div class="property-label">ID:</div>
                    <div class="property-value">${document._id}</div>
                </div>
                ${document.title ? `
                    <div class="property-row">
                        <div class="property-label">Title:</div>
                        <div class="property-value">${document.title}</div>
                    </div>
                ` : ''}
                ${document.import_date ? `
                    <div class="property-row">
                        <div class="property-label">Import Date:</div>
                        <div class="property-value">${new Date(document.import_date).toLocaleString()}</div>
                    </div>
                ` : ''}
            </div>
            
            <div class="json-viewer">
                <div class="json-viewer-header">
                    <h6>Document JSON</h6>
                </div>
                <pre class="json-content">${this.escapeHtml(formattedJson)}</pre>
            </div>
        `;
        
        // Update detail content
        document.getElementById('document-detail-content').innerHTML = detailHtml;
    }
    
    /**
     * Close document detail view
     */
    closeDocumentDetail() {
        document.getElementById('mongodb-document-detail').style.display = 'none';
        document.getElementById('mongodb-documents-list').style.display = 'block';
    }
    
    /**
     * Helper Functions
     */
    
    // Get document title for display
    getDocumentTitle(doc) {
        if (doc.title) {
            return this.escapeHtml(doc.title);
        } else if (doc.name) {
            return this.escapeHtml(doc.name);
        } else if (doc.game_metadata && doc.game_metadata.book_full_name) {
            return this.escapeHtml(doc.game_metadata.book_full_name);
        } else {
            return `Document ${doc._id}`;
        }
    }
    
    // Get document preview text
    getDocumentPreview(doc) {
        let previewText = '';
        
        if (doc.content) {
            previewText = doc.content;
        } else if (doc.description) {
            previewText = doc.description;
        } else if (doc.text) {
            previewText = doc.text;
        } else if (doc.sections && doc.sections.length > 0) {
            // Extract preview from sections
            for (const section of doc.sections.slice(0, 2)) {
                if (typeof section === 'string') {
                    previewText += section + ' ';
                } else if (section.content) {
                    previewText += section.content + ' ';
                }
            }
        } else {
            // Try to find any text-like field
            for (const key in doc) {
                if (typeof doc[key] === 'string' && doc[key].length > 20 && 
                    !['_id', '_source_collection'].includes(key)) {
                    previewText = doc[key];
                    break;
                }
            }
        }
        
        // Truncate and escape
        if (previewText) {
            return this.escapeHtml(previewText.substring(0, 150) + (previewText.length > 150 ? '...' : ''));
        } else {
            return '<em>No preview available</em>';
        }
    }
    
    // Format bytes to human-readable size
    formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
    }
    
    // Escape HTML
    escapeHtml(text) {
        if (typeof text !== 'string') return '';
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
}

// Create global instance
const mongoDBBrowser = new MongoDBBrowser();

// Function to open MongoDB browser
function openMongoDBBrowser() {
    mongoDBBrowser.initialize();
}