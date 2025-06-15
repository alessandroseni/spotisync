#!/usr/bin/env python3
"""
Lot Radio Artist Finder 🎵📻🤖

This script uses AI-powered analysis to match your Spotify listening habits 
with The Lot Radio NYC's schedule and discover new music recommendations.

Usage:
    python lot_radio_finder.py

Requirements:
    - .env file with Spotify and OpenAI credentials
    - Chrome browser + ChromeDriver for Selenium web scraping
"""

# Basic imports
import os
import sys
import random
from bs4 import BeautifulSoup
from datetime import datetime
import re
from collections import Counter

# For Spotify
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# For OpenAI LLM analysis
import openai

# Load environment variables
load_dotenv()

# Helper function to convert time to minutes for duration calculation
def time_to_minutes(time_str):
    """Convert time string like '10:00am' to minutes since midnight"""
    if not time_str:
        return 0
        
    time_str = time_str.lower().strip()
    
    # Handle special cases
    if time_str == "12:00am" or time_str == "midnight":
        return 0  # Midnight = 0 minutes
        
    if time_str == "12:00pm" or time_str == "noon":
        return 12 * 60  # Noon = 12 hours * 60 minutes
    
    # Regular parsing
    try:
        # Extract hours, minutes, and am/pm
        match = re.search(r'(\d{1,2}):(\d{2})(am|pm)', time_str)
        if not match:
            return 0
            
        hours = int(match.group(1))
        minutes = int(match.group(2))
        am_pm = match.group(3)
        
        # Convert to 24-hour format
        if am_pm == 'pm' and hours < 12:
            hours += 12
        elif am_pm == 'am' and hours == 12:
            hours = 0
            
        return hours * 60 + minutes
    except Exception as e:
        print(f"Error converting time to minutes: {e}")
        return 0

# Terminal colors for better readability
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

# Scrape The Lot Radio using Selenium (JavaScript-rendered content)
def scrape_lot_radio_schedule():
    """Extract live schedule from The Lot Radio using Selenium"""
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        
        print("🚀 Setting up Chrome WebDriver...")
        
        # Configure Chrome to run headlessly  
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")  # Larger window size to ensure all content loads
        
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        
        print("📖 Loading The Lot Radio website...")
        driver.get("https://www.thelotradio.com")
        
        # Wait for JavaScript to load the schedule
        print("⏳ Waiting for schedule to load...")
        try:
            # Wait up to 15 seconds for the schedule to appear
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "schedule"))
            )
            print("✅ Schedule element found, waiting for content to fully load...")
        except Exception as e:
            print(f"⚠️ Schedule element not found, continuing with static wait: {e}")
        
        # Additional wait to ensure all JavaScript renders
        time.sleep(12)  # Increased from 8 to 12 seconds
        
        # Extract the page content after JS rendering
        page_source = driver.page_source
        
        # Try to get direct schedule data if possible
        schedule_data = []
        try:
            # First try to get schedule days
            schedule_days = driver.find_elements(By.CLASS_NAME, "schedule-day")
            if schedule_days:
                print("🔍 Found schedule days, extracting...")
                for day_elem in schedule_days:
                    day_name = day_elem.find_element(By.TAG_NAME, "h3").text.strip()
                    print(f"   📅 Processing {day_name}...")
                    
                    # Get all show rows for this day
                    show_rows = day_elem.find_elements(By.CLASS_NAME, "schedule-row")
                    for row in show_rows:
                        try:
                            time_elem = row.find_element(By.CLASS_NAME, "schedule-time").text.strip()
                            show_elem = row.find_element(By.CLASS_NAME, "schedule-show").text.strip()
                            
                            # Parse time range (e.g., "10:00am - 12:00pm")
                            if "-" in time_elem:
                                start_time, end_time = time_elem.split("-")
                                start_time = start_time.strip()
                                end_time = end_time.strip()
                                
                                # Make sure we have valid times
                                if re.match(r'\d{1,2}:\d{2}(?:am|pm)', start_time) and re.match(r'\d{1,2}:\d{2}(?:am|pm)', end_time):
                                    schedule_data.append({
                                        'day': day_name,
                                        'start_time': start_time,
                                        'end_time': end_time,
                                        'show_name': show_elem,
                                        'artist': extract_artist_from_show(show_elem)
                                    })
                                    print(f"      ✓ Added: {start_time}-{end_time}: {show_elem}")
                                else:
                                    print(f"      ⚠️ Invalid time format: {time_elem}")
                            else:
                                print(f"      ⚠️ No time range found in: {time_elem}")
                        except Exception as e:
                            print(f"      ⚠️ Error parsing show row: {e}")
                
                print(f"✅ Successfully extracted {len(schedule_data)} shows directly from DOM")
        except Exception as e:
            print(f"⚠️ Could not extract schedule directly: {e}")
        
        driver.quit()
        
        # Parse the rendered content
        soup = BeautifulSoup(page_source, 'html.parser')
        rendered_text = soup.get_text()
        
        print_success("✅ Successfully scraped schedule data!")
        return rendered_text, schedule_data
        
    except ImportError:
        print_error("❌ Selenium not installed. Run: pip install selenium")
        print_error("❌ Also need ChromeDriver")
        return None, []
        
    except Exception as e:
        print_error(f"❌ Error with Selenium: {e}")
        return None, []

