#!/usr/bin/env fish
# Installation script for ZKP Evaluation System

echo "🚀 ZKP Evaluation System - Installation"
echo "========================================"
echo ""

# Check Python version
if not command -v python3 &> /dev/null
    echo "❌ Python 3 is required but not found"
    exit 1
end

set PYTHON_VERSION (python3 --version | cut -d' ' -f2)
echo "✓ Found Python $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate.fish

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Install package in development mode
echo ""
echo "Installing zkp-evaluation package..."
pip install -e .

# Create necessary directories
echo ""
echo "Creating directory structure..."
mkdir -p data/raw
mkdir -p data/processed
mkdir -p results/charts
mkdir -p results/reports

echo ""
echo "✅ Installation complete!"
echo ""
echo "To activate the environment, run:"
echo "  source venv/bin/activate.fish"
echo ""
echo "To run a quick demo:"
echo "  python scripts/run_demo.py"
echo ""
echo "To run full benchmark:"
echo "  python scripts/run_full_benchmark.py"
