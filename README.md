# Spotisync 🎵

A Python tool to sync your Spotify liked songs to a public playlist, with the most recent tracks at the top.

## Setup

### 1. Spotify API Setup
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app with these settings:
   - Redirect URI: `http://127.0.0.1:8080`
3. Note down your **Client ID** and **Client Secret**

### 2. Installation
```bash
# Install pipenv if you don't have it
pip install pipenv

# Install dependencies
pipenv install

# Copy environment template
cp .env.example .env
```

### 3. Configuration
Edit `.env` file with your credentials:
```
SPOTIPY_CLIENT_ID=your_client_id_here
SPOTIPY_CLIENT_SECRET=your_client_secret_here
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8080/callback
PLAYLIST_ID=your_playlist_id_here
```

## Usage

```bash
# Run with pipenv
pipenv run python spotisync.py

# Or activate shell and run directly
pipenv shell
python spotisync.py

# Or use the helper script
./run.sh
```

The script will:
1. Create the playlist if it doesn't exist
2. Clear all existing tracks from the playlist
3. Add all your liked songs with newest tracks at the top

## Features

- ✅ Syncs all liked songs to a public playlist
- ✅ Most recent likes appear at the top
- ✅ Automatically clears and refreshes the playlist
- ✅ One-command execution
- ✅ Clean pipenv dependency management 