def parse_schedule_data(raw_text, direct_schedule_data=None):
    """Parse the raw schedule text into structured data"""
    
    shows = []
    
    # First try to use direct schedule data from the DOM if available
    if direct_schedule_data and len(direct_schedule_data) > 0:
        print_success(f"✅ Using {len(direct_schedule_data)} shows extracted directly from DOM")
        shows = direct_schedule_data.copy()
        
        # Check if we have a reasonable amount of shows (at least 30)
        # If not, we'll also try text parsing and merge the results
        if len(shows) >= 30:
            return shows
        else:
            print_warning(f"⚠️ Only found {len(shows)} shows from DOM, will also try text parsing")
    
    if not raw_text:
        print_error("❌ No raw schedule data to parse")
        return shows  # Return whatever we have from DOM extraction
    
    print("📝 Parsing schedule data from text...")
    
    # Split into lines and clean up
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    
    # Find the line that contains the schedule (usually the longest line with days/times)
    schedule_line = ""
    for line in lines:
        if ('monday' in line.lower() or 'tuesday' in line.lower()) and len(line) > 500:
            schedule_line = line
            break
    
    if not schedule_line:
        print_error("❌ Could not find schedule data in scraped content")
        return shows  # Return whatever we have from DOM extraction
    
    print(f"📄 Found schedule line with {len(schedule_line)} characters")
    
    # Parse the schedule using regex patterns
    text_parsed_shows = []
    
    # Pattern to match time ranges and show names - improved to better handle 24-hour format and late-night shows
    # Looking for patterns like "1:00pm - 2:00pm" or "10:00pm - 12:00am" followed by show name
    time_pattern = r'(\d{1,2}:\d{2}(?:am|pm))\s*-\s*(\d{1,2}:\d{2}(?:am|pm))\s*([^0-9]*?(?:[^0-9]:)?[^0-9]*?)(?=\d{1,2}:\d{2}(?:am|pm)|$)'
    
    # Also try to extract day information
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for day in days:
        if day.lower() in schedule_line.lower():
            # Find the position and extract shows for this day
            # Improved regex to better capture shows that span into late night
            day_pattern = f'{day}.*?(?={"|".join([d for d in days if d != day])}|$)'
            day_content_match = re.search(day_pattern, schedule_line, re.IGNORECASE | re.DOTALL)
            
            if day_content_match:
                day_content = day_content_match.group(0)
                # Extract time patterns from this day's content
                time_matches = re.findall(time_pattern, day_content, re.IGNORECASE)
                
                for start_time, end_time, show_name in time_matches:
                    if show_name.strip():
                        text_parsed_shows.append({
                            'day': day,
                            'start_time': start_time,
                            'end_time': end_time,
                            'show_name': show_name.strip(),
                            'artist': extract_artist_from_show(show_name.strip())
                        })
    
    print_success(f"✅ Parsed {len(text_parsed_shows)} shows from schedule text")
    
    # If the regex approach didn't work well, try a simpler split approach
    if len(text_parsed_shows) < 10:
        print("🔄 Trying alternative parsing method...")
        text_parsed_shows = parse_schedule_simple(schedule_line)
    
    # Merge DOM data with text-parsed data
    # First create a set of existing show keys to avoid duplicates
    existing_shows = {f"{show['day']}|{show['start_time']}|{show['end_time']}" for show in shows}
    
    # Add text-parsed shows that aren't already in the list
    for show in text_parsed_shows:
        show_key = f"{show['day']}|{show['start_time']}|{show['end_time']}"
        if show_key not in existing_shows:
            shows.append(show)
            existing_shows.add(show_key)
    
    print_success(f"✅ Final show count after merging: {len(shows)}")
    
    return shows

