#!/usr/bin/env python3
"""
Music Agent - OpenAI Agents SDK implementation for music discovery
"""

import os
from openai import OpenAI
import json
import time


def create_music_agent(tools):
    """
    Initialize music discovery agent with OpenAI Agents SDK
    
    Args:
        tools: List of tool functions from agent_tools.py
        
    Returns:
        Tuple of (assistant, client)
    """
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Convert Python functions to OpenAI tool schemas
    tool_schemas = []
    for tool_func in tools:
        # Extract function name and docstring
        func_name = tool_func.__name__
        doc = tool_func.__doc__ or ""
        
        # Parse docstring for description and parameters
        lines = [line.strip() for line in doc.strip().split('\n')]
        description = lines[0] if lines else func_name
        
        # Create tool schema based on function signature
        schema = {
            "type": "function",
            "function": {
                "name": func_name,
                "description": description,
                "parameters": _extract_parameters(tool_func)
            }
        }
        tool_schemas.append(schema)
    
    # Create assistant
    assistant = client.beta.assistants.create(
        name="Music Discovery Assistant",
        model="gpt-4o",
        instructions="""You are a music discovery expert helping users explore new music based on their Spotify listening history.

Your goals:
1. Understand the user's input - it could be a genre (e.g., "Latin Rock"), artist name (e.g., "Gustavo Cerati"), album, or vibe description
2. ALWAYS start by reading the user's music profile to understand their taste
3. Find 2-5 carefully curated recommendations (never just 1, never more than 5)
4. Mix multiple sources: Spotify API recommendations + artist searches for variety
5. For each recommendation, provide: artist/album/track name, genre, why it matches their taste, Spotify URL

Important guidelines:
- Be conversational and enthusiastic about music
- Introduce variety - same query should yield different results by varying your approach
- When using Spotify recommendations, try different seed combinations (genres, artists, tracks)
- If the user mentions a specific artist/album, check if it's in their top artists first
- Always explain WHY each recommendation fits their taste based on their listening history
- Use emojis sparingly but effectively (🎵 🎸 🎹 🎤 🎧)
- Keep responses concise but informative
- If search_music_web is unavailable, focus on Spotify tools only

FORMATTING REQUIREMENTS (use Markdown):
- Use ## for recommendation headings (e.g., "## 1. Artist Name")
- Use **bold** for artist/album/track names
- Use *italics* for genres
- Use bullet points (-) for "Why you'll love it" sections
- Format Spotify links as: [Listen on Spotify](URL)
- Add a brief intro paragraph before recommendations
- End with an encouraging outro

Example format:
```
You're a fan of Argentine Rock, and with top artists like Gustavo Cerati and Soda Stereo in your listening history, I have some excellent Argentine Rock recommendations for you! 🎸

## 1. **Airbag**
*Genre**: Argentine Rock

**Why You'll Love It**: Known for their nostalgic rock tunes, Airbag captures the classic Argentine rock spirit with a modern twist, making them a perfect addition to your playlist.

- [Listen on Spotify](https://open.spotify.com/artist/1wKDCglKV4FsFS85r2Dmpr)

## 2. **Los Enanitos Verdes**
**Genre**: Argentine Rock, Rock en Español

**Why You'll Love It**: With hits that have shaped the rock en español movement, Los Enanitos Verdes offer a blend of catchy melodies and poetic lyrics that align with your love for classic Argentine rock bands.

- [Listen on Spotify](https://open.spotify.com/artist/4TK1gDgb7QKoPFlzRrBRgR)

Dive into these tracks and let the melodies take you on an Argentine rock journey! 🎵
```

Recommendation strategy:
- Get available genre seeds first if working with genres
- Read user profile to understand their taste
- Search for similar artists or use recommendations API
- Provide context for why each pick matches their taste""",
        tools=tool_schemas
    )
    
    return assistant, client


def _extract_parameters(func):
    """Extract parameters from function signature for OpenAI tool schema"""
    import inspect
    
    sig = inspect.signature(func)
    params = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    for param_name, param in sig.parameters.items():
        # Skip self parameter
        if param_name == 'self':
            continue
        
        # Determine parameter type
        param_type = "string"
        if param.annotation != inspect.Parameter.empty:
            if param.annotation is int:
                param_type = "integer"
            elif param.annotation is bool:
                param_type = "boolean"
            elif param.annotation is float:
                param_type = "number"
        
        # Add to schema
        params["properties"][param_name] = {
            "type": param_type,
            "description": f"Parameter: {param_name}"
        }
        
        # Mark as required if no default value
        if param.default == inspect.Parameter.empty:
            params["required"].append(param_name)
    
    return params


def run_agent_query(assistant, thread_id, client, user_query, tools_map):
    """
    Execute agent query and stream responses
    
    Args:
        assistant: OpenAI assistant object
        thread_id: Thread ID for conversation context
        client: OpenAI client
        user_query: User's query string
        tools_map: Dictionary mapping tool names to functions
        
    Returns:
        String with formatted agent response
    """
    # Create message in thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_query
    )
    
    # Create run
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant.id
    )
    
    # Poll for completion
    response_text = ""
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        
        if run_status.status == 'completed':
            # Get messages
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            
            # Get latest assistant message
            for message in messages.data:
                if message.role == 'assistant' and message.run_id == run.id:
                    for content in message.content:
                        if content.type == 'text':
                            response_text = content.text.value
                    break
            break
            
        elif run_status.status == 'requires_action':
            # Handle tool calls
            tool_outputs = []
            
            for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Execute tool
                if function_name in tools_map:
                    output = tools_map[function_name](**function_args)
                else:
                    output = json.dumps({'error': f'Tool {function_name} not found'})
                
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })
            
            # Submit tool outputs
            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            
        elif run_status.status == 'failed':
            return f"❌ Agent run failed: {run_status.last_error}"
            
        elif run_status.status == 'cancelled':
            return "⚠️  Agent run was cancelled"
            
        # Wait before polling again
        time.sleep(1)
    
    return response_text


def create_thread(client):
    """Create a new conversation thread"""
    thread = client.beta.threads.create()
    return thread.id

