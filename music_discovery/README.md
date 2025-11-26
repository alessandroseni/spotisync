# Music Discovery Agent

AI-powered music recommendations based on your Spotify listening history.

## Features

- 🎵 Personalized music discovery using OpenAI Agents SDK
- 📊 Analyzes your Spotify library (tracks, albums, top artists)
- 🎸 Genre-aware recommendations
- 💾 Local CSV caching for fast access
- 🎨 Beautiful terminal UI with `rich` and **markdown rendering**
- ✨ Rich text formatting: **bold**, *italics*, headings, clickable links

## Setup

1. Install dependencies:
   ```bash
   pipenv install
   ```

2. Ensure your `.env` file has:
   ```
   SPOTIPY_CLIENT_ID=your_spotify_client_id
   SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
   OPENAI_API_KEY=your_openai_api_key
   ```

3. Run the agent:
   ```bash
   ./discover.sh
   ```
   
   Or directly:
   ```bash
   pipenv run python -m music_discovery.main
   ```

## Usage

### Interactive Queries

Just describe what you're looking for:
- "Latin American Rock"
- "Indie music like Radiohead"
- "Chill electronic vibes"
- "Artists similar to Gustavo Cerati"

### Commands

- `/refresh` - Update your Spotify library data
- `/stats` - Show detailed library statistics and top genres
- `/help` - Display help information
- `/quit` - Exit the application

### Example Output

The agent responds with beautifully formatted markdown:

```
You're a fan of Argentine Rock! 🎸

## 1. **Airbag**
*Genre*: Argentine Rock

**Why You'll Love It**: Known for their nostalgic rock tunes, Airbag 
captures the classic Argentine rock spirit with a modern twist.

- [Listen on Spotify](https://open.spotify.com/artist/1wKDCglKV4FsFS85r2Dmpr)
  🔗 https://open.spotify.com/artist/1wKDCglKV4FsFS85r2Dmpr

## 2. **Los Enanitos Verdes**  
*Genre*: Argentine Rock, Rock en Español

**Why You'll Love It**: With hits that have shaped the rock en español
movement, their catchy melodies align with your taste.

- [Listen on Spotify](https://open.spotify.com/artist/4TK1gDgb7QKoPFlzRrBRgR)
  🔗 https://open.spotify.com/artist/4TK1gDgb7QKoPFlzRrBRgR
```

All text is rendered with proper formatting: **bold**, *italics*, clickable links (with URLs shown for easy copying), and styled headings!

**Note**: Spotify URLs are displayed both as markdown links (clickable in supported terminals like iTerm2, Hyper, or modern terminal emulators) and as raw URLs for easy copy-pasting.

## How It Works

1. **Data Collection**: Fetches your saved tracks, albums, and top artists from Spotify
2. **Local Storage**: Caches data in CSV files (refreshes weekly)
3. **AI Analysis**: OpenAI agent analyzes your taste and finds recommendations
4. **Smart Search**: Uses Spotify's recommendation API and artist search
5. **Personalized Results**: Each query considers your listening history
6. **Rich Formatting**: Recommendations display with markdown formatting (headings, bold, italics, clickable links)

## Tools Available to Agent

- `search_spotify_artist` - Search for artists by name or genre
- `get_spotify_recommendations` - Get Spotify's algorithmic recommendations
- `get_available_genre_seeds` - List valid genre seeds for recommendations
- `read_user_music_profile` - Access your listening history summary
- `search_music_web` - Web search for additional discovery (requires setup)

## Data Privacy

- All data stored locally in `music_discovery/data/` (gitignored)
- Agent only receives summarized profile (top genres, artists)
- No personal data sent to external services beyond Spotify/OpenAI APIs

## Architecture

```
music_discovery/
├── __init__.py           - Package initialization
├── main.py               - Entry point & interactive loop
├── data_manager.py       - Spotify data fetching & CSV storage
├── agent_tools.py        - OpenAI agent tool definitions
├── music_agent.py        - OpenAI Agents SDK setup
├── ui.py                 - Rich terminal interface
└── data/                 - Local CSV cache (auto-created)
```

## Troubleshooting

**"Missing Spotify credentials"**
- Check your `.env` file has all required variables
- Verify credentials are correct at https://developer.spotify.com/dashboard

**"Failed to initialize agent"**
- Verify `OPENAI_API_KEY` in `.env`
- Check you have OpenAI API credits

**"No data found"**
- Run `/refresh` command to fetch your Spotify library
- First fetch may take 1-2 minutes for large libraries

