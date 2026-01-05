#!/bin/bash
# Run all tests with coverage

set -e

echo "🧪 Running DeepMemory LLM Test Suite"
echo "===================================="

# Activate virtual environment if needed
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -r requirements-test.txt

# Run unit tests
echo ""
echo "🔬 Running unit tests..."
pytest tests/ -m unit -v

# Run integration tests
echo ""
echo "🔗 Running integration tests..."
pytest tests/ -m integration -v

# Run agent tests
echo ""
echo "🤖 Running agent tests..."
pytest tests/ -m agent -v

# Run all tests with coverage
echo ""
echo "📊 Running full test suite with coverage..."
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

echo ""
echo "✅ Test suite complete!"
echo "📈 Coverage report generated in htmlcov/index.html"
