# Extractor Project Tests

This directory contains comprehensive tests for the Extractor project, organized by priority and functionality.

## Test Structure

### Priority 1: Critical Core Functionality ⭐⭐⭐
These tests validate the most essential components that everything else depends on:

- **`test_pdf_processor.py`** - PDF processing, text extraction, ISBN validation
- **`test_ai_game_detector.py`** - AI-powered game detection and classification
- **`test_mongodb_manager.py`** - Database operations and data management
- **`test_isbn_extraction.py`** - ISBN extraction and validation (existing)

### Priority 2: Essential Integration & Workflow ⭐⭐
These tests validate component interactions and complete user workflows:

- **`test_e2e_extraction.py`** - End-to-end extraction workflows and error recovery
- **`test_web_ui.py`** - Flask web application, file upload, API endpoints
- **`test_text_quality_enhancer.py`** - Text quality enhancement and OCR cleanup

### Test Infrastructure
- **`test_infrastructure.py`** - Validates test setup and fixtures
- **`conftest.py`** - Shared fixtures and mock classes
- **`pytest.ini`** - Pytest configuration and settings
- **`run_priority1_tests.py`** - Test runner for Priority 1 tests

## Running Tests

### Quick Start
```bash
# Run all Priority 1 tests (Critical Core Functionality)
python tests/run_priority1_tests.py

# Run all Priority 2 tests (Essential Integration & Workflow)
python tests/run_priority2_tests.py

# Run with verbose output and coverage
python tests/run_priority1_tests.py --verbose --coverage
python tests/run_priority2_tests.py --verbose --coverage

# Run fast tests only (skip slow ones)
python tests/run_priority1_tests.py --fast
python tests/run_priority2_tests.py --fast

# Run specific Priority 2 categories
python tests/run_priority2_tests.py --integration-only  # End-to-end tests
python tests/run_priority2_tests.py --web-only         # Flask web UI tests
python tests/run_priority2_tests.py --text-only        # Text enhancement tests
```

### Using pytest directly
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_pdf_processor.py

# Run with coverage
pytest --cov=Modules --cov-report=html

# Run only unit tests
pytest -m unit

# Run excluding slow tests
pytest -m "not slow"
```

### Test Infrastructure Validation
```bash
# Verify test setup is working
python tests/test_infrastructure.py
```

## Test Categories

Tests are marked with the following categories:

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests for component interactions
- `@pytest.mark.e2e` - End-to-end workflow tests
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.ai` - Tests requiring AI provider access
- `@pytest.mark.mongodb` - Tests requiring MongoDB connection
- `@pytest.mark.pdf` - Tests working with PDF files
- `@pytest.mark.mock` - Tests using only mock data
- `@pytest.mark.web` - Tests for Flask web application
- `@pytest.mark.text_enhancement` - Tests for text quality enhancement
- `@pytest.mark.workflow` - Tests for complete user workflows
- `@pytest.mark.priority1` - Priority 1 (Critical Core Functionality) tests
- `@pytest.mark.priority2` - Priority 2 (Essential Integration & Workflow) tests

## Test Coverage Goals

- **Priority 1 Tests**: >90% coverage
- **Priority 2 Tests**: >80% coverage
- **Overall Project**: >75% coverage

## Mock Data and Fixtures

### Available Fixtures

#### Configuration
- `mock_ai_config` - AI provider configuration for testing
- `mock_mongodb_config` - MongoDB connection configuration
- `temp_dir` - Temporary directory for test files

#### Sample Content
- `sample_dnd_content` - D&D 5th Edition sample text
- `sample_pathfinder_content` - Pathfinder 2nd Edition sample text
- `sample_isbn_texts` - Various ISBN format examples
- `sample_extraction_result` - Complete extraction result example

#### Mock Objects
- `MockPDFDocument` - Mock PyMuPDF document
- `MockPDFPage` - Mock PyMuPDF page
- `mock_pdf_with_isbn` - PDF with ISBN in metadata
- `mock_pdf_without_isbn` - PDF without ISBN

#### AI Responses
- `mock_ai_response_dnd` - D&D detection response
- `mock_ai_response_pathfinder` - Pathfinder detection response
- `mock_ai_response_unknown` - Unknown content response

#### Factories
- `create_test_pdf` - Factory for creating test PDF files

## Test Implementation Guidelines

### Writing New Tests

1. **Use descriptive test names** that explain what is being tested
2. **Follow the AAA pattern**: Arrange, Act, Assert
3. **Use appropriate fixtures** from `conftest.py`
4. **Mock external dependencies** (AI APIs, databases, file system)
5. **Test both success and failure cases**
6. **Add appropriate markers** for test categorization

### Example Test Structure
```python
class TestFeatureName:
    """Test description for the feature"""

    def test_successful_operation(self, fixture_name):
        """Test successful operation with valid input"""
        # Arrange
        processor = SomeProcessor(config)

        # Act
        result = processor.process(valid_input)

        # Assert
        assert result is not None
        assert result.success == True

    def test_error_handling(self, fixture_name):
        """Test error handling with invalid input"""
        processor = SomeProcessor(config)

        with pytest.raises(ExpectedException):
            processor.process(invalid_input)
```

### Mocking Best Practices

1. **Mock at the boundary** - Mock external services, not internal logic
2. **Use patch decorators** for cleaner test code
3. **Verify mock calls** when testing interactions
4. **Reset mocks** between tests (handled automatically by pytest)

## Continuous Integration

Tests are designed to run in CI/CD environments:

- **No external dependencies** required for core tests
- **Mock all AI providers** and database connections
- **Fast execution** for quick feedback
- **Comprehensive coverage** reporting

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the project root
   cd /path/to/extractor
   python -m pytest tests/
   ```

2. **Missing Dependencies**
   ```bash
   pip install pytest pytest-cov
   ```

3. **Path Issues**
   ```bash
   # Add project root to Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

4. **Mock Failures**
   - Check that mocks are properly configured
   - Verify patch targets are correct
   - Ensure fixtures are available

### Debug Mode
```bash
# Run with debug output
pytest -v -s tests/test_infrastructure.py

# Run single test with debugging
pytest -v -s tests/test_pdf_processor.py::TestPDFValidation::test_file_not_found
```

## Future Test Priorities

### Priority 2: Essential Integration & Workflow
- End-to-end extraction tests
- Flask application tests
- Text quality enhancement tests

### Priority 3: Advanced Features & Optimization
- Novel element extraction tests
- Performance and load tests
- AI categorization tests

### Priority 4: Configuration & Environment
- Environment configuration tests
- AI provider integration tests
- Game configuration tests

### Priority 5: Security & Validation
- Input validation tests
- Error handling tests
- Security tests

### Priority 6: Utility & Helper Components
- Multi-collection manager tests
- Building blocks manager tests
- Memory management tests

## Contributing

When adding new tests:

1. **Follow the priority system** - implement higher priority tests first
2. **Update this README** if adding new test categories or fixtures
3. **Ensure tests pass** before committing
4. **Add appropriate documentation** for complex test scenarios
5. **Consider test performance** - mark slow tests appropriately
