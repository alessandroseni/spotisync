<!-- 099ca6f1-b816-4624-b5f7-43b92cedbddd c422060a-40ba-48b9-9b4f-15974333ef09 -->
# Music Discovery Agent CLI

## Implementation Progress

- [x] Create folder structure and __init__.py
- [x] Implement data_manager.py (CSV storage + Spotify fetching) - 354 lines
- [x] Implement agent_tools.py (5 OpenAI agent tools) - 251 lines
- [x] Implement music_agent.py (OpenAI Agents SDK setup) - 210 lines
- [x] Implement ui.py (rich + prompt_toolkit interface) - 198 lines
- [x] Implement main.py (entry point + interactive loop) - 166 lines
- [x] Create discover.sh launch script
- [x] Update Pipfile with dependencies (added rich + prompt-toolkit)
- [x] Update .gitignore for data/ folder
- [x] Create README.md for music_discovery service
- [ ] Install dependencies: `pipenv install`
- [ ] Test end-to-end flow: `./discover.sh`

**Total Implementation**: 1,182 lines of Python code across 6 files

## Architecture Overview

Create a `music_discovery/` service folder containing all components:

1. **Data Layer** - CSV-based storage for user's Spotify data
2. **Agent Layer** - OpenAI Agents SDK with custom tools
3. **UI Layer** - Interactive terminal using `rich` and `prompt_toolkit`

**Folder Structure**:

```
spotisync/
├── .env                          # Shared config (root)
├── spotisync.py                  # Existing
├── lot_radio_finder.py          # Existing
├── discover.sh                   # New launch script (root)
└── music_discovery/             # New service folder
    ├── __init__.py
    ├── main.py                   # Entry point
    ├── data_manager.py           # CSV storage & Spotify fetching
    ├── agent_tools.py            # OpenAI agent tools
    ├── music_agent.py            # Agent initialization
    ├── ui.py                     # Rich + prompt_toolkit UI
    └── data/                     # CSV storage (gitignored)
        ├── user_profile.csv
        ├── saved_tracks.csv
        ├── saved_albums.csv
        └── top_artists.csv
```

The service reads `.env` from root and can reuse Spotify setup patterns from existing files.

## Component Breakdown

### 1. Data Management (`music_discovery/data_manager.py`)

**Purpose**: Fetch and cache Spotify data in CSVs for fast agent access

**CSVs to create** (in `music_discovery/data/` directory):

- `user_profile.csv` - user_id, display_name, last_updated
- `saved_tracks.csv` - track_id, name, artists, album, genres, added_at, popularity, spotify_url
- `saved_albums.csv` - album_id, name, artists, genres, release_date, total_tracks, added_at, spotify_url
- `top_artists.csv` - artist_id, name, genres, popularity, time_range, spotify_url

**Key functions**:

- `setup_spotify_client()` - Initialize Spotify (reuse pattern from `spotisync.py`)
- `ensure_data_dir()` - Create `data/` folder if missing
- `fetch_and_store_tracks(sp)` - Use `sp.current_user_saved_tracks()` with pagination, extract artist genres
- `fetch_and_store_albums(sp)` - Use `sp.current_user_saved_albums()` with pagination
- `fetch_and_store_top_artists(sp)` - Use `sp.current_user_top_artists()` for 3 time ranges
- `refresh_all_data()` - Update all CSVs
- `get_data_stats()` - Return counts for UI display
- `get_genre_summary()` - Aggregate top genres from all CSVs for agent context
- `is_data_stale(days=7)` - Check if CSVs need refresh

**Spotify API calls needed**:

- `current_user_saved_tracks(limit=50)` with pagination
- `current_user_saved_albums(limit=50)` with pagination  
- `current_user_top_artists(limit=50, time_range)` for short/medium/long term
- `artist(artist_id)` to get genre data for tracks

### 2. OpenAI Agent Tools (`music_discovery/agent_tools.py`)

**Tool 1: `search_spotify_artist`**

- Use `sp.search(q=query, type='artist', limit=10)`
- Return: artist name, genres, popularity, Spotify URL
- Tool description: "Search Spotify for artists by name or genre keywords"

**Tool 2: `get_spotify_recommendations`**

- Use `sp.recommendations(seed_artists, seed_genres, seed_tracks, limit=5)` 
- Reference: https://developer.spotify.com/documentation/web-api/reference/get-recommendations
- Accept params: genre seeds (comma-separated), artist IDs (comma-separated), track IDs (comma-separated)
- Return: track name, artists, album, spotify_url
- Tool description: "Get Spotify recommendations based on seed genres, artists, or tracks. Up to 5 seeds total."

**Tool 3: `get_available_genre_seeds`**

