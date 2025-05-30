#!/bin/bash
echo "🎵 Spotisync - Syncing your liked songs..."
echo "============================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and configure your credentials"
    exit 1
fi

# Check if pipenv is installed
if ! command -v pipenv &> /dev/null; then
    echo "❌ pipenv not found!"
    echo "Please install pipenv: pip install pipenv"
    exit 1
fi

# Run the sync using pipenv
pipenv run python spotisync.py 