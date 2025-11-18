# Integration Tests for 1_Publication

This directory contains comprehensive integration tests for the publication fetching and filtering system.

## 📋 Test Coverage

The test suite covers:

1. **OpenAlex API Integration** (`TestOpenAlexIntegration`)

   - Institution search
   - Paper fetching with pagination
   - CSV export functionality
   - Summary statistics

2. **AI Ethics Filtering** (`TestFilterAIEthicsIntegration`)

   - CSV reading/writing
   - API key pool management
   - Rate limiting
   - Parallel processing
   - Live checkpoint writing
   - Resume functionality

3. **Gemini API Integration** (`TestGeminiCallIntegration`)

   - JSON response parsing
   - Markdown code block stripping
   - Error handling

4. **End-to-End Workflow** (`TestEndToEndWorkflow`)

   - Complete pipeline: fetch → save → filter → classify
   - Integration of all components

5. **Error Handling** (`TestErrorHandling`)
   - API timeouts
   - Empty data
   - Malformed CSV
   - Retry mechanisms

## 🚀 Running Tests

### Install Dependencies

```bash
# Using pip
pip install -r requirements-test.txt

# Using uv (recommended)
uv pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Classes

```bash
# Run only OpenAlex tests
pytest test_integration.py::TestOpenAlexIntegration -v

# Run only filtering tests
pytest test_integration.py::TestFilterAIEthicsIntegration -v

# Run end-to-end tests
pytest test_integration.py::TestEndToEndWorkflow -v
```

### Run Specific Test Methods

```bash
# Run a specific test
pytest test_integration.py::TestOpenAlexIntegration::test_search_institution_success -v
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term

# View HTML coverage report
# Open htmlcov/index.html in browser
```

### Run in Parallel

```bash
# Run tests in parallel (faster)
pytest -n auto
```

## 📊 Test Markers

Tests can be marked for selective execution:

```bash
# Run only integration tests
pytest -m integration

# Run only API tests
pytest -m api

# Skip slow tests
pytest -m "not slow"
```

## 🔧 Configuration

Test configuration is in `pytest.ini`:

- Test discovery patterns
- Output formatting
- Logging settings
- Coverage options
- Timeout settings

## 📝 Writing New Tests

### Test Structure

```python
class TestYourFeature:
    """Tests for your feature"""

    @pytest.fixture
    def sample_data(self):
        """Fixture providing test data"""
        return {"key": "value"}

    def test_something(self, sample_data):
        """Test description"""
        result = your_function(sample_data)
        assert result == expected_value
```

### Using Mocks

```python
from unittest.mock import patch, Mock

@patch('module.function')
def test_with_mock(self, mock_function):
    mock_function.return_value = "mocked_result"
    result = call_that_uses_function()
    assert result == "expected"
```

### Testing Files

```python
def test_file_operations(tmp_path):
    """Use tmp_path fixture for file testing"""
    test_file = tmp_path / "test.csv"
    # ... perform file operations
    assert test_file.exists()
```

## 🐛 Debugging Tests

### Verbose Output

```bash
pytest -vv
```

### Show Print Statements

```bash
pytest -s
```

### Stop on First Failure

```bash
pytest -x
```

### Run Last Failed Tests

```bash
pytest --lf
```

### Enter Debugger on Failure

```bash
pytest --pdb
```

## 📈 Continuous Integration

To run in CI/CD pipelines:

```bash
# Run with XML output for CI
pytest --junitxml=test-results.xml

# Run with coverage for CI
pytest --cov=. --cov-report=xml
```

## ⚠️ Important Notes

1. **API Keys**: Tests mock external API calls. Real API keys are not needed.
2. **Temporary Files**: Tests use `tmp_path` fixture - files are auto-cleaned.
3. **Parallel Safety**: Tests are isolated and can run in parallel.
4. **Mocking**: External dependencies are mocked to avoid rate limits.

## 🔍 Test Scenarios Covered

### Happy Path

- ✅ Successful API calls
- ✅ Valid data processing
- ✅ Complete workflow execution

### Edge Cases

- ✅ Empty results
- ✅ Missing data fields
- ✅ Malformed responses

### Error Conditions

- ✅ Network timeouts
- ✅ API rate limits
- ✅ Invalid data formats
- ✅ File system errors

### Performance

- ✅ Rate limiting
- ✅ Parallel processing
- ✅ Large dataset handling

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Unittest.mock Guide](https://docs.python.org/3/library/unittest.mock.html)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