- Use `sp.recommendation_genre_seeds()`
- Reference: https://developer.spotify.com/documentation/web-api/reference/get-recommendation-genres
- Return: list of valid genre seed strings
- Tool description: "Get the complete list of genre seeds available for Spotify recommendations"

**Tool 4: `search_music_web`** (via Brave Search MCP)

- Call Brave Search MCP `brave_web_search` tool
- Query format: "{genre/artist} music recommendations 2025" or "{artist} similar artists"
- Parse top 5 results, extract artist/album mentions
- Return: concise summary with sources
- Tool description: "Search the web for music recommendations, similar artists, and genre exploration"

**Tool 5: `read_user_music_profile`**

- Read CSVs using pandas
- Return formatted summary:
  - Total tracks/albums/artists
  - Top 10 genres with counts
  - Top 10 artists by time range
  - Recently added tracks (last 10)
- Tool description: "Access user's Spotify library summary including top genres, favorite artists, and recent additions"

**Tool initialization pattern**:

```python
from openai import OpenAI

def create_agent_tools(spotify_client):
    """Create tool definitions for OpenAI agent"""
    
    def search_spotify_artist(query: str) -> str:
        # Implementation
        pass
    
    # Return list of tool functions
    return [search_spotify_artist, get_spotify_recommendations, ...]
```

### 3. Agent Core (`music_discovery/music_agent.py`)

**OpenAI Agents SDK implementation**:

```python
from openai import OpenAI

def create_music_agent(tools):
    """Initialize music discovery agent"""
    
    client = OpenAI()  # Uses OPENAI_API_KEY from env
    
    agent = client.beta.assistants.create(
        name="Music Discovery Assistant",
        model="gpt-4o",  # or "gpt-4o-mini" for faster responses
        instructions="""You are a music discovery expert helping users explore new music based on their Spotify listening history.

Your goals:
1. Understand the user's input - it could be a genre (e.g., "Latin Rock"), artist name (e.g., "Gustavo Cerati"), album, or vibe description
2. ALWAYS start by reading the user's music profile to understand their taste
3. Find 2-5 carefully curated recommendations (never just 1, never more than 5)
4. Mix multiple sources: Spotify API recommendations + web research for variety
5. For each recommendation, provide: artist/album name, genre, why it matches their taste, Spotify URL

Important guidelines:
- Be conversational and enthusiastic about music
- Introduce variety - same query should yield different results using randomness in your approach
- When searching the web, prioritize hidden gems and emerging artists over mainstream picks
- If user mentions a specific artist/album, check if it's already in their library first
- Always explain WHY each recommendation fits their taste based on their listening history
- Format recommendations clearly with one per section""",
        tools=tools
    )
    
    return agent, client

def run_agent_query(agent, thread_id, client, user_query):
    """Execute agent query and return response"""
    # Create message
    # Run agent
    # Stream responses
    # Return formatted results
```

**Key flow**:

1. Agent receives user query
2. Calls `read_user_music_profile` to understand taste
3. Interprets query and decides which tools to use
4. May call `get_available_genre_seeds` for valid genres
5. Calls `search_spotify_artist` and/or `get_spotify_recommendations`
6. May call `search_music_web` for additional variety
7. Returns 2-5 curated recommendations with reasoning

### 4. Interactive UI (`music_discovery/ui.py`)

**Using `rich` for display**:

- `rich.console.Console` for colored, formatted output
- `rich.status.Status` for "thinking" animations
- `rich.panel.Panel` for recommendation cards
- `rich.table.Table` for library stats
- `rich.progress.Progress` for data refresh

**Using `prompt_toolkit` for input**:

- `prompt_toolkit.PromptSession` for input with history
- Custom completer for commands: `/refresh`, `/help`, `/quit`, `/stats`
- History saved to `music_discovery/.history`

**Key functions**:

```python
def display_welcome(stats):
    """Show welcome panel with library stats"""

def display_recommendation(rec_data):
    """Display a single recommendation in a panel"""

def display_thinking_status(message):
    """Show thinking animation"""

def get_user_input(session):
    """Get input with command completion"""
```

**UI Flow**:

```
🎵🤖 Music Discovery Agent

┌─ Your Music Library ────────────────────────────┐
│ Tracks: 1,234  Albums: 156  Artists: 289       │
│ Top Genres: indie rock, electronic, jazz        │
│ Last Updated: 2 hours ago                       │
└──────────────────────────────────────────────────┘

Commands: /refresh /stats /help /quit

> Latin American Rock

● Analyzing your taste...
● Searching for recommendations...

┌─ 🎸 Recommendation 1 ───────────────────────────┐
│ Soda Stereo - Canción Animal                    │
│ Genre: Latin Rock, New Wave                     │
│                                                  │
│ Why: You'll love this! Pioneers of Latin rock   │
│ with new wave influences similar to your love   │
│ of The Smiths and indie rock.                   │
│                                                  │
│ 🔗 https://open.spotify.com/album/...          │
└──────────────────────────────────────────────────┘

> /refresh
Refreshing Spotify data...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
✓ Updated 1,245 tracks, 160 albums, 289 artists
```

