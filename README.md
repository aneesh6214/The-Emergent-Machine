# Twitter Browsing Agent

An autonomous agent that browses Twitter using a perceive-recall-reflect-act-store cycle, powered by LangGraph and a local Mixtral model via Ollama.

## Architecture

The agent follows a 5-node cycle:

1. **Perceive** - Captures visible text and DOM elements from Twitter
2. **Recall** - Retrieves relevant memories from past interactions
3. **Reflect** - Uses Mixtral to decide the next action
4. **Act** - Executes one action (scroll, click, navigate, or tweet)
5. **Store** - Saves the interaction to memory for future reference

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) running locally with Mixtral model
- Twitter account for initial login

## Installation

1. Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
python cli.py install-playwright
```

3. Pull the Mixtral model in Ollama:
```bash
ollama pull mixtral
```

## Usage

### First Run - Login to Twitter

On first run, use the dedicated login command:

```bash
# Recommended: Use the login command
python cli.py login --browser chrome

# This will:
# 1. Open Chrome browser
# 2. Navigate to Twitter login
# 3. Wait for you to log in
# 4. Automatically save the session when you reach the home page
```

Alternative method:
```bash
# Use real Chrome browser (recommended to avoid detection)
python cli.py run --no-headless --browser chrome

# Or use Edge if you're on Windows
python cli.py run --no-headless --browser edge
```

After logging in, the session will be saved to `twitter_session.pkl`.

### Browser Detection Issues

Twitter/X actively detects and blocks automated browsers. To avoid this:

1. **Use a real browser**: The agent now supports using your installed Chrome or Edge browser instead of Playwright's Chromium:
   ```bash
   python cli.py run --browser chrome  # Uses Google Chrome
   python cli.py run --browser edge    # Uses Microsoft Edge
   ```

2. **Install playwright-stealth**: This package is included in requirements.txt and provides additional anti-detection measures.

3. **First-time setup tips**:
   - Clear your browser cache before first login
   - Log in manually and interact naturally (scroll, click around) before letting the agent take over
   - If you get blocked, try using a different browser type

### Subsequent Runs

Once logged in, you can run the agent in headless mode:

```bash
python cli.py run --cycles 20 --browser chrome
```

### CLI Commands

- **login** - Log in to Twitter and save session (recommended for first time)
  ```bash
  python cli.py login [OPTIONS]
  
  Options:
    -s, --session TEXT           Session file path (default: twitter_session.pkl)
    -b, --browser [chromium|chrome|edge]  Browser type (default: chrome)
  ```

- **run** - Start the autonomous agent
  ```bash
  python cli.py run --cycles 20 --no-headless
  ```

- **run-overnight** - Run for extended period (500 cycles)
  ```bash
  python cli.py run-overnight --headless
  ```
  Perfect for letting the agent explore overnight while you sleep!

- **show-memories** - Display recent memories
  ```bash
  python cli.py show-memories --limit 5
  ```

- **search-memories** - Search through stored memories
  ```bash
  python cli.py search-memories "interesting tweets"
  ```

- **clear-session** - Remove saved login session
  ```bash
  python cli.py clear-session
  ```

- **clear-memory** - Clear all memories (use with caution)
  ```bash
  python cli.py clear-memory
  ```

## Project Structure

```
├── agent.py       # LangGraph orchestration with 5 nodes
├── browser.py     # Playwright helpers for Twitter interaction
├── llm.py         # Ollama/Mixtral wrapper
├── memory.py      # Memory storage (JSON + vector store)
├── cli.py         # Command-line interface
└── requirements.txt
```

## Configuration

### Ollama Settings

The agent expects Ollama to be running on `http://localhost:11434`. To use a different endpoint or model, modify `llm.py`:

```python
llm = OllamaLLM(model="your-model", base_url="http://your-host:11434/v1")
```

### Features

