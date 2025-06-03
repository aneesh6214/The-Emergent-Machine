# Twitter Agent Architecture

## Overview

The Twitter browsing agent is built using LangGraph to orchestrate a 5-node cycle that mimics human browsing behavior.

## Core Components

### 1. Browser Automation (`browser.py`)
- Uses Playwright for browser control
- Supports Chrome, Edge, and Chromium
- Session persistence via pickle
- Anti-detection measures (stealth mode, user agent spoofing)

### 2. LLM Decision Making (`llm.py`)
- Uses Ollama with Mixtral model
- Decides next action based on page state and memories
- Generates reflections on action outcomes

### 3. Memory System (`memory.py`)
- Dual storage: JSON file + ChromaDB vector store
- Stores perceptions, actions, and reflections
- Semantic search for relevant memories

### 4. Agent Orchestration (`agent.py`)
- LangGraph state machine with 5 nodes
- Manages the perception-action cycle
- Handles state passing between nodes

### 5. CLI Interface (`cli.py`)
- Commands: run, login, save-session, verify-session
- Configuration options for browser type, cycles, etc.

## The 5-Node Cycle

```
┌─────────────┐
│  PERCEIVE   │ ← Extract page content & clickable elements
└──────┬──────┘
       ↓
┌─────────────┐
│   RECALL    │ ← Retrieve relevant memories
└──────┬──────┘
       ↓
┌─────────────┐
│  REFLECT    │ ← LLM decides next action
└──────┬──────┘
       ↓
┌─────────────┐
│    ACT      │ ← Execute browser action
└──────┬──────┘
       ↓
┌─────────────┐
│   STORE     │ ← Save interaction to memory
└──────┬──────┘
       ↓
   [REPEAT or END]
```

## Available Actions

1. **scroll** - Parameterized scrolling (1-10 times, up/down)
2. **click** - Click on specific elements via CSS selector
3. **navigate** - Go to any URL
4. **search** - Search Twitter for topics
5. **go_to_section** - Navigate to Twitter sections (home, explore, etc.)
6. **wait** - Pause for observation
7. **tweet** - Post content (use sparingly)

## State Management

The `AgentState` TypedDict contains:
- `browser`: TwitterBrowser instance
- `llm`: OllamaLLM instance
- `memory_store`: MemoryStore instance
- `perception`: Current page state
- `memories`: Retrieved relevant memories
- `action`: Chosen action
- `action_result`: Execution result
- `reflection`: LLM's summary of what happened
- `cycle_count`: Current cycle number
- `max_cycles`: Maximum allowed cycles

## Configuration

Key configuration points:
- Browser type (Chrome recommended for anti-detection)
- Headless mode (False for debugging)
- Vector store usage (True for semantic search)
- Max cycles (controls how long agent runs)
- Recursion limit (must be > cycles * nodes)

## Memory Schema

Each memory contains:
```json
{
  "timestamp": "ISO datetime",
  "perception": {
    "url": "current page URL",
    "title": "page title",
    "text_preview": "first 500 chars of visible text"
  },
  "action": {
    "action_type": "chosen action",
    "...": "action parameters"
  },
  "result": {
    "success": true/false,
    "error": "error message if failed"
  },
  "summary": "LLM reflection on what happened"
}
``` 