#!/bin/bash

set -e

echo "🎬 Starting YouTube Shorts Generator (Docker)"

# Warn if API key missing
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "⚠️  DEEPSEEK_API_KEY is not set. Cloud LLM features will fail."
fi

# Start backend
echo "🚀 Starting backend server..."
cd /app
export PYTHONPATH=/app
exec python3 backend/main.py

