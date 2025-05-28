# Test Requirements for Extractor Project (Priority Order)

## **Priority 1: Critical Core Functionality**

### **1.1 PDF Processing Tests (`test_pdf_processor.py`)**
**Why Critical**: Core functionality that everything depends on
- **PDF Reading & Validation**
  - Test PDF file opening with valid/invalid files
  - Test corrupted PDF handling
  - Test large file handling (memory management)
  - Test different PDF versions and formats

- **Content Extraction**
  - Test text extraction from different PDF types (scanned vs text-based)
  - Test metadata extraction (title, author, subject, keywords)
  - Test page-by-page extraction
  - Test special character handling (Unicode, symbols)

- **ISBN Extraction** (already partially implemented)
  - Test ISBN-10 validation and extraction
  - Test ISBN-13 validation and extraction
  - Test ISBN extraction from metadata vs content
  - Test malformed ISBN handling

### **1.2 AI Game Detection Tests (`test_ai_game_detector.py`)**
**Why Critical**: Primary AI functionality for content classification
- **Game Type Detection**
  - Test detection accuracy for each supported game system
  - Test confidence scoring for different content types
  - Test fallback mechanisms when AI fails
  - Test novel vs source material detection

- **AI Provider Integration**
  - Test OpenRouter API integration
  - Test Anthropic API integration
  - Test mock provider fallback
  - Test API error handling and retries

### **1.3 MongoDB Manager Tests (`test_mongodb_manager.py`)**
**Why Critical**: Data persistence layer
- **Connection Management**
  - Test connection establishment with various configurations
  - Test authentication with username/password
  - Test connection failure handling

- **Collection Operations**
  - Test collection creation with hierarchical naming
  - Test document insertion and validation
  - Test query operations and filtering

## **Priority 2: Essential Integration & Workflow**

### **2.1 End-to-End Extraction Tests (`test_e2e_extraction.py`)**
**Why Essential**: Validates complete user workflow
- **Complete Workflow**
  - Test full PDF → Analysis → Extraction → Database workflow
  - Test different content types (source material vs novels)
  - Test various game systems and editions
  - Test confidence testing integration

- **Error Recovery**
  - Test graceful failure handling at each stage
  - Test partial extraction recovery
  - Test session state persistence

### **2.2 Flask Application Tests (`test_web_ui.py`)**
**Why Essential**: User interface functionality
- **File Upload**
  - Test PDF file upload validation
  - Test file size limits (200MB)
  - Test file type restrictions
  - Test upload timeout handling

- **API Endpoints**
  - Test `/analyze` endpoint with different AI providers
  - Test `/extract` endpoint with various configurations
  - Test `/progress` endpoint for real-time updates
  - Test error handling and status codes

### **2.3 Text Quality Enhancement Tests (`test_text_quality_enhancer.py`)**
**Why Essential**: Content quality improvement
- **OCR Artifact Cleanup**
  - Test common OCR errors (rn→m, l→I, etc.)
  - Test spacing normalization
  - Test line break optimization

- **Spell Checking**
  - Test RPG-specific dictionary preservation
  - Test aggressive vs normal cleanup modes
  - Test correction accuracy and false positives

## **Priority 3: Advanced Features & Optimization**

### **3.1 Novel Element Extraction Tests (`test_novel_element_extractor.py`)**
**Why Important**: Advanced AI feature for novel processing
- **Character Identification**
  - Test character discovery in novel text
  - Test character filtering by mention frequency
  - Test batch processing (10 characters at once)
  - Test memory optimization for large novels

- **Building Blocks Extraction**
  - Test keyword extraction across categories
  - Test depersonalization of extracted elements
  - Test pattern recognition for reusable content

### **3.2 AI Categorization Tests (`test_ai_categorizer.py`)**
**Why Important**: Content classification enhancement
- **Content Classification**
  - Test category assignment accuracy
  - Test multi-category content handling
  - Test confidence scoring for categorization

- **Content Analysis**
  - Test theme identification
  - Test mechanics detection
  - Test complexity level assessment

### **3.3 Performance Tests (`test_performance.py`)**
**Why Important**: System scalability and efficiency
- **Large File Handling**
  - Test extraction of 100+ page PDFs
  - Test memory usage during processing
  - Test processing time benchmarks
  - Test concurrent file processing

- **Database Performance**
  - Test large collection operations
  - Test query performance with thousands of documents
  - Test index effectiveness

## **Priority 4: Configuration & Environment**

### **4.1 Environment Configuration Tests (`test_config.py`)**
**Why Useful**: System configuration validation
- **Environment Variables**
  - Test `.env` file loading
  - Test environment variable validation
  - Test default value fallbacks

