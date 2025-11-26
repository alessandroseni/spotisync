#!/bin/bash
echo "🎵🤖 Music Discovery Agent"
echo "==========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create a .env file with:"
    echo "  SPOTIPY_CLIENT_ID=your_id"
    echo "  SPOTIPY_CLIENT_SECRET=your_secret"
    echo "  SPOTIPY_REDIRECT_URI=your_redirect_uri"
    echo "  OPENAI_API_KEY=your_key"
    exit 1
fi

# Check if pipenv is installed
if ! command -v pipenv &> /dev/null; then
    echo "❌ pipenv not found!"
    echo "Please install pipenv: pip install pipenv"
    exit 1
fi

# Run the service
pipenv run python -m music_discovery.main

