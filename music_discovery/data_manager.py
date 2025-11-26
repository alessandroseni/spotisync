#!/usr/bin/env python3
"""
Data Manager - CSV storage and Spotify data fetching
"""

import os
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv


class DataManager:
    """Manages CSV storage and Spotify data fetching"""
    
    def __init__(self):
        """Initialize data manager"""
        self.data_dir = Path(__file__).parent / 'data'
        self.sp = None
        
    def ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_spotify_client(self):
        """Initialize Spotify client with proper scopes"""
        # Load environment variables from root .env
        root_dir = Path(__file__).parent.parent
        load_dotenv(root_dir / '.env')
        
        client_id = os.getenv('SPOTIPY_CLIENT_ID')
        client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
        redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
        
        if not all([client_id, client_secret, redirect_uri]):
            raise ValueError("Missing Spotify credentials in .env file")
        
        # Scope for reading user data
        scope = "user-library-read user-top-read"
        
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope
        ))
        
        return self.sp
    
    def fetch_and_store_tracks(self, sp=None):
        """Fetch and store user's saved tracks"""
        if sp is None:
            sp = self.sp
            
        print("📥 Fetching saved tracks...")
        
        tracks_data = []
        offset = 0
        limit = 50
        
        while True:
            results = sp.current_user_saved_tracks(limit=limit, offset=offset)
            items = results['items']
            
            if not items:
                break
            
            for item in items:
                track = item['track']
                if not track:
                    continue
                
                # Get primary artist's genres
                artist_id = track['artists'][0]['id']
                try:
                    artist_info = sp.artist(artist_id)
                    genres = ', '.join(artist_info['genres']) if artist_info['genres'] else ''
                except:
                    genres = ''
                
                tracks_data.append({
                    'track_id': track['id'],
                    'name': track['name'],
                    'artists': ', '.join([a['name'] for a in track['artists']]),
                    'album': track['album']['name'],
                    'genres': genres,
                    'added_at': item['added_at'],
                    'popularity': track['popularity'],
                    'spotify_url': track['external_urls']['spotify']
                })
            
            offset += limit
            print(f"   Retrieved {len(tracks_data)} tracks...")
        
        # Write to CSV
        csv_path = self.data_dir / 'saved_tracks.csv'
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            if tracks_data:
                writer = csv.DictWriter(f, fieldnames=tracks_data[0].keys())
                writer.writeheader()
                writer.writerows(tracks_data)
        
        print(f"✅ Stored {len(tracks_data)} tracks")
        return len(tracks_data)
    
    def fetch_and_store_albums(self, sp=None):
        """Fetch and store user's saved albums"""
        if sp is None:
            sp = self.sp
            
        print("📥 Fetching saved albums...")
        
        albums_data = []
        offset = 0
        limit = 50
        
        while True:
            results = sp.current_user_saved_albums(limit=limit, offset=offset)
            items = results['items']
            
            if not items:
                break
            
            for item in items:
                album = item['album']
                if not album:
                    continue
                
                # Get genres from first artist
                artist_id = album['artists'][0]['id']
                try:
                    artist_info = sp.artist(artist_id)
                    genres = ', '.join(artist_info['genres']) if artist_info['genres'] else ''
                except:
                    genres = ''
                
                albums_data.append({
                    'album_id': album['id'],
                    'name': album['name'],
                    'artists': ', '.join([a['name'] for a in album['artists']]),
                    'genres': genres,
                    'release_date': album['release_date'],
                    'total_tracks': album['total_tracks'],
                    'added_at': item['added_at'],
                    'spotify_url': album['external_urls']['spotify']
                })
            
            offset += limit
            print(f"   Retrieved {len(albums_data)} albums...")
        
        # Write to CSV
        csv_path = self.data_dir / 'saved_albums.csv'
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            if albums_data:
                writer = csv.DictWriter(f, fieldnames=albums_data[0].keys())
                writer.writeheader()
                writer.writerows(albums_data)
        
        print(f"✅ Stored {len(albums_data)} albums")
        return len(albums_data)
    
    def fetch_and_store_top_artists(self, sp=None):
        """Fetch and store user's top artists across time ranges"""
        if sp is None:
            sp = self.sp
            
        print("📥 Fetching top artists...")
        
        artists_data = []
        time_ranges = {
            'short_term': 'last 4 weeks',
            'medium_term': 'last 6 months',
            'long_term': 'all time'
        }
        
        for time_range, description in time_ranges.items():
            print(f"   Fetching {description}...")
            results = sp.current_user_top_artists(limit=50, time_range=time_range)
            
            for artist in results['items']:
                artists_data.append({
                    'artist_id': artist['id'],
                    'name': artist['name'],
                    'genres': ', '.join(artist['genres']) if artist['genres'] else '',
                    'popularity': artist['popularity'],
                    'time_range': time_range,
                    'spotify_url': artist['external_urls']['spotify']
                })
        
        # Write to CSV
        csv_path = self.data_dir / 'top_artists.csv'
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            if artists_data:
                writer = csv.DictWriter(f, fieldnames=artists_data[0].keys())
                writer.writeheader()
                writer.writerows(artists_data)
        
        print(f"✅ Stored {len(artists_data)} top artists")
        return len(artists_data)
    
    def fetch_and_store_user_profile(self, sp=None):
        """Fetch and store user profile"""
        if sp is None:
            sp = self.sp
            
        user = sp.current_user()
        
        profile_data = [{
            'user_id': user['id'],
            'display_name': user.get('display_name', user['id']),
            'last_updated': datetime.now().isoformat()
        }]
        
        csv_path = self.data_dir / 'user_profile.csv'
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=profile_data[0].keys())
            writer.writeheader()
            writer.writerows(profile_data)
    
    def refresh_all_data(self):
        """Update all CSV files with fresh Spotify data"""
        self.ensure_data_dir()
        
        if self.sp is None:
            self.setup_spotify_client()
        
        print("🔄 Refreshing Spotify data...\n")
        
        # Fetch user profile
        self.fetch_and_store_user_profile(self.sp)
        
        # Fetch all data
        tracks_count = self.fetch_and_store_tracks(self.sp)
        albums_count = self.fetch_and_store_albums(self.sp)
        artists_count = self.fetch_and_store_top_artists(self.sp)
        
        print(f"\n✨ Refresh complete!")
        return {
            'tracks': tracks_count,
            'albums': albums_count,
            'artists': artists_count
        }
    
    def get_data_stats(self) -> Dict[str, any]:
        """Get statistics about stored data"""
        stats = {
            'tracks': 0,
            'albums': 0,
            'artists': 0,
            'last_updated': None,
            'data_exists': False
        }
        
        # Check if CSVs exist
        tracks_csv = self.data_dir / 'saved_tracks.csv'
        albums_csv = self.data_dir / 'saved_albums.csv'
        artists_csv = self.data_dir / 'top_artists.csv'
        profile_csv = self.data_dir / 'user_profile.csv'
        
        if not all([tracks_csv.exists(), albums_csv.exists(), artists_csv.exists()]):
            return stats
        
        stats['data_exists'] = True
        
        # Count rows
        with open(tracks_csv, 'r', encoding='utf-8') as f:
            stats['tracks'] = sum(1 for _ in csv.reader(f)) - 1  # Subtract header
        
        with open(albums_csv, 'r', encoding='utf-8') as f:
            stats['albums'] = sum(1 for _ in csv.reader(f)) - 1
        
        with open(artists_csv, 'r', encoding='utf-8') as f:
            stats['artists'] = sum(1 for _ in csv.reader(f)) - 1
        
        # Get last updated time
        if profile_csv.exists():
            with open(profile_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                profile = next(reader, None)
                if profile:
                    stats['last_updated'] = profile.get('last_updated')
        
        return stats
    
    def get_genre_summary(self) -> List[tuple]:
        """Get top genres from all data sources"""
        genre_counts = {}
        
        # Read tracks
        tracks_csv = self.data_dir / 'saved_tracks.csv'
        if tracks_csv.exists():
            with open(tracks_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    genres = row.get('genres', '')
                    if genres:
                        for genre in genres.split(', '):
                            genre = genre.strip()
                            if genre:
                                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Read albums
        albums_csv = self.data_dir / 'saved_albums.csv'
        if albums_csv.exists():
            with open(albums_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    genres = row.get('genres', '')
                    if genres:
                        for genre in genres.split(', '):
                            genre = genre.strip()
                            if genre:
                                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Read top artists
        artists_csv = self.data_dir / 'top_artists.csv'
        if artists_csv.exists():
            with open(artists_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    genres = row.get('genres', '')
                    if genres:
                        for genre in genres.split(', '):
                            genre = genre.strip()
                            if genre:
                                # Weight top artists more heavily
                                genre_counts[genre] = genre_counts.get(genre, 0) + 2
        
        # Sort by count and return top genres
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_genres[:20]  # Top 20 genres
    
    def is_data_stale(self, days=7) -> bool:
        """Check if data needs refresh"""
        profile_csv = self.data_dir / 'user_profile.csv'
        
        if not profile_csv.exists():
            return True
        
        with open(profile_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            profile = next(reader, None)
            
            if not profile or 'last_updated' not in profile:
                return True
            
            last_updated = datetime.fromisoformat(profile['last_updated'])
            age = datetime.now() - last_updated
            
            return age > timedelta(days=days)