def extract_artist_from_show(show_name):
    """Extract artist name from show title"""
    # Remove common show prefixes/suffixes
    artist = show_name
    
    # Handle special cases for complex shows with multiple artists
    if ':' in artist:
        # For format like "Show Name: Artist(s)"
        parts = artist.split(':', 1)
        if len(parts) > 1 and parts[1].strip():
            artist = parts[1].strip()
    
    # Remove "with" and everything before it
    if ' with ' in artist:
        artist = artist.split(' with ')[-1]
    elif ' w/ ' in artist:
        artist = artist.split(' w/ ')[-1]
    
    # Handle "presents" format
    if ' presents ' in artist:
        artist = artist.split(' presents ')[-1]
    
    # Remove show type indicators
    prefixes_to_remove = ['DJ ', 'The ', 'Radio ', 'Show ']
    for prefix in prefixes_to_remove:
        if artist.startswith(prefix):
            artist = artist[len(prefix):]
    
    # Handle "b2b" (back-to-back) DJ sets
    if ' b2b ' in artist.lower():
        # Keep the format as is, it's a collaboration
        pass
    
    return artist.strip()

def parse_schedule_simple(schedule_text):
    """Simpler parsing approach - split by common patterns"""
    shows = []
    
    # Try to split by day names and extract shows
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for day in days:
        if day in schedule_text:
            # Extract everything after this day until the next day
            day_start = schedule_text.find(day)
            next_day_start = len(schedule_text)
            
            for next_day in days:
                if next_day != day and next_day in schedule_text:
                    pos = schedule_text.find(next_day, day_start + 1)
                    if pos > day_start and pos < next_day_start:
                        next_day_start = pos
            
            day_content = schedule_text[day_start:next_day_start]
            
            # Extract time patterns from this day's content - improved to catch late night shows
            time_pattern = r'(\d{1,2}:\d{2}(?:am|pm))\s*-\s*(\d{1,2}:\d{2}(?:am|pm))\s*([^0-9]*?(?:[^0-9]:)?[^0-9]*?)(?=\d{1,2}:\d{2}|$)'
            time_matches = re.findall(time_pattern, day_content, re.IGNORECASE)
            
            for start_time, end_time, show_name in time_matches:
                if show_name.strip():
                    shows.append({
                        'day': day,
                        'start_time': start_time,
                        'end_time': end_time,
                        'show_name': show_name.strip(),
                        'artist': extract_artist_from_show(show_name.strip())
                    })
    
    # Second pass to catch any shows that might have been missed
    # Look specifically for late night patterns (10:00pm-12:00am, etc.)
    late_night_pattern = r'(\d{1,2}:\d{2}pm)\s*-\s*(\d{1,2}:\d{2}am)\s*([^0-9]*?(?:[^0-9]:)?[^0-9]*?)(?=\d{1,2}:\d{2}|$)'
    for day in days:
        if day in schedule_text:
            day_start = schedule_text.find(day)
            next_day_start = len(schedule_text)
            
            for next_day in days:
                if next_day != day and next_day in schedule_text:
                    pos = schedule_text.find(next_day, day_start + 1)
                    if pos > day_start and pos < next_day_start:
                        next_day_start = pos
            
            day_content = schedule_text[day_start:next_day_start]
            late_matches = re.findall(late_night_pattern, day_content, re.IGNORECASE)
            
            for start_time, end_time, show_name in late_matches:
                if show_name.strip():
                    # Check if this show is already in our list to avoid duplicates
                    duplicate = False
                    for existing_show in shows:
                        if (existing_show['day'] == day and 
                            existing_show['start_time'] == start_time and
                            existing_show['end_time'] == end_time):
                            duplicate = True
                            break
                    
                    if not duplicate:
                        shows.append({
                            'day': day,
                            'start_time': start_time,
                            'end_time': end_time,
                            'show_name': show_name.strip(),
                            'artist': extract_artist_from_show(show_name.strip())
                        })
    
    # Third pass: look for multi-hour shows (2pm-4pm, etc.)
    for day in days:
        if day in schedule_text:
            day_start = schedule_text.find(day)
            next_day_start = len(schedule_text)
            
            for next_day in days:
                if next_day != day and next_day in schedule_text:
                    pos = schedule_text.find(next_day, day_start + 1)
                    if pos > day_start and pos < next_day_start:
                        next_day_start = pos
            
            day_content = schedule_text[day_start:next_day_start]
            
            # Try to find all time ranges, especially multi-hour ones
            all_times = re.findall(r'(\d{1,2}:\d{2}(?:am|pm))', day_content)
            for i in range(len(all_times) - 1):
                start_time = all_times[i]
                end_time = all_times[i+1]
                
                # Try to find show name between these times
                pattern = f"{re.escape(start_time)}\\s*-\\s*{re.escape(end_time)}\\s*([^0-9]*?(?:[^0-9]:)?[^0-9]*?)(?=\\d{{1,2}}:\\d{{2}}|$)"
                show_match = re.search(pattern, day_content, re.IGNORECASE)
                
                if show_match:
                    show_name = show_match.group(1).strip()
                    if show_name:
                        # Check if this show is already in our list to avoid duplicates
                        duplicate = False
                        for existing_show in shows:
                            if (existing_show['day'] == day and 
                                existing_show['start_time'] == start_time and
                                existing_show['end_time'] == end_time):
                                duplicate = True
                                break
                        
                        if not duplicate:
                            shows.append({
                                'day': day,
                                'start_time': start_time,
                                'end_time': end_time,
                                'show_name': show_name,
                                'artist': extract_artist_from_show(show_name)
                            })
    
    # Fourth pass: try to find longer shows by looking for consecutive times
    # This is especially for shows like "5:00pm-8:00pm" that might be missed
    for day in days:
        if day in schedule_text:
            day_start = schedule_text.find(day)
            next_day_start = len(schedule_text)
            
            for next_day in days:
                if next_day != day and next_day in schedule_text:
                    pos = schedule_text.find(next_day, day_start + 1)
                    if pos > day_start and pos < next_day_start:
                        next_day_start = pos
            
            day_content = schedule_text[day_start:next_day_start]
            
            # Look for patterns like "5:00pm-8:00pm"
            long_show_pattern = r'(\d{1,2}:\d{2}(?:am|pm))\s*-\s*(\d{1,2}:\d{2}(?:am|pm))\s*([^0-9]*?(?:[^0-9]:)?[^0-9]*?)(?=\d{1,2}:\d{2}(?:am|pm)|$)'
            long_matches = re.findall(long_show_pattern, day_content, re.IGNORECASE)
            
            for start_time, end_time, show_name in long_matches:
                show_name = show_name.strip()
                if show_name:
                    # Check for duplicate
                    duplicate = False
                    for existing_show in shows:
                        if (existing_show['day'] == day and 
                            existing_show['start_time'] == start_time and
                            existing_show['end_time'] == end_time):
                            duplicate = True
                            break
                    
                    if not duplicate:
                        # Check if this is a multi-hour show
                        start_mins = time_to_minutes(start_time)
                        end_mins = time_to_minutes(end_time)
                        duration = (end_mins - start_mins) % (24 * 60)  # Handle overnight shows
                        
                        if duration > 60:  # More than 1 hour
                            shows.append({
                                'day': day,
                                'start_time': start_time,
                                'end_time': end_time,
                                'show_name': show_name,
                                'artist': extract_artist_from_show(show_name)
                            })
    
    return shows

