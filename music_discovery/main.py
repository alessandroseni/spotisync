#!/usr/bin/env python3
"""
Music Discovery Agent - AI-powered music exploration
Usage: python -m music_discovery.main
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

from music_discovery.data_manager import DataManager
from music_discovery.agent_tools import create_agent_tools
from music_discovery.music_agent import create_music_agent, run_agent_query, create_thread
from music_discovery import ui


def main():
    """Main entry point for music discovery agent"""
    
    # Load environment variables from root
    root_dir = Path(__file__).parent.parent
    load_dotenv(root_dir / '.env')
    
    # Initialize data manager
    data_manager = DataManager()
    
    # Display welcome
    stats = data_manager.get_data_stats()
    ui.display_welcome(stats)
    
    # Check if data exists and is fresh
    if not stats['data_exists'] or data_manager.is_data_stale(days=7):
        if not stats['data_exists']:
            ui.display_info("First time setup - fetching your Spotify library...")
            ui.console.print()
        else:
            ui.display_info("Your data is more than 7 days old. Refreshing...")
            ui.console.print()
        
        # Refresh data
        try:
            data_manager.setup_spotify_client()
            tracks, albums, artists = ui.display_refresh_progress(data_manager)
            ui.console.print()
            ui.display_success(f"Updated {tracks} tracks, {albums} albums, {artists} artists")
            ui.console.print()
            
            # Update stats
            stats = data_manager.get_data_stats()
        except Exception as e:
            ui.display_error(f"Failed to fetch Spotify data: {e}")
            ui.console.print("[yellow]You can try /refresh later or check your .env configuration[/yellow]")
            ui.console.print()
    
    # Initialize Spotify client if not already done
    try:
        if data_manager.sp is None:
            data_manager.setup_spotify_client()
    except Exception as e:
        ui.display_error(f"Failed to initialize Spotify client: {e}")
        sys.exit(1)
    
    # Create agent tools
    tools = create_agent_tools(data_manager.sp)
    
    # Create tools map for execution
    tools_map = {func.__name__: func for func in tools}
    
    # Initialize OpenAI agent
    try:
        ui.display_info("Initializing music discovery agent...")
        assistant, client = create_music_agent(tools)
        thread_id = create_thread(client)
        ui.display_success("Agent ready!")
        ui.console.print()
    except Exception as e:
        ui.display_error(f"Failed to initialize agent: {e}")
        ui.console.print("[yellow]Please check your OPENAI_API_KEY in .env[/yellow]")
        sys.exit(1)
    
    # Create prompt session
    session = ui.create_prompt_session()
    
    # Main interaction loop
    while True:
        try:
            # Get user input
            user_input = ui.get_user_input(session)
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith('/'):
                command = user_input.lower()
                
                if command == '/quit':
                    ui.console.print("\n[cyan]👋 Happy listening![/cyan]\n")
                    break
                
                elif command == '/help':
                    ui.display_help()
                    continue
                
                elif command == '/refresh':
                    ui.console.print()
                    try:
                        tracks, albums, artists = ui.display_refresh_progress(data_manager)
                        ui.console.print()
                        ui.display_success(f"Updated {tracks} tracks, {albums} albums, {artists} artists")
                        ui.console.print()
                    except Exception as e:
                        ui.display_error(f"Refresh failed: {e}")
                        ui.console.print()
                    continue
                
                elif command == '/stats':
                    ui.console.print()
                    stats = data_manager.get_data_stats()
                    ui.display_welcome(stats)
                    
                    # Show top genres
                    genres = data_manager.get_genre_summary()
                    ui.display_genre_stats(genres)
                    ui.console.print()
                    continue
                
                else:
                    ui.display_error(f"Unknown command: {command}")
                    ui.console.print("[dim]Type /help for available commands[/dim]")
                    ui.console.print()
                    continue
            
            # Process music query with agent
            ui.console.print()
            with ui.display_thinking_status("🎵 Discovering music for you..."):
                try:
                    response = run_agent_query(
                        assistant=assistant,
                        thread_id=thread_id,
                        client=client,
                        user_query=user_input,
                        tools_map=tools_map
                    )
                except Exception as e:
                    ui.display_error(f"Agent query failed: {e}")
                    ui.console.print()
                    continue
            
            # Display results
            ui.console.print()
            ui.display_recommendation(response)
            ui.console.print()
            
        except KeyboardInterrupt:
            ui.console.print("\n\n[cyan]👋 Happy listening![/cyan]\n")
            break
        except Exception as e:
            ui.display_error(f"Unexpected error: {e}")
            ui.console.print()
            continue


if __name__ == "__main__":
    main()

