#!/usr/bin/env python3
"""
Agent Tools - OpenAI agent tool definitions for music discovery
"""

import csv
from pathlib import Path
import json


def create_agent_tools(spotify_client):
    """Create tool definitions for OpenAI agent"""
    
    sp = spotify_client
    data_dir = Path(__file__).parent / 'data'
    
    def search_spotify_artist(query: str) -> str:
        """
        Search Spotify for artists by name or genre keywords.
        
        Args:
            query: Artist name or genre keywords to search for
            
        Returns:
            JSON string with artist results including name, genres, popularity, and Spotify URL
        """
        try:
            results = sp.search(q=query, type='artist', limit=10)
            
            artists = []
            for artist in results['artists']['items']:
                artists.append({
                    'name': artist['name'],
                    'genres': artist.get('genres', []),
                    'popularity': artist.get('popularity', 0),
                    'spotify_url': artist['external_urls']['spotify'],
                    'artist_id': artist['id']
                })
            
            return json.dumps({
                'query': query,
                'results': artists,
                'count': len(artists)
            }, indent=2)
            
        except Exception as e:
            return json.dumps({'error': f'Search failed: {str(e)}'})
    
    def get_spotify_recommendations(
        seed_genres: str = "",
        seed_artists: str = "",
        seed_tracks: str = "",
        limit: int = 5
    ) -> str:
        """
        Get Spotify recommendations based on seed genres, artists, or tracks.
        Up to 5 seeds total combined across all parameters.
        
        Args:
            seed_genres: Comma-separated genre seeds (e.g., "rock,indie")
            seed_artists: Comma-separated artist IDs
            seed_tracks: Comma-separated track IDs
            limit: Number of recommendations (default 5, max 20)
            
        Returns:
            JSON string with track recommendations including name, artists, album, and Spotify URL
        """
        try:
            # Parse seeds
            genres = [g.strip() for g in seed_genres.split(',') if g.strip()]
            artists = [a.strip() for a in seed_artists.split(',') if a.strip()]
            tracks = [t.strip() for t in seed_tracks.split(',') if t.strip()]
            
            # Validate total seeds
            total_seeds = len(genres) + len(artists) + len(tracks)
            if total_seeds == 0:
                return json.dumps({'error': 'At least one seed is required'})
            if total_seeds > 5:
                return json.dumps({'error': 'Maximum 5 seeds total allowed'})
            
            # Get recommendations
            results = sp.recommendations(
                seed_genres=genres if genres else None,
                seed_artists=artists if artists else None,
                seed_tracks=tracks if tracks else None,
                limit=min(limit, 20)
            )
            
            recommendations = []
            for track in results['tracks']:
                recommendations.append({
                    'name': track['name'],
                    'artists': [a['name'] for a in track['artists']],
                    'album': track['album']['name'],
                    'spotify_url': track['external_urls']['spotify'],
                    'track_id': track['id'],
                    'preview_url': track.get('preview_url')
                })
            
            return json.dumps({
                'seeds': {
                    'genres': genres,
                    'artists': artists,
                    'tracks': tracks
                },
                'recommendations': recommendations,
                'count': len(recommendations)
            }, indent=2)
            
        except Exception as e:
            return json.dumps({'error': f'Recommendations failed: {str(e)}'})
    
    def get_available_genre_seeds() -> str:
        """
        Get the complete list of genre seeds available for Spotify recommendations.
        
        Returns:
            JSON string with list of valid genre seed strings
        """
        try:
            genres = sp.recommendation_genre_seeds()
            
            return json.dumps({
                'genres': genres['genres'],
                'count': len(genres['genres'])
            }, indent=2)
            
        except Exception as e:
            return json.dumps({'error': f'Failed to fetch genre seeds: {str(e)}'})
    
    def search_music_web(query: str) -> str:
        """
        Search the web for music recommendations, similar artists, and genre exploration.
        Uses web search to find recommendations beyond Spotify's API.
        
        Args:
            query: Search query (e.g., "Latin Rock music recommendations 2025")
            
        Returns:
            Summary of web search results with artist/album mentions and sources
        """
        # Note: This would integrate with Brave Search MCP in production
        # For now, return a helpful message about the limitation
        return json.dumps({
            'note': 'Web search integration requires Brave Search MCP setup',
            'query': query,
            'suggestion': 'Focus on Spotify API tools for now (search_spotify_artist, get_spotify_recommendations)'
        }, indent=2)
    
    def read_user_music_profile() -> str:
        """
        Access user's Spotify library summary including top genres, favorite artists, and recent additions.
        This provides context about the user's music taste for making personalized recommendations.
        
        Returns:
            JSON string with formatted summary of user's music library
        """
        try:
            profile = {
                'total_tracks': 0,
                'total_albums': 0,
                'total_artists': 0,
                'top_genres': [],
                'top_artists_short_term': [],
                'top_artists_medium_term': [],
                'top_artists_long_term': [],
                'recent_tracks': []
            }
            
            # Read tracks
            tracks_csv = data_dir / 'saved_tracks.csv'
            if tracks_csv.exists():
                with open(tracks_csv, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    tracks = list(reader)
                    profile['total_tracks'] = len(tracks)
                    
                    # Get recent tracks (last 10)
                    for track in tracks[:10]:
                        profile['recent_tracks'].append({
                            'name': track['name'],
                            'artists': track['artists'],
                            'added_at': track['added_at']
                        })
            
            # Read albums
            albums_csv = data_dir / 'saved_albums.csv'
            if albums_csv.exists():
                with open(albums_csv, 'r', encoding='utf-8') as f:
                    profile['total_albums'] = sum(1 for _ in csv.reader(f)) - 1
            
            # Read top artists
            artists_csv = data_dir / 'top_artists.csv'
            if artists_csv.exists():
                with open(artists_csv, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        artist_data = {
                            'name': row['name'],
                            'genres': row['genres'].split(', ') if row['genres'] else [],
                            'popularity': int(row['popularity']) if row['popularity'] else 0,
                            'artist_id': row['artist_id']
                        }
                        
                        if row['time_range'] == 'short_term':
                            profile['top_artists_short_term'].append(artist_data)
                        elif row['time_range'] == 'medium_term':
                            profile['top_artists_medium_term'].append(artist_data)
                        elif row['time_range'] == 'long_term':
                            profile['top_artists_long_term'].append(artist_data)
            
            # Count unique artists
            profile['total_artists'] = len(set(
                [a['name'] for a in profile['top_artists_short_term']] +
                [a['name'] for a in profile['top_artists_medium_term']] +
                [a['name'] for a in profile['top_artists_long_term']]
            ))
            
            # Aggregate genres
            genre_counts = {}
            for artist_list in [profile['top_artists_short_term'], 
                               profile['top_artists_medium_term'],
                               profile['top_artists_long_term']]:
                for artist in artist_list:
                    for genre in artist['genres']:
                        if genre:
                            genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            # Sort genres by count
            sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
            profile['top_genres'] = [{'genre': g[0], 'count': g[1]} for g in sorted_genres[:10]]
            
            # Limit artist lists to top 10 for readability
            profile['top_artists_short_term'] = profile['top_artists_short_term'][:10]
            profile['top_artists_medium_term'] = profile['top_artists_medium_term'][:10]
            profile['top_artists_long_term'] = profile['top_artists_long_term'][:10]
            
            return json.dumps(profile, indent=2)
            
        except Exception as e:
            return json.dumps({'error': f'Failed to read user profile: {str(e)}'})
    
    # Return list of tool functions
    return [
        search_spotify_artist,
        get_spotify_recommendations,
        get_available_genre_seeds,
        search_music_web,
        read_user_music_profile
    ]

