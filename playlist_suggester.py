#!/usr/bin/env python3
"""
Playlist Suggester 🎵🤖

An AI-powered tool that analyzes a Spotify playlist to detect duplicate tracks
and suggest new music additions based on the existing content.

Usage:
    python playlist_suggester.py

Requirements:
    - .env file with Spotify and OpenAI credentials
    - SUGGESTIONS_PLAYLIST_ID environment variable set
"""

# Basic imports
import os
import sys
from collections import Counter
from datetime import datetime

# For Spotify
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# For OpenAI LLM analysis
import openai

# Load environment variables
load_dotenv()

# Terminal colors for better readability (reused from lot_radio_finder.py)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{text}{Colors.ENDC}\n")

def print_subheader(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{text}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.GREEN}{text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}{text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}{text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.CYAN}{text}{Colors.ENDC}")


def setup_spotify_client():
    """Set up Spotify client using existing credentials"""
    
    client_id = os.getenv('SPOTIPY_CLIENT_ID')
    client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')  
    redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:8080/callback')
    
    if not all([client_id, client_secret]):
        print_error("❌ Missing Spotify credentials in .env file")
        print_error("   Required: SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET")
        return None
    
    # Scope for reading playlists
    scope = "playlist-read-private playlist-read-collaborative"
    
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope
        ))
        
        # Test the connection
        sp.current_user()
        
        return sp
        
    except Exception as e:
        print_error(f"❌ Error setting up Spotify client: {e}")
        return None


def fetch_playlist_tracks(sp, playlist_id):
    """Fetch all tracks from the specified playlist"""
    
    if not sp:
        print_error("❌ No Spotify client available")
        return None, []
    
    try:
        # Get playlist info
        playlist = sp.playlist(playlist_id)
        
        # Fetch all tracks with pagination
        all_tracks = []
        offset = 0
        limit = 100
        
        while True:
            results = sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
            items = results['items']
            
            if not items:
                break
                
            all_tracks.extend(items)
            offset += limit
        
        return playlist, all_tracks
        
    except Exception as e:
        print_error(f"❌ Error fetching playlist: {e}")
        return None, []


