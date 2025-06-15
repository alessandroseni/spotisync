# Spotisync 🎵

A Python tool that automatically syncs your Spotify liked songs to a public playlist, keeping your most recent tracks at the top. Perfect for sharing your music taste or creating a backup of your likes!

# Lot Radio Artist Finder 🎵📻🤖

An AI-powered tool that matches your Spotify listening habits with The Lot Radio NYC's schedule and discovers new music recommendations.

## What It Does

### Spotisync
- 📥 **Fetch all your liked songs** from your Spotify library
- 🧹 **Clear your target playlist** (removes all existing tracks)
- ➕ **Add all liked songs** to the playlist with newest tracks at the top
- 🔄 **Keep everything in sync** - run it anytime to update your playlist

### Lot Radio Artist Finder
- 🔍 **Smart Scraping** - Uses Selenium to extract live schedule from thelotradio.com
- 🎵 **Comprehensive Spotify Analysis** - Fetches 100s of artists across all time ranges
- 🤖 **AI-Powered Matching** - Uses OpenAI GPT-4 to find artistic similarities and recommendations
- 📊 **Detailed Insights** - Comprehensive analysis of your music taste vs Lot Radio programming

## Setup

### 1. Create a Spotify App (Get API Keys)

1. **Go to Spotify Developer Dashboard**
   - Visit [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
   - Log in with your Spotify account

2. **Create a New App**
   - Click "Create app"
   - Fill in the form:
     - **App name**: `Spotisync` (or any name you prefer)
     - **App description**: `Personal playlist sync tool`
     - **Website**: Leave blank or use `http://localhost`
     - **Redirect URI**: `http://127.0.0.1:8080/callback` ⚠️ **Important: Use this exact URL**
   - Check the boxes to agree to terms
   - Click "Save"

3. **Get Your Credentials**
   - Click on your newly created app
   - Click "Settings" in the top right
   - Copy your **Client ID** and **Client Secret** (click "View client secret")

4. **Create a Target Playlist** (For Spotisync)
   - Go to Spotify and create a new playlist where you want your liked songs synced
   - Make sure it's set to **Public** if you want others to see it
   - Copy the playlist ID from the URL (e.g., `spotify.com/playlist/YOUR_PLAYLIST_ID`)

### 2. Get OpenAI API Key (For Lot Radio Finder)

1. **Go to OpenAI**
   - Visit [platform.openai.com](https://platform.openai.com/)
   - Sign up or log in

2. **Get API Key**
   - Go to API Keys section
   - Create a new API key
   - Copy the API key

### 3. Installation

```bash
# Clone or download this repository
# Navigate to the spotisync directory

# Install pipenv if you don't have it
pip install pipenv

# Install dependencies
pipenv install

# Copy environment template
cp .env.example .env
```

### 4. Configuration

Edit the `.env` file with your credentials:

```env
# Required for both tools
SPOTIPY_CLIENT_ID=your_client_id_from_step_1
SPOTIPY_CLIENT_SECRET=your_client_secret_from_step_1
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8080/callback

# Required for Spotisync
PLAYLIST_ID=your_playlist_id_from_step_1

# Required for Lot Radio Finder
OPENAI_API_KEY=your_openai_api_key_from_step_2
```

## How to Run

### Spotisync
```bash
./run.sh
```

### Lot Radio Finder
```bash
./lot_radio.sh
```

### First Time Setup
- On first run, your browser will open asking you to authorize the app
- Click "Agree" to grant permissions
- You'll be redirected to a callback URL (this is normal, even if the page doesn't load)
- The sync will start automatically

## Features

### Spotisync
- ✅ **Complete sync** - All your liked songs in one playlist
- ✅ **Newest first** - Most recent likes appear at the top
- ✅ **Auto-refresh** - Clears and rebuilds the playlist each time
- ✅ **One-command execution** - Just run and forget
- ✅ **Safe authentication** - Uses official Spotify OAuth
- ✅ **Clean dependencies** - Managed with pipenv

### Lot Radio Finder
- ✅ **Live Schedule** - Gets the current week's schedule from The Lot Radio
- ✅ **Exact Matches** - Finds artists you know who are playing this week
- ✅ **Smart Recommendations** - Suggests shows based on your music taste
- ✅ **Terminal-Friendly** - Clean output format designed for terminal use
- ✅ **AI Analysis** - Powered by OpenAI GPT-4.1 for accurate recommendations

## Troubleshooting

**"Missing required environment variables"**
- Double-check your `.env` file has all required variables set

**"Error accessing playlist"**
- Make sure the playlist ID is correct
- Ensure the playlist exists and you have access to it

**Authentication issues**
- Delete the `.cache` file and run again
- Make sure your redirect URI is exactly `http://127.0.0.1:8080/callback`

**Selenium issues with Lot Radio Finder**
- Make sure Chrome and ChromeDriver are installed
- Try running `pip install selenium` if not included in pipenv