def setup_spotify_client():
    """Set up Spotify client using existing credentials"""
    
    client_id = os.getenv('SPOTIPY_CLIENT_ID')
    client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')  
    redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:8080/callback')
    
    if not all([client_id, client_secret]):
        print_error("❌ Missing Spotify credentials in .env file")
        return None
    
    # Scope for getting user's top artists
    # Add user-follow-read for followed artists and user-read-recently-played for recently played tracks
    scope = "user-top-read user-library-read user-follow-read user-read-recently-played"
    
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope
        ))
        
        # Test the connection
        user_info = sp.current_user()
        print_success(f"✅ Connected to Spotify as: {user_info['display_name']} (@{user_info['id']})")
        
        return sp
        
    except Exception as e:
        print_error(f"❌ Error setting up Spotify client: {e}")
        return None

def get_comprehensive_spotify_data(sp):
    """Get comprehensive Spotify data: top artists, saved artists, and recently played"""
    
    if not sp:
        print_error("❌ No Spotify client available")
        return []
    
    all_artists = {}  # Use dict to avoid duplicates
    
    try:
        print_info("🎵 Fetching comprehensive Spotify data...")
        
        # 1. Get top artists from multiple time ranges
        time_ranges = [
            ('short_term', '4 weeks'),
            ('medium_term', '6 months'), 
            ('long_term', 'all time')
        ]
        
        for time_range, description in time_ranges:
            print(f"   📊 Getting top artists from {description}...")
            
            # Get multiple batches of 50 artists each (Spotify's max per call)
            for offset in range(0, 150, 50):  # Get up to 150 artists per time range
                try:
                    results = sp.current_user_top_artists(
                        limit=50, 
                        time_range=time_range,
                        offset=offset
                    )
                    
                    if not results['items']:
                        break  # No more artists
                        
                    for item in results['items']:
                        artist_info = {
                            'name': item['name'],
                            'genres': item['genres'],
                            'popularity': item['popularity'],
                            'followers': item['followers']['total'],
                            'spotify_url': item['external_urls']['spotify'],
                            'source': f'top_{time_range}',
                            'spotify_id': item['id']
                        }
                        all_artists[item['id']] = artist_info
                        
                except Exception as e:
                    print_warning(f"      ⚠️  Error getting batch at offset {offset}: {e}")
                    break
        
        # 2. Get saved/followed artists
        print("   💾 Getting your saved/followed artists...")
        try:
            # This gets artists you follow
            followed = sp.current_user_followed_artists(limit=50)
            for item in followed['artists']['items']:
                artist_info = {
                    'name': item['name'],
                    'genres': item['genres'],
                    'popularity': item['popularity'],
                    'followers': item['followers']['total'],
                    'spotify_url': item['external_urls']['spotify'],
                    'source': 'followed',
                    'spotify_id': item['id']
                }
                all_artists[item['id']] = artist_info
        except Exception as e:
            # Don't show the full error, just a simplified message
            print_warning(f"⚠️  Skipping followed artists (missing permissions {e})")
        
        # 3. Get artists from recently played tracks
        print("   🎧 Getting artists from recently played tracks...")
        try:
            recent = sp.current_user_recently_played(limit=50)
            for item in recent['items']:
                track = item['track']
                for artist in track['artists']:
                    if artist['id'] not in all_artists:
                        # Get full artist info
                        try:
                            full_artist = sp.artist(artist['id'])
                            artist_info = {
                                'name': full_artist['name'],
                                'genres': full_artist['genres'],
                                'popularity': full_artist['popularity'],
                                'followers': full_artist['followers']['total'],
                                'spotify_url': full_artist['external_urls']['spotify'],
                                'source': 'recently_played',
                                'spotify_id': full_artist['id']
                            }
                            all_artists[artist['id']] = artist_info
                        except Exception as e:
                            # If we can't get full info, use basic info
                            artist_info = {
                                'name': artist['name'],
                                'genres': [],
                                'popularity': 0,
                                'followers': 0,
                                'spotify_url': artist['external_urls']['spotify'],
                                'source': 'recently_played_basic',
                                'spotify_id': artist['id']
                            }
                            all_artists[artist['id']] = artist_info
                            print_warning(f"⚠️  Error getting artist info for {artist['name']}: {e}")
        except Exception as e:
            # Don't show the full error, just a simplified message
            print_warning(f"⚠️  Skipping recently played tracks (missing permissions): {e}")
        
        final_artists = list(all_artists.values())
        print_success(f"✅ Total unique artists collected: {len(final_artists)}")
        
        # Show source breakdown
        sources = Counter(artist['source'] for artist in final_artists)
        print("   📊 Source breakdown:")
        for source, count in sources.items():
            print(f"      • {source}: {count} artists")
        
        return final_artists
        
    except Exception as e:
        print_error(f"❌ Error fetching comprehensive Spotify data: {e}")
        return []