### 5. Main Entry Point (`music_discovery/main.py`)

**CLI structure**:

```python
#!/usr/bin/env python3
"""
Music Discovery Agent - AI-powered music exploration
Usage: python -m music_discovery.main
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
root_dir = Path(__file__).parent.parent
load_dotenv(root_dir / '.env')

def main():
    # 1. Display welcome
    # 2. Initialize Spotify client
    # 3. Check if CSVs exist, prompt to refresh if missing/stale
    # 4. Load data stats for display
    # 5. Initialize agent with tools
    # 6. Start interactive prompt loop
    # 7. Handle commands: /refresh, /stats, /help, /quit
    # 8. Pass user queries to agent
    # 9. Display results with rich formatting
    # 10. Handle Ctrl+C gracefully

if __name__ == "__main__":
    main()
```

**Shell script** (`discover.sh` in root):

```bash
#!/bin/bash
echo "🎵🤖 Music Discovery Agent"
echo "==========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# Check if pipenv is installed
if ! command -v pipenv &> /dev/null; then
    echo "❌ pipenv not found!"
    exit 1
fi

# Run the service
pipenv run python -m music_discovery.main
```

### 6. Service Init (`music_discovery/__init__.py`)

Simple package initialization:

```python
"""Music Discovery Agent - AI-powered music recommendations"""
__version__ = "0.1.0"
```

## Dependencies to Add

Update `Pipfile` (root):

```
openai = "*"           # OpenAI Agents SDK
rich = "*"             # Terminal UI
prompt-toolkit = "*"   # Interactive prompts
pandas = "*"           # Already exists - CSV handling
```

## Configuration

**Environment variables** (`.env` in root):

- `SPOTIPY_CLIENT_ID` (already exists)
- `SPOTIPY_CLIENT_SECRET` (already exists)
- `OPENAI_API_KEY` (already exists)
- `BRAVE_API_KEY` (new - for Brave Search MCP)

**Add to `.gitignore`**:

```
music_discovery/data/
music_discovery/.history
```

## Security & Privacy

- All CSVs stored locally in `music_discovery/data/`
- Agent receives summarized data (top genres, counts), not full library
- Brave Search queries are generic music queries, no personal info
- Spotify URLs are public and safe to share

## Key Implementation Details

**Genre Extraction** (for tracks):

```python
# Tracks don't have genres - must fetch from primary artist
for track_item in saved_tracks:
    artist_id = track_item['track']['artists'][0]['id']
    artist_info = sp.artist(artist_id)
    genres = ', '.join(artist_info['genres'])
```

**Randomness Strategy**:

- Agent temperature: 0.9 (high creativity)
- Vary seed selection in recommendations (random subset of user's top genres/artists)
- Web search includes "2025" and "emerging" keywords
- Agent instructions encourage trying different tools each run

**Performance**:

- CSVs avoid repeated API calls (cache for 7 days)
- Pandas for fast CSV operations
- Agent tools return concise data (max 10 items per tool call)
- Consider `gpt-4o-mini` if `gpt-4o` is too slow

**Error Handling**:

- Graceful degradation if Brave MCP fails (Spotify-only mode)
- Spotify rate limit: exponential backoff, show friendly message
- CSV corruption: auto-refresh
- Agent errors: log, show user-friendly message, continue

## Testing the Service

1. Set up environment: `pipenv install`
2. Configure `.env` with all API keys
3. Run: `./discover.sh` or `pipenv run python -m music_discovery.main`
4. First run will fetch data (may take 1-2 min)
5. Try queries: "indie rock", "Radiohead", "chill vibes"
6. Test commands: `/refresh`, `/stats`, `/help`

### To-dos

- [ ] Create data_manager.py with CSV storage and Spotify data fetching (tracks, albums, top artists with genre extraction)
- [ ] Implement agent_tools.py with 5 tools: search_spotify_artist, get_spotify_recommendations, get_available_genre_seeds, search_music_web, read_user_music_profile
- [ ] Create music_agent.py using OpenAI Agents SDK with well-crafted system prompt and tool integration
- [ ] Build ui.py with rich for display and prompt_toolkit for input, including live updates and recommendation cards
- [ ] Create music_discovery.py main entry point that orchestrates data refresh, agent initialization, and interactive loop
- [ ] Configure Brave Search MCP integration and add BRAVE_API_KEY to .env.example
- [ ] Update Pipfile with new dependencies (openai, rich, prompt-toolkit) and create discover.sh launch script