- **API Key Management**
  - Test API key validation for each provider
  - Test secure storage and retrieval
  - Test missing key fallback behavior

### **4.2 AI Provider Integration Tests (`test_ai_providers.py`)**
**Why Useful**: Multi-provider support validation
- **Provider Switching**
  - Test switching between AI providers mid-session
  - Test fallback to mock when APIs fail
  - Test model selection persistence

- **Model Performance**
  - Test accuracy across different models
  - Test response time comparisons
  - Test cost optimization

### **4.3 Game Configuration Tests (`test_game_configs.py`)**
**Why Useful**: Game system support validation
- **Game System Support**
  - Test configuration loading for each game system
  - Test keyword detection accuracy
  - Test book catalog validation
  - Test categorization rule application

## **Priority 5: Security & Validation**

### **5.1 Input Validation Tests (`test_validation.py`)**
**Why Important for Production**: Security and data integrity
- **File Security**
  - Test malicious PDF handling
  - Test file path traversal prevention
  - Test filename sanitization
  - Test upload size validation

- **Data Sanitization**
  - Test SQL injection prevention (MongoDB)
  - Test XSS prevention in web UI
  - Test input validation for all endpoints
  - Test session security

### **5.2 Error Handling Tests (`test_error_handling.py`)**
**Why Important for Production**: System reliability
- **Graceful Degradation**
  - Test behavior when AI APIs are unavailable
  - Test database connection failures
  - Test partial extraction scenarios
  - Test timeout handling

## **Priority 6: Utility & Helper Components**

### **6.1 Multi-Collection Manager Tests (`test_multi_collection_manager.py`)**
**Why Nice-to-Have**: Enhanced data management
- **Collection Management**
  - Test automatic collection creation
  - Test collection name generation
  - Test metadata storage and retrieval
  - Test duplicate prevention

### **6.2 Building Blocks Manager Tests (`test_building_blocks.py`)**
**Why Nice-to-Have**: Advanced pattern management
- **Pattern Management**
  - Test pattern storage and retrieval
  - Test category-based organization
  - Test pattern matching algorithms
  - Test procedural generation support

### **6.3 OpenRouter Models Tests (`test_openrouter_models.py`)**
**Why Nice-to-Have**: Model management utilities
- **Model Management**
  - Test model list fetching and caching
  - Test model recommendation logic
  - Test dropdown option generation
  - Test model metadata handling

### **6.4 Memory Management Tests (`test_memory.py`)**
**Why Nice-to-Have**: Performance optimization
- **Memory Optimization**
  - Test memory usage during novel processing
  - Test garbage collection effectiveness
  - Test memory leaks in long-running processes
  - Test chunked processing efficiency

### **6.5 Real-time Progress Tests (`test_progress_tracking.py`)**
**Why Nice-to-Have**: User experience enhancement
- **Progress Updates**
  - Test progress callback functionality
  - Test session-based progress tracking
  - Test real-time UI updates
  - Test progress persistence across requests

## **Test Infrastructure Requirements**

### **Immediate Setup Needs (Priority 1)**
1. **Test Framework**: Set up pytest with proper configuration
2. **Mock Data**: Create basic mock PDFs for D&D, Pathfinder
3. **CI/CD Integration**: Basic GitHub Actions for test automation
4. **Coverage Reports**: Set up coverage.py for code coverage tracking

### **Medium-term Setup (Priority 2-3)**
1. **Test Fixtures**: Comprehensive test data and configurations
2. **Performance Benchmarks**: Establish baseline performance metrics
3. **Integration Test Environment**: Test MongoDB and AI provider mocks
4. **Mock Services**: Complete AI provider mocking system

### **Long-term Setup (Priority 4-6)**
1. **Load Testing**: Stress testing infrastructure
2. **Security Testing**: Penetration testing tools
3. **Documentation**: Test documentation and examples
4. **Monitoring**: Test result tracking and analysis

## **Implementation Strategy**

1. **Start with Priority 1**: Focus on core PDF processing and AI detection
2. **Build incrementally**: Add one test suite at a time
3. **Maintain coverage**: Aim for >80% coverage on Priority 1-2 tests
4. **Automate early**: Set up CI/CD as soon as Priority 1 tests exist
5. **Document thoroughly**: Include test examples and best practices

## **Success Metrics**

- **Priority 1-2**: >90% test coverage, all tests passing
- **Priority 3-4**: >80% test coverage, comprehensive edge case handling
- **Priority 5-6**: >70% test coverage, security and performance validated
- **Overall**: Reliable CI/CD pipeline, automated testing on all commits
