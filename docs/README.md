# Twitter Agent Documentation

## Quick Links

- [Architecture Overview](ARCHITECTURE.md) - System design and components
- [Changelog](CHANGELOG.md) - Version history and updates
- [Main README](../README.md) - Setup and usage instructions

## Project Overview

This is an autonomous Twitter browsing agent that uses:
- **LangGraph** for orchestrating a 5-node perception-action cycle
- **Playwright** for browser automation
- **Ollama/Mixtral** for decision making
- **ChromaDB** for semantic memory search

## Key Features

1. **Autonomous Browsing** - The agent explores Twitter on its own
2. **Memory System** - Remembers past interactions and learns
3. **Session Persistence** - Saves login state between runs
4. **Anti-Detection** - Uses real browsers to avoid blocks
5. **Diverse Actions** - Can scroll, click, search, navigate sections
6. **CLI Interface** - Easy command-line control

## Current Capabilities

The agent can:
- Browse the Twitter feed
- Search for topics
- Navigate to different sections (Explore, Notifications, etc.)
- Click on tweets and profiles
- Remember what it has seen
- Make decisions based on past experiences

## Future Directions

- Goal-directed behavior (e.g., "find tweets about AI")
- Conversation threading (follow reply chains)
- Better content understanding
- More sophisticated memory retrieval
- Multi-modal perception (images, videos) 