def prepare_track_data(playlist, tracks):
    """Prepare track data for LLM analysis"""
    
    track_list = []
    all_artists = []
    release_years = []
    
    for idx, item in enumerate(tracks, 1):
        if not item['track']:
            continue
        
        track = item['track']
        
        # Extract track metadata
        track_name = track['name']
        track_artists = [artist['name'] for artist in track['artists']]
        album_name = track['album']['name']
        track_uri = track['uri']
        track_id = track['id']
        popularity = track.get('popularity', 0)
        
        # Extract release year
        release_date = track['album'].get('release_date', '')
        release_year = None
        if release_date:
            try:
                release_year = int(release_date.split('-')[0])
                release_years.append(release_year)
            except:
                pass
        
        track_info = {
            'index': idx,
            'name': track_name,
            'artists': track_artists,
            'album': album_name,
            'uri': track_uri,
            'id': track_id,
            'popularity': popularity,
            'release_year': release_year
        }
        
        track_list.append(track_info)
        all_artists.extend(track_artists)
    
    # Artist frequency analysis
    artist_counts = Counter(all_artists)
    unique_artists = len(artist_counts)
    
    # Era distribution
    era_distribution = {}
    if release_years:
        for year in release_years:
            decade = (year // 10) * 10
            era_distribution[decade] = era_distribution.get(decade, 0) + 1
    
    return {
        'playlist_name': playlist['name'],
        'playlist_owner': playlist['owner']['display_name'],
        'total_tracks': len(track_list),
        'tracks': track_list,
        'artist_counts': artist_counts,
        'unique_artists': unique_artists,
        'era_distribution': era_distribution
    }


def setup_openai_client():
    """Setup OpenAI client with API key"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print_error("❌ Missing OPENAI_API_KEY in .env file")
        return None
    
    openai.api_key = api_key
    return True


def build_llm_prompt(data):
    """Build comprehensive prompt for LLM analysis"""
    
    tracks = data['tracks']
    artist_counts = data['artist_counts']
    
    # Build the prompt
    prompt = f"""You are a music expert with deep knowledge of rock music, particularly Latin American rock.

## PLAYLIST INFORMATION:
- Name: {data['playlist_name']}
- Total Tracks: {data['total_tracks']}
- Unique Artists: {data['unique_artists']}

## TOP ARTISTS (by track count):
"""
    
    # Add top 20 artists
    for artist, count in artist_counts.most_common(20):
        prompt += f"- {artist}: {count} track{'s' if count > 1 else ''}\n"
    
    prompt += f"\n## COMPLETE TRACK LIST:\n"
    
    # Add all tracks
    for track in tracks:
        artists_str = ', '.join(track['artists'])
        year_str = f" ({track['release_year']})" if track['release_year'] else ""
        prompt += f"{track['index']}. \"{track['name']}\" by {artists_str} - Album: {track['album']}{year_str}\n"
    
    prompt += """

## YOUR TASKS:

### TASK 1: DEDUPLICATION ANALYSIS
Analyze the track list to identify ONLY exact duplicates. Focus exclusively on:
- The SAME song by the SAME artist appearing multiple times
- Ignore differences in version suffixes (like "- Remastered", "- Live", "- MTV Unplugged", "- Acoustic")
- Compare the core song title without version descriptors

IMPORTANT: Only flag tracks where the base song title and artist match. Different songs by the same artist are NOT duplicates. Different versions (live, remastered, etc.) of the same song ARE duplicates.

For each duplicate found, list:
- The track positions and full names
- Note that they are the same song

If NO duplicates are found, clearly state: "NO DUPLICATES FOUND - The playlist is clean!"

### TASK 2: TRACK SUGGESTIONS (15-20 tracks)
Based on the playlist's musical identity and existing content, suggest 15-20 tracks that would be excellent additions. Follow these guidelines:

1. **Balance and Diversity**: 
   - Include a mix of artists already in the playlist (deep cuts they might not know) and related artists not yet included
   - Avoid over-suggesting from artists who already have many tracks (e.g., if an artist has 9 tracks, suggest max 1-2 more)
   - Consider different eras and regional varieties within the genre

2. **Quality over Quantity**:
   - Suggest tracks that genuinely fit the playlist's vibe
   - Include both well-known classics that might be missing and quality deep cuts
   - Be creative but not too obscure

## OUTPUT FORMAT REQUIREMENTS:

Format your response for terminal display (NO markdown formatting). Use this structure:

==== DEDUPLICATION ANALYSIS ====

[Your analysis here - either list exact duplicates or state "NO DUPLICATES FOUND - The playlist is clean!"]

==== TRACK SUGGESTIONS ====

List each suggestion as a simple numbered list starting from 1:

1. "Song Name" (Artist Name) - Album Name (Year)
2. "Song Name" (Artist Name) - Album Name (Year)
...and so on

Do NOT include:
- "Track" prefix or continuation numbers beyond the list
- Reason or explanation lines
- Any additional commentary per track

==== SUMMARY ====

[Brief 2-3 sentence summary of the playlist's character and your overall suggestion approach]

IMPORTANT: 
- Use simple ASCII formatting (===, ---, bullets with -)
- NO markdown (no **, no ##, no backticks)
- Keep it clean and readable in a terminal
- Follow the exact format shown above
"""
    
    return prompt


def analyze_playlist_with_llm(data):
    """Use OpenAI to analyze playlist for duplicates and suggestions"""
    
    if not data:
        print_error("❌ No playlist data available for analysis")
        return None
    
    try:
        prompt = build_llm_prompt(data)
        
        # Call OpenAI API
        response = openai.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a music expert specializing in rock music with deep knowledge of Latin American rock history, artists, and connections between musical styles. You provide thoughtful, well-researched music recommendations. Format your output for terminal display without markdown."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.7
        )
        
        analysis_text = response.choices[0].message.content
        
        return analysis_text
        
    except Exception as e:
        print_error(f"❌ Error with OpenAI analysis: {e}")
        return None


def display_results(data, llm_analysis):
    """Display the analysis results in terminal"""
    
    print(f"\n{data['playlist_name']} ({data['total_tracks']} tracks, {data['unique_artists']} artists)\n")
    print(llm_analysis)


def main():
    """Main execution"""
    # Get playlist ID from environment
    playlist_id = os.getenv('SUGGESTIONS_PLAYLIST_ID')
    if not playlist_id:
        print_error("❌ Missing SUGGESTIONS_PLAYLIST_ID in .env file")
        sys.exit(1)
    
    # Set up Spotify client
    spotify_client = setup_spotify_client()
    if not spotify_client:
        print_error("❌ Failed to set up Spotify client")
        sys.exit(1)
    
    # Fetch playlist tracks
    playlist, tracks = fetch_playlist_tracks(spotify_client, playlist_id)
    if not playlist or not tracks:
        print_error("❌ Failed to fetch playlist tracks")
        sys.exit(1)
    
    # Prepare track data for analysis
    data = prepare_track_data(playlist, tracks)
    
    # Set up OpenAI client
    openai_available = setup_openai_client()
    if not openai_available:
        print_error("❌ Failed to set up OpenAI client")
        sys.exit(1)
    
    # Run LLM analysis
    llm_analysis = analyze_playlist_with_llm(data)
    
    if not llm_analysis:
        print_error("❌ LLM analysis failed")
        sys.exit(1)
    
    # Display results
    display_results(data, llm_analysis)


if __name__ == "__main__":
    main()
