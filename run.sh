#!/bin/bash

# YouTube Shorts Generator - Startup Script

set -e

echo "🎬 Starting YouTube Shorts Generator..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Ensure DeepSeek API key is present
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "❌ DEEPSEEK_API_KEY is not set. Export it or add it to your .env file."
    exit 1
fi

# Create necessary directories
mkdir -p temp output

# Start backend
echo "🚀 Starting backend server..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python backend/main.py