def prepare_data_for_llm(spotify_artists, lot_radio_shows):
    """Format data for LLM analysis"""
    
    print("📊 Preparing data for LLM analysis...")
    
    # Format Spotify artists data
    spotify_data = {
        "total_artists": len(spotify_artists),
        "artists": []
    }
    
    # Filter out any invalid artist entries
    valid_artists = []
    for artist in spotify_artists:
        if isinstance(artist, dict) and 'popularity' in artist and 'name' in artist and 'genres' in artist:
            valid_artists.append(artist)
        else:
            print_warning(f"⚠️ Skipping invalid artist entry: {artist}")
    
    # Group artists by popularity tiers for better LLM understanding
    high_pop = [a for a in valid_artists if a['popularity'] >= 70]
    med_pop = [a for a in valid_artists if 40 <= a['popularity'] < 70]
    low_pop = [a for a in valid_artists if a['popularity'] < 40]
    
    for tier_list, tier_id, tier_name in [
        (high_pop, "high_popularity", "High Popularity (70+)"),
        (med_pop, "medium_popularity", "Medium Popularity (40-69)"), 
        (low_pop, "low_popularity", "Low Popularity (<40)")
    ]:
        if tier_list:
            sorted_tier = sorted(tier_list, key=lambda x: x['popularity'], reverse=True)[:20]  # Top 20 per tier
            spotify_data["artists"].append({
                "tier": tier_name,
                "count": len(tier_list),
                "top_artists": [
                    {
                        "name": a['name'],
                        "genres": a['genres'],
                        "popularity": a['popularity']
                    } for a in sorted_tier
                ]
            })
    
    # Format Lot Radio shows data
    lot_radio_data = {
        "total_shows": len(lot_radio_shows),
        "shows_by_day": {}
    }
    
    for show in lot_radio_shows:
        day = show['day']
        if day not in lot_radio_data["shows_by_day"]:
            lot_radio_data["shows_by_day"][day] = []
        
        lot_radio_data["shows_by_day"][day].append({
            "time": f"{show['start_time']}-{show['end_time']}",
            "show_name": show['show_name'],
            "artist": show['artist']
        })
    
    # Get genre analysis
    all_genres = []
    for artist in valid_artists:
        all_genres.extend(artist['genres'])
    
    genre_counts = Counter(all_genres)
    top_genres = dict(genre_counts.most_common(15))
    
    return {
        "spotify_data": spotify_data,
        "lot_radio_data": lot_radio_data,
        "user_top_genres": top_genres,
        "analysis_timestamp": datetime.now().isoformat()
    }

