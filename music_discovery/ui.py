#!/usr/bin/env python3
"""
UI - Interactive terminal interface using rich and prompt_toolkit
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.status import Status
from rich.progress import Progress
from rich.markdown import Markdown
from rich.text import Text
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from pathlib import Path
from datetime import datetime
import re


# Enable hyperlink support for clickable URLs
console = Console(legacy_windows=False)


def display_welcome(stats):
    """Show welcome panel with library stats"""
    console.print("\n")
    console.print("🎵🤖 [bold cyan]Music Discovery Agent[/bold cyan]", justify="center")
    console.print("\n")
    
    if stats['data_exists']:
        # Create stats table
        table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        table.add_column("Label", style="dim")
        table.add_column("Value", style="bold cyan")
        
        table.add_row("Tracks", str(stats['tracks']))
        table.add_row("Albums", str(stats['albums']))
        table.add_row("Artists", str(stats['artists']))
        
        # Format last updated
        if stats['last_updated']:
            try:
                updated = datetime.fromisoformat(stats['last_updated'])
                now = datetime.now()
                delta = now - updated
                
                if delta.days > 0:
                    time_str = f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
                elif delta.seconds // 3600 > 0:
                    hours = delta.seconds // 3600
                    time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
                else:
                    minutes = delta.seconds // 60
                    time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                
                table.add_row("Last Updated", time_str)
            except:
                table.add_row("Last Updated", "Unknown")
        
        panel = Panel(
            table,
            title="[bold]Your Music Library[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(panel)
    else:
        console.print("[yellow]⚠️  No data found. Use /refresh to fetch your Spotify library.[/yellow]")
    
    console.print("\n[dim]Commands: /refresh /stats /help /quit[/dim]\n")


def display_genre_stats(genres):
    """Display top genres in a table"""
    if not genres:
        console.print("[yellow]No genre data available[/yellow]")
        return
    
    table = Table(title="🎸 Top Genres", box=box.ROUNDED)
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Genre", style="bold")
    table.add_column("Count", justify="right", style="green")
    
    for i, (genre, count) in enumerate(genres[:15], 1):
        table.add_row(str(i), genre, str(count))
    
    console.print(table)


def display_thinking_status(message="Analyzing your taste..."):
    """Show thinking animation"""
    return Status(message, spinner="dots")


def display_recommendation(rec_text):
    """Display agent recommendation response with markdown rendering and clickable links"""
    # Convert markdown links to include both clickable links and visible URLs
    # Pattern: [text](url) -> clickable link + URL shown
    def replace_link(match):
        text = match.group(1)
        url = match.group(2)
        # Return markdown link followed by the raw URL for terminals without clickable link support
        return f"[{text}]({url})\n  🔗 `{url}`"
    
    # Process the text to add visible URLs after links
    processed_text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, rec_text)
    
    # Render as markdown for rich formatting
    markdown = Markdown(processed_text)
    
    panel = Panel(
        markdown,
        title="[bold green]🎵 Recommendations[/bold green]",
        border_style="green",
        padding=(1, 2),
        expand=False
    )
    console.print(panel)


def display_error(message):
    """Display error message"""
    console.print(f"[bold red]❌ Error:[/bold red] {message}")


def display_info(message):
    """Display info message"""
    console.print(f"[cyan]ℹ️  {message}[/cyan]")


def display_success(message):
    """Display success message"""
    console.print(f"[bold green]✓[/bold green] {message}")


def display_markdown(text, title=None, border_style="cyan"):
    """Display markdown-formatted text in a panel"""
    markdown = Markdown(text)
    panel = Panel(
        markdown,
        title=title,
        border_style=border_style,
        padding=(1, 2),
        expand=False
    )
    console.print(panel)


def display_help():
    """Display help information"""
    help_text = """# Music Discovery Agent - Help

## How to use:
Just type what you're looking for! Examples:
- "Latin American Rock"
- "Indie music like Radiohead"
- "Chill electronic vibes"
- "Artists similar to Gustavo Cerati"

## Commands:
- `/refresh` - Update your Spotify library data
- `/stats` - Show detailed library statistics
- `/help` - Show this help message
- `/quit` - Exit the application

## Tips:
- The agent analyzes your music taste automatically
- Each query may give different results for variety
- Be specific or vague - both work!
- Spotify links are provided for all recommendations
"""
    display_markdown(help_text, border_style="cyan")


def get_user_input(session):
    """Get input with command completion"""
    try:
        text = session.prompt("🎧 > ")
        return text.strip()
    except KeyboardInterrupt:
        return "/quit"
    except EOFError:
        return "/quit"


def create_prompt_session():
    """Create prompt session with history and completion"""
    history_file = Path(__file__).parent / '.history'
    
    # Define commands for auto-completion
    commands = ['/refresh', '/stats', '/help', '/quit']
    completer = WordCompleter(commands, ignore_case=True)
    
    session = PromptSession(
        history=FileHistory(str(history_file)),
        completer=completer,
        complete_while_typing=False
    )
    
    return session


def display_refresh_progress(data_manager):
    """Display progress during data refresh"""
    with Progress() as progress:
        task = progress.add_task("[cyan]Refreshing Spotify data...", total=4)
        
        # Fetch user profile
        progress.update(task, advance=1, description="[cyan]Fetching user profile...")
        data_manager.fetch_and_store_user_profile()
        
        # Fetch tracks
        progress.update(task, advance=1, description="[cyan]Fetching saved tracks...")
        tracks = data_manager.fetch_and_store_tracks()
        
        # Fetch albums
        progress.update(task, advance=1, description="[cyan]Fetching saved albums...")
        albums = data_manager.fetch_and_store_albums()
        
        # Fetch top artists
        progress.update(task, advance=1, description="[cyan]Fetching top artists...")
        artists = data_manager.fetch_and_store_top_artists()
        
        progress.update(task, completed=4)
    
    return tracks, albums, artists