- **Autonomous Browsing**: The agent explores Twitter on its own, making decisions based on what it sees
- **Smart Actions**: Multiple action types with parameters (scroll multiple times, search, navigate sections)
- **Memory System**: Stores and recalls past interactions using ChromaDB vector search
- **Session Persistence**: Login once, run multiple times
- **Anti-Detection**: Uses real Chrome/Edge browsers with stealth techniques
- **LLM Decision Making**: Mixtral model via Ollama decides what to do next

### Available Actions

The agent can perform these actions:
- **scroll** - Scroll the page (1-10 times, up or down)
  - Example: `{"action_type": "scroll", "times": 5, "direction": "down"}`
- **click** - Click on tweets, profiles, or any element
  - Example: `{"action_type": "click", "selector": "[data-perceive-id='5']"}`
- **search** - Search Twitter for any topic
  - Example: `{"action_type": "search", "query": "AI news"}`
- **go_to_section** - Navigate to different Twitter sections
  - Sections: home, explore, notifications, messages, bookmarks, profile
  - Example: `{"action_type": "go_to_section", "section": "explore"}`
- **navigate** - Go to any specific URL
  - Example: `{"action_type": "navigate", "url": "https://x.com/elonmusk"}`
- **wait** - Pause for observation (1-5 seconds)
  - Example: `{"action_type": "wait", "seconds": 2}`
- **tweet** - Post tweets (use responsibly)
  - Example: `{"action_type": "tweet", "text": "Hello Twitter!"}`
- **like** - Like tweets
  - Example: `{"action_type": "like", "selector": "[data-perceive-id='3']"}`
- **bookmark** - Save tweets for later
  - Example: `{"action_type": "bookmark", "selector": "[data-perceive-id='7']"}`
- **refresh** - Refresh the current page
  - Example: `{"action_type": "refresh"}`

### Logging System

The agent now includes a comprehensive logging system that tracks:

1. **Multiple Log Files** (in `logs/` directory):
   - `summary.log` - High-level decisions and actions
   - `detailed.log` - Full debug information
   - `errors.log` - Any errors encountered
   - `stats.json` - Real-time statistics

2. **Statistics Tracked**:
   - Action counts by type
   - Sections visited
   - Likes given, bookmarks saved
   - Average cycle time
   - Error rates
   - Interesting finds

3. **Human-Readable Logs**:
   - Clean formatting with timestamps
   - Cycle numbers for easy tracking
   - Statistical summaries every 10 cycles

### Human-Like Behavior

The agent now includes human-like delays:
- Random pre-action delays (300-1500ms)
- Random post-action delays (200-1000ms)
- Variable scrolling speeds
- Natural typing speeds (50-150ms between characters)
- Irregular wait times

### Memory Storage

Memories are stored in two ways:
1. **JSON file** (`memories.json`) - Plain text storage
2. **ChromaDB** (`./chroma_db/`) - Vector embeddings for semantic search

## Troubleshooting

### Ollama Connection Error
Ensure Ollama is running:
```bash
ollama serve
```

### Login Issues
If login fails or Twitter shows "disabled on this website", try:
1. Use a real Chrome or Edge browser: `--browser chrome`
2. Clear session and try again: `python cli.py clear-session`
3. Ensure your browser is up-to-date
4. Try logging in during off-peak hours

```bash
python cli.py clear-session
python cli.py run --no-headless --browser chrome
```

### Session Expiration
Twitter/X sessions expire frequently. If you see the login page when running the agent:
1. This is normal - Twitter invalidates sessions after some time
2. Simply log in again when prompted
3. The agent will detect when you've logged in and continue
4. Consider using `--no-headless` for the first few cycles to monitor the session

To manually save a session after logging in:
```bash
python cli.py save-session --browser chrome
```

### Memory Search Not Working
The vector store requires sentence-transformers. If it fails, the agent falls back to text search.

## Notes

- The agent is designed for research and educational purposes
- Be respectful of Twitter's terms of service
- The tweet action should be used carefully
- Sessions expire after some time - you may need to re-login periodically

## Future Improvements

- Add more sophisticated goal-directed behavior
- Implement conversation threading
- Add image perception capabilities
- Support for more actions (like, retweet, follow)
- Better error recovery mechanisms 