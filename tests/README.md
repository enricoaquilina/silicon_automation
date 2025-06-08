# Testing Guide for Silicon Automation MCP MongoDB Server

This directory contains comprehensive tests for the MCP MongoDB server and related components.

## 🧪 Test Structure

```
tests/
├── README.md                 # This file
├── conftest.py              # pytest configuration and fixtures
├── requirements.txt         # Test dependencies
├── test_mcp_server.py       # Main MCP server tests
├── test_instagram_analysis.py # Instagram analysis module tests
└── test_carousel_extraction.py # Existing carousel tests
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Or use the test runner
python run_tests.py --install
```

### 2. Set Up MongoDB (for integration tests)

```bash
# Using Docker (recommended)
docker run -d --name test-mongodb -p 27017:27017 mongo:7.0

# Or install MongoDB locally
# macOS: brew install mongodb-community
# Ubuntu: sudo apt-get install mongodb
```

### 3. Run Tests

```bash
# Quick unit tests (no external dependencies)
python run_tests.py --unit

# All tests with coverage
python run_tests.py --coverage

# Integration tests (requires MongoDB)
python run_tests.py --integration

# Run everything
python run_tests.py --all
```

## 📋 Test Categories

### Unit Tests
- **Purpose**: Test individual functions and classes in isolation
- **Dependencies**: None (uses mocks)
- **Speed**: Fast (< 1 second each)
- **Run with**: `pytest -m "not slow and not integration"`

### Integration Tests
- **Purpose**: Test component interactions with real services
- **Dependencies**: MongoDB, external APIs (mocked in CI)
- **Speed**: Medium (1-10 seconds each)
- **Run with**: `pytest -m integration`

### Performance Tests
- **Purpose**: Test performance under load and stress
- **Dependencies**: MongoDB, large datasets
- **Speed**: Slow (10+ seconds each)
- **Run with**: `pytest -m "slow or performance"`

## 🎯 Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Performance/stress tests
- `@pytest.mark.browser` - Browser automation tests
- `@pytest.mark.security` - Security-related tests

## 🔧 Configuration

### Environment Variables

```bash
# MongoDB connection
export MONGODB_URI="mongodb://localhost:27017/"
export MONGODB_DATABASE="test_silicon_automation"

# API keys for integration tests (optional)
export REPLICATE_API_TOKEN="your_test_token"
export OPENAI_API_KEY="your_test_key"
```

### pytest.ini

The root `pytest.ini` file configures:
- Test discovery patterns
- Coverage reporting
- Warning filters
- Default markers

## 📊 Coverage Reports

### Generate Coverage Report

```bash
# Terminal report
pytest --cov=mcp_mongodb_server --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov=mcp_mongodb_server --cov-report=html:htmlcov
open htmlcov/index.html

# XML report (for CI)
pytest --cov=mcp_mongodb_server --cov-report=xml
```

### Coverage Goals

- **Overall**: 80%+ line coverage
- **Critical modules**: 90%+ line coverage
- **New code**: 95%+ line coverage

## 🐍 Test Runner Script

The `run_tests.py` script provides convenient commands:

```bash
# Install dependencies
python run_tests.py --install

# Check MongoDB connection
python run_tests.py --check-db

# Run specific test types
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --performance

# Code quality checks
python run_tests.py --lint

# Full coverage report
python run_tests.py --coverage

# Everything
python run_tests.py --all
```

## 🔄 CI/CD Integration

### GitHub Actions

The `.github/workflows/ci.yml` file runs:

1. **Test Matrix**: Python 3.9-3.12 × MongoDB 5.0-7.0
2. **Unit Tests**: Fast tests with mocked dependencies
3. **Integration Tests**: Real MongoDB connection
4. **Code Quality**: Linting, formatting, type checking
5. **Security**: Bandit security scanning
6. **Coverage**: Upload to Codecov

### Local Pre-commit Checks

```bash
# Run the same checks as CI
python run_tests.py --lint
python run_tests.py --unit
python run_tests.py --coverage
```

## 🧩 Writing New Tests

### Test File Structure

```python
#!/usr/bin/env python3
"""
Test module for [component name]
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_mongodb_server"))

class TestYourComponent:
    """Test cases for YourComponent"""
    
    @pytest.fixture
    def mock_dependency(self):
        """Mock external dependencies"""
        return Mock()
    
    @pytest.mark.unit
    def test_basic_functionality(self, mock_dependency):
        """Test basic functionality"""
        # Arrange
        component = YourComponent(mock_dependency)
        
        # Act
        result = component.do_something()
        
        # Assert
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality"""
        # Use AsyncMock for async dependencies
        pass
    
    @pytest.mark.integration
    def test_real_integration(self):
        """Test with real external services"""
        # Only runs when integration tests are enabled
        pass
    
    @pytest.mark.slow
    def test_performance(self):
        """Test performance characteristics"""
        # Only runs when slow tests are enabled
        pass
```

### Best Practices

1. **Use descriptive test names**: `test_generate_missing_images_success`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Mock external dependencies**: Database, APIs, file system
4. **Test edge cases**: Empty inputs, errors, timeouts
5. **Use fixtures**: Reusable test data and mocks
6. **Mark appropriately**: Unit, integration, slow tests

## 🐛 Debugging Tests

### Running Individual Tests

```bash
# Single test
pytest tests/test_mcp_server.py::TestImageGenerationIntegration::test_initialization -v

# Single test class
pytest tests/test_mcp_server.py::TestImageGenerationIntegration -v

# With debugging
pytest tests/test_mcp_server.py -v -s --tb=long
```

### Common Issues

1. **Import errors**: Check PYTHONPATH setup
2. **MongoDB connection**: Ensure MongoDB is running
3. **Missing dependencies**: Run `python run_tests.py --install`
4. **Async test failures**: Use `@pytest.mark.asyncio`

## 📈 Metrics and Reporting

### Test Results

- **GitHub Actions**: Automatic test reports on PRs
- **Coverage**: HTML reports in `htmlcov/`
- **Timing**: Pytest timing plugin shows slow tests
- **Security**: Bandit reports in CI artifacts

### Performance Benchmarks

Performance tests track:
- Database query times
- Image generation latency
- Memory usage patterns
- Throughput under load

## 🔒 Security Testing

Security tests verify:
- Input validation
- SQL injection prevention
- API key handling
- Data sanitization

Run security checks:

```bash
# Security linting
bandit -r mcp_mongodb_server/

# Dependency vulnerability check
safety check

# Through test runner
python run_tests.py --lint
```

## 📚 Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py](https://coverage.readthedocs.io/)
- [GitHub Actions](https://docs.github.com/en/actions)

## 🤝 Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure 90%+ coverage for new code
3. Add appropriate markers
4. Update this README if needed
5. Run full test suite before committing

```bash
# Pre-commit checklist
python run_tests.py --lint
python run_tests.py --unit
python run_tests.py --coverage
```