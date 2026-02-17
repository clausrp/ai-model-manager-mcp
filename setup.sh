#!/bin/bash

# AI Model Manager MCP Server - Setup Script

set -e

echo "=================================="
echo "AI Model Manager MCP Server Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.10 or higher is required. Found: $python_version"
    exit 1
fi
echo "✓ Python $python_version found"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your API keys!"
else
    echo ".env file already exists. Skipping..."
fi
echo ""

# Create data directory
echo "Creating data directory..."
mkdir -p data
echo "✓ Data directory created"
echo ""

# Check if Ollama is installed
echo "Checking for Ollama..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama is installed"
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✓ Ollama is running"
        
        # List installed models
        echo ""
        echo "Installed Ollama models:"
        ollama list
    else
        echo "⚠️  Ollama is installed but not running"
        echo "   Start it with: ollama serve"
    fi
else
    echo "⚠️  Ollama is not installed"
    echo "   Install from: https://ollama.ai"
    echo "   Then run: ollama pull llama3.2"
fi
echo ""

echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Install Ollama models (optional):"
echo "   ollama pull llama3.2"
echo "   ollama pull mistral"
echo "3. Run the server:"
echo "   python -m src.server"
echo ""
echo "For Claude Desktop integration, see README.md"
echo ""

# Made with Bob