def setup_openai_client():
    """Setup OpenAI client with API key"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print_error("❌ Missing OPENAI_API_KEY in .env file")
        return None
    
    openai.api_key = api_key
    print_success("✅ OpenAI client configured")
    return True

def analyze_music_compatibility(formatted_data):
    """Use OpenAI to analyze music compatibility between user and Lot Radio"""
    
    if not formatted_data:
        print_error("❌ No formatted data available for analysis")
        return None
    
    try:
        print("🤖 Starting LLM analysis...")
        
        # Create comprehensive prompt with terminal-friendly output instructions
        prompt = f"""
You are a music expert analyzing compatibility between a user's Spotify listening habits and The Lot Radio NYC's schedule.

## USER'S SPOTIFY DATA:
Total Artists: {formatted_data['spotify_data']['total_artists']}
Top Genres: {formatted_data['user_top_genres']}

Artist Breakdown by Popularity:
"""
        
        # Add artist data
        for tier_data in formatted_data['spotify_data']['artists']:
            prompt += f"\n{tier_data['tier']} ({tier_data['count']} artists):\n"
            for artist in tier_data['top_artists'][:10]:  # Top 10 per tier for prompt
                genres_str = ', '.join(artist['genres'][:3]) if artist['genres'] else 'No genres'
                prompt += f"- {artist['name']} ({artist['popularity']} popularity) - {genres_str}\n"
        
        prompt += f"""
