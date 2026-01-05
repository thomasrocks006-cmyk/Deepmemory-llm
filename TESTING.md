# Testing Guide

## Overview

The DeepMemory LLM project includes a comprehensive test suite covering:
- **Unit Tests**: Individual component functionality
- **Integration Tests**: Multi-component workflows
- **Agent Tests**: AI agent behavior and outputs
- **API Tests**: Endpoint validation

## Quick Start

```bash
# Install test dependencies
cd backend
pip install -r requirements-test.txt

# Run all tests
bash run_tests.sh

# Or use pytest directly
pytest tests/ -v
```

## Test Categories

### Unit Tests

Test individual modules in isolation:

```bash
pytest tests/ -m unit -v
```

Examples:
- Importer parsing logic
- Coreference resolution
- Database models
- Utility functions

### Integration Tests

Test complete workflows:

```bash
pytest tests/ -m integration -v
```

Examples:
- Full ingestion pipeline
- Multi-agent collaboration
- API endpoint flows
- Database operations

### Agent Tests

Test AI agent behavior:

```bash
pytest tests/ -m agent -v
```

Examples:
- Librarian retrieval accuracy
- Strategist response quality
- Profiler psychological analysis
- Multi-vector search

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures and mocks
├── fixtures.py          # Sample test data
├── test_agents.py       # Agent behavior tests
├── test_ingestion.py    # Ingestion pipeline tests
├── test_learning_loop.py # Learning loop tests
├── test_api.py          # API endpoint tests
└── .env.test            # Test environment variables
```

## Writing Tests

### Basic Test

```python
import pytest

@pytest.mark.unit
def test_example():
    assert 1 + 1 == 2
```

### Async Test

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Using Fixtures

```python
def test_with_db(db_session):
    # db_session is provided by conftest.py
    conv = Conversation(id="test", title="Test")
    db_session.add(conv)
    db_session.commit()
    
    assert db_session.query(Conversation).count() == 1
```

### Mock External Services

```python
async def test_with_mocks(mock_gemini_client, mock_pinecone_client):
    # Mocks prevent real API calls during tests
    agent = LibrarianAgent(
        gemini_client=mock_gemini_client,
        vector_db=mock_pinecone_client
    )
    
    result = await agent.process({"query": "test"})
    assert result is not None
```

## Coverage

View test coverage:

```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=html

# Open in browser
open htmlcov/index.html
```

Target coverage: **70%+**

## Continuous Integration

Tests run automatically on:
- Pull requests
- Main branch commits
- Release tags

## Common Issues

### Import Errors

```bash
# Ensure backend is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
```

### Database Errors

Tests use SQLite in-memory database. If you see connection errors:

```bash
# Check .env.test configuration
cat .env.test
```

### Mock Failures

If mocks aren't working:

```python
# Verify fixture is imported
def test_example(mock_gemini_client):  # ✅ Correct
    pass

def test_example():
    mock = MockGeminiClient()  # ❌ Won't use fixture
```

## Best Practices

1. **Isolation**: Tests should not depend on each other
2. **Determinism**: Tests should produce same results every time
3. **Speed**: Use mocks for external services
4. **Clarity**: Test names should describe what they test
5. **Coverage**: Aim for high coverage of critical paths

## Example Test Session

```bash
$ pytest tests/ -v

tests/test_agents.py::TestLibrarianAgent::test_initialization PASSED
tests/test_agents.py::TestLibrarianAgent::test_process_query PASSED
tests/test_agents.py::TestStrategistAgent::test_response_generation PASSED
tests/test_ingestion.py::TestChatGPTImporter::test_parse_valid_export PASSED
tests/test_ingestion.py::TestManualImporter::test_parse_simple_format PASSED
tests/test_learning_loop.py::TestLearningLoop::test_post_turn_extraction PASSED
tests/test_api.py::TestHealthEndpoint::test_health_check PASSED

======================== 7 passed in 2.34s =========================
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
