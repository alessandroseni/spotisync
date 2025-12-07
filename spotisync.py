#!/usr/bin/env python3
"""
Spotisync - Sync Spotify liked songs to a public playlist
"""

import os
import sys
import base64
from datetime import datetime
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth


class Spotisync:
    def __init__(self):
        """Initialize Spotisync with environment variables"""
        load_dotenv()
        
        # Load configuration from environment
        self.client_id = os.getenv('SPOTIPY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
        self.playlist_id = os.getenv('PLAYLIST_ID')
        self.cover_image_path = os.getenv('COVER_IMAGE_PATH', 'assets/Jazz Drummer 2.jpeg')
        
        # Validate required environment variables
        if not all([self.client_id, self.client_secret, self.redirect_uri, self.playlist_id]):
            print("❌ Error: Missing required environment variables!")
            print("Please check your .env file and ensure PLAYLIST_ID is set.")
            sys.exit(1)
        
        # Set up Spotify client with proper scopes
        scope = "user-library-read playlist-modify-public playlist-modify-private ugc-image-upload"
        
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=scope
        ))
        
        # Get current user info automatically
        user_info = self.sp.current_user()
        self.username = user_info['id']
        
        print(f"🎵 Spotisync initialized for user: {self.username}")

    def get_all_liked_songs(self):
        """Fetch all liked songs from Spotify"""
        print("📥 Fetching all liked songs...")
        
        liked_songs = []
        offset = 0
        limit = 50
        
        while True:
            results = self.sp.current_user_saved_tracks(limit=limit, offset=offset)
            items = results['items']
            
            if not items:
                break
                
            liked_songs.extend(items)
            offset += limit
            print(f"   Retrieved {len(liked_songs)} songs so far...")
        
        print(f"✅ Found {len(liked_songs)} liked songs")
        return liked_songs

    def get_playlist(self):
        """Get the specified playlist"""
        print(f"🎯 Using playlist ID: {self.playlist_id}")
        try:
            playlist = self.sp.playlist(self.playlist_id)
            print(f"✅ Found playlist: '{playlist['name']}'")
            return self.playlist_id
        except Exception as e:
            print(f"❌ Error accessing playlist {self.playlist_id}: {e}")
            sys.exit(1)

    def clear_playlist(self, playlist_id):
        """Remove all tracks from the playlist"""
        print("🧹 Clearing existing tracks from playlist...")
        
        # Get ALL current tracks using pagination
        all_track_uris = []
        offset = 0
        limit = 100
        
        while True:  # Loop through all pages
            tracks = self.sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
            track_uris = [item['track']['uri'] for item in tracks['items'] if item['track']]
            
            if not track_uris:  # No more tracks
                break
                
            all_track_uris.extend(track_uris)
            offset += limit
            print(f"   Found {len(all_track_uris)} tracks to remove so far...")
        
        if not all_track_uris:
            print("   Playlist is already empty")
            return
        
        print(f"   Total tracks to remove: {len(all_track_uris)}")
        
        # Remove tracks in batches (Spotify API limit is 100 per request)
        batch_size = 100
        removed_count = 0
        for i in range(0, len(all_track_uris), batch_size):
            batch = all_track_uris[i:i + batch_size]
            self.sp.playlist_remove_all_occurrences_of_items(playlist_id, batch)
            removed_count += len(batch)
            print(f"   Removed batch {i//batch_size + 1} ({removed_count}/{len(all_track_uris)} tracks)")
        
        print(f"✅ Removed ALL {len(all_track_uris)} tracks from playlist")

    def add_tracks_to_playlist(self, playlist_id, liked_songs):
        """Add tracks to playlist with newest first"""
        print("➕ Adding liked songs to playlist (newest first)...")
        
        # Extract track URIs (already in newest first order from Spotify API)
        track_uris = []
        for item in liked_songs:  # Remove reversed() to keep newest first
            if item['track'] and item['track']['uri']:
                track_uris.append(item['track']['uri'])
        
        if not track_uris:
            print("   No valid tracks to add")
            return
        
        # Add tracks in batches (Spotify API limit is 100 per request)
        batch_size = 100
        added_count = 0
        
        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i:i + batch_size]
            self.sp.playlist_add_items(playlist_id, batch)
            added_count += len(batch)
            print(f"   Added batch {i//batch_size + 1} ({added_count}/{len(track_uris)} tracks)")
        
        print(f"✅ Successfully added {added_count} tracks to playlist")

    def update_playlist_description(self, playlist_id):
        """Update playlist description with current timestamp"""
        print("📝 Updating playlist description...")
        
        # Format timestamp as "Nov 26, 2025 at 2:30 PM"
        timestamp = datetime.now().strftime("%b %d, %Y at %-I:%M %p")
        description = f"Last updated: {timestamp}"
        
        try:
            self.sp.playlist_change_details(
                playlist_id,
                description=description
            )
            print(f"✅ Updated description: {description}")
        except Exception as e:
            print(f"⚠️  Warning: Could not update description: {e}")

    def upload_cover_image(self, playlist_id):
        """Upload custom cover image to the playlist"""
        print("🖼️  Uploading playlist cover image...")
        
        # Resolve path relative to script location
        if not os.path.isabs(self.cover_image_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(script_dir, self.cover_image_path)
        else:
            image_path = self.cover_image_path
        
        if not os.path.exists(image_path):
            print(f"⚠️  Warning: Cover image not found at {image_path}")
            return
        
        # Check file size (max 256 KB)
        file_size = os.path.getsize(image_path)
        if file_size > 256 * 1024:
            print(f"⚠️  Warning: Image too large ({file_size // 1024} KB). Max is 256 KB.")
            return
        
        try:
            with open(image_path, 'rb') as image_file:
                image_b64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            self.sp.playlist_upload_cover_image(playlist_id, image_b64)
            print(f"✅ Uploaded cover image: {os.path.basename(image_path)}")
        except Exception as e:
            print(f"⚠️  Warning: Could not upload cover image: {e}")

    def run(self):
        """Main execution method"""
        print("🚀 Starting Spotisync...")
        
        try:
            # Step 1: Get all liked songs
            liked_songs = self.get_all_liked_songs()
            
            if not liked_songs:
                print("⚠️  No liked songs found!")
                return
            
            # Step 2: Get playlist
            playlist_id = self.get_playlist()
            
            # Step 3: Clear existing tracks
            self.clear_playlist(playlist_id)
            
            # Step 4: Add liked songs (newest first)
            self.add_tracks_to_playlist(playlist_id, liked_songs)
            
            # Step 5: Update playlist description with timestamp
            self.update_playlist_description(playlist_id)
            
            # Step 6: Upload cover image
            self.upload_cover_image(playlist_id)
            
            print("🎉 Spotisync completed successfully!")
            print(f"   Playlist now contains {len(liked_songs)} tracks")
            print("   Most recent tracks are at the top 🔝")
            
        except Exception as e:
            print(f"❌ Error during sync: {e}")
            sys.exit(1)


def main():
    """Entry point"""
    spotisync = Spotisync()
    spotisync.run()


if __name__ == "__main__":
    main() 