## THE LOT RADIO SCHEDULE:
Total Shows: {formatted_data['lot_radio_data']['total_shows']}

Shows by Day:
"""
        
        # Add Lot Radio schedule
        for day, shows in formatted_data['lot_radio_data']['shows_by_day'].items():
            prompt += f"\n{day} ({len(shows)} shows):\n"
            for show in shows:
                prompt += f"- {show['time']}: {show['show_name']} (Artist: {show['artist']})\n"
        
        prompt += """
## ANALYSIS TASKS:

1. **EXACT MATCHES**: Find ONLY exact matches between the user's Spotify artists and Lot Radio artists who are ACTUALLY playing this week. Do not include artists who are not on this week's schedule.

2. **RECOMMENDATIONS**: Based on the user's music taste, recommend 5-10 Lot Radio shows they would likely enjoy, explaining the musical/genre connections.

3. **OVERALL SUMMARY**: Provide a concise summary of whether this user would enjoy The Lot Radio and which specific shows to prioritize.

## OUTPUT FORMAT REQUIREMENTS:
- Format your response for a terminal display (no markdown, no bold, no italics)
- Use clear section headers with ASCII decorations (e.g., "==== EXACT MATCHES ====")
- Use simple bullet points with dashes (-)
- Keep explanations concise and to the point
- For each recommendation or match, clearly state: DAY, TIME, SHOW NAME, and REASON
- Do not use markdown formatting as this will be displayed in a terminal

