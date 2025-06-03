# Twitter Agent Changelog

## [0.2.0] - 2025-05-31

### Added
- Parameterized scrolling action (scroll 1-10 times, up or down)
- New actions: search, go_to_section, wait
- Section navigation (explore, notifications, messages, bookmarks, profile)
- Architecture documentation
- Improved tweet content extraction (filters out CSS)

### Fixed
- Recursion limit increased from 5x to 10x cycles
- CSP errors in login command by removing JavaScript evaluation
- Session saving now works with polling instead of wait_for_function

### Changed
- Updated LLM prompt with clearer action examples
- Better action variety guidance for the model
- Scroll action now supports multiple scrolls in one action

## [0.1.0] - 2025-05-30

### Added
- Initial Twitter browsing agent with LangGraph
- 5-node cycle: Perceive → Recall → Reflect → Act → Store
- Browser automation with Playwright
- Session persistence for Twitter login
- Memory storage with ChromaDB vector search
- CLI commands: run, login, save-session, verify-session
- Anti-detection measures for browser automation

### Current Issues
- Agent gets stuck in repetitive scrolling loops
- Limited action variety (only scroll, click, navigate, tweet)
- Small scroll increments (0.8 * window height)
- Recursion limit errors from LangGraph
- LLM not exploring Twitter features effectively

### Planned Improvements
- [x] Add parameterized scrolling (scroll multiple times)
- [x] Add more diverse actions (search, explore, notifications, messages)
- [x] Fix recursion limit configuration
- [ ] Improve action selection logic
- [ ] Add goal-directed behavior
- [x] Better content extraction from tweets 