Please provide a structured response that covers all these areas with specific examples and reasoning.
"""

        # Call OpenAI API
        response = openai.chat.completions.create(
            model="gpt-4.1",  # Using GPT-4.1 as requested
            messages=[
                {"role": "system", "content": "You are a music expert specializing in electronic music, underground scenes, and radio curation. You have deep knowledge of music genres, artist relationships, and can identify musical similarities across different styles. Format your output for terminal display, not markdown."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2500,
            temperature=0.7
        )
        
        analysis_text = response.choices[0].message.content
        print_success("✅ LLM analysis completed!")
        
        return analysis_text
        
    except Exception as e:
        print_error(f"❌ Error with OpenAI analysis: {e}")
        return None

def display_schedule(shows, day_filter=None):
    """Display the schedule in a nice format, optionally filtered by day"""
    
    if not shows:
        print_error("❌ No shows to display")
        return
    
    # Group by day
    shows_by_day = {}
    for show in shows:
        day = show['day']
        if day not in shows_by_day:
            shows_by_day[day] = []
        shows_by_day[day].append(show)
    
    # Sort days in order
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Filter by day if specified
    if day_filter:
        day_filter = day_filter.capitalize()
        if day_filter in shows_by_day:
            filtered_days = [day_filter]
        else:
            print_warning(f"⚠️ No shows found for {day_filter}")
            return
    else:
        filtered_days = [day for day in day_order if day in shows_by_day]
    
    # Display each day
    for day in filtered_days:
        print(f"\n{day}")
        print("-" * 80)
        
        # Sort shows by start time
        day_shows = shows_by_day[day]
        day_shows.sort(key=lambda x: time_to_minutes(x['start_time']))
        
        # Display shows
        for show in day_shows:
            start_time = show['start_time']
            end_time = show['end_time']
            show_name = show['show_name']
            artist = show['artist']
            
            
            # Highlight late night shows (after 10pm)
            is_late_night = time_to_minutes(start_time) >= 22 * 60
            
            if is_late_night:
                print(f"{start_time}-{end_time}: {show_name} ({artist}) 🌙")
            else:
                print(f"{start_time}-{end_time}: {show_name} ({artist})")
    
    print(f"\n📻 Total shows: {len(shows)}")

def print_spotify_summary(artists):
    """Print a summary of Spotify data with random sample"""
    print_header("YOUR SPOTIFY LIBRARY")
    print("=" * 80)
    
    # Get total artists
    print(f"Total Artists: {len(artists)}")
    
    # Get genre diversity
    all_genres = []
    for artist in artists:
        if 'genres' in artist:
            all_genres.extend(artist['genres'])
    
    if all_genres:
        genre_counts = Counter(all_genres)
        print("\nTop 10 Genres:")
        for genre, count in genre_counts.most_common(10):
            print(f"- {genre} ({count} artists)")
    
    # Print random sample of 10 artists
    if artists:
        print("\nRandom Sample of 10 Artists:")
        sample = random.sample(artists, min(10, len(artists)))
        for artist in sample:
            genres = ', '.join(artist['genres'][:2]) if 'genres' in artist and artist['genres'] else 'No genres'
            print(f"- {artist['name']} ({artist['popularity']} popularity) - {genres}")

def main():
    """Main execution"""
    print_header("LOT RADIO ARTIST FINDER 🎵📻🤖")
    print("=" * 80)
    
    # 1. Scrape The Lot Radio schedule
    raw_schedule_data, direct_schedule_data = scrape_lot_radio_schedule()
    if not raw_schedule_data:
        print_error("❌ Failed to scrape The Lot Radio schedule")
        sys.exit(1)
    
    # 2. Parse schedule data
    parsed_shows = parse_schedule_data(raw_schedule_data, direct_schedule_data)
    if not parsed_shows:
        print_error("❌ Failed to parse schedule data")
        sys.exit(1)
    
    # 3. Set up Spotify client
    spotify_client = setup_spotify_client()
    if not spotify_client:
        print_error("❌ Failed to set up Spotify client")
        sys.exit(1)
    
    # 4. Get comprehensive Spotify data
    my_artists = get_comprehensive_spotify_data(spotify_client)
    if not my_artists:
        print_error("❌ Failed to get Spotify data")
        sys.exit(1)
    
    # 5. Display schedule
    display_schedule(parsed_shows)
    
    # 6. Print Spotify summary with random sample
    print_spotify_summary(my_artists)
    
    # 7. Prepare data for LLM
    formatted_data = prepare_data_for_llm(my_artists, parsed_shows)
    
    # 8. Set up OpenAI client
    openai_available = setup_openai_client()
    
    # 9. Run LLM analysis
    if openai_available and formatted_data:
        print_header("RUNNING AI ANALYSIS")
        print("=" * 80)
        print("This may take 30-60 seconds...")
        
        llm_analysis = analyze_music_compatibility(formatted_data)
        
        if llm_analysis:
            print_header("MUSIC COMPATIBILITY ANALYSIS")
            print("=" * 80)
            print(llm_analysis)
        else:
            print_error("❌ LLM analysis failed")
    else:
        print_error("⚠️ OpenAI analysis not available - check API key or data preparation")
    
    # 10. Print summary
    print_header("ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"🎵 Spotify: {len(my_artists)} artists analyzed")
    print(f"📻 Lot Radio: {len(parsed_shows)} shows analyzed")
    print("🤖 AI-powered recommendations generated")
    print("\nHappy music discovering! 🎧")

if __name__ == "__main__":
    main() 