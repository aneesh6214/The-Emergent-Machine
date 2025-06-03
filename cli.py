"""Command-line interface for the Twitter agent."""
import asyncio
import click
from typing import Optional
from agent import TwitterAgent
from memory import MemoryStore
import config


@click.group()
def cli():
    """Twitter browsing agent CLI."""
    pass


@cli.command()
@click.option('--headless/--no-headless', default=True, help='Run browser in headless mode')
@click.option('--cycles', '-c', default=10, help='Maximum number of cycles to run')
@click.option('--session', '-s', default='twitter_session.pkl', help='Session file path')
@click.option('--no-vector', is_flag=True, help='Disable vector store (use simple text search)')
@click.option('--browser', '-b', default='chrome', type=click.Choice(['chromium', 'chrome', 'edge']), help='Browser type to use')
def run(headless: bool, cycles: int, session: str, no_vector: bool, browser: str):
    """Run the Twitter agent."""
    print(f"""
Twitter Agent Starting...
========================
Browser: {browser} ({'headless' if headless else 'visible'})
Max cycles: {cycles}
Vector store: {'disabled' if no_vector else 'enabled'}
Session file: {session}

Logs will be saved to: logs/
- Summary log: High-level decisions and actions
- Detailed log: Full debug information
- Error log: Any errors encountered
- Stats JSON: Real-time statistics

Press Ctrl+C to stop gracefully.
========================
""")
    
    agent = TwitterAgent(
        session_file=session,
        headless=headless,
        use_vector_store=not no_vector,
        max_cycles=cycles,
        browser_type=browser
    )
    
    asyncio.run(agent.run())
    
    print("\nAgent finished. Check the logs/ directory for detailed logs and statistics.")


@cli.command()
@click.option('--session', '-s', default='twitter_session.pkl', help='Session file to clear')
def clear_session(session: str):
    """Clear the saved browser session."""
    from pathlib import Path
    
    session_path = Path(session)
    if session_path.exists():
        session_path.unlink()
        print(f"Cleared session: {session}")
    else:
        print(f"No session found at: {session}")


@cli.command()
@click.option('--session', '-s', default='twitter_session.pkl', help='Session file path')  
@click.option('--browser', '-b', default='chrome', type=click.Choice(['chromium', 'chrome', 'edge']), help='Browser type to use')
def login(session: str, browser: str):
    """Log in to Twitter and save the session."""
    import asyncio
    from browser import TwitterBrowser
    
    async def do_login():
        print(f"Opening {browser} browser for Twitter login...")
        browser_instance = TwitterBrowser(session, headless=False, browser_type=browser)
        
        try:
            # Initialize playwright
            from playwright.async_api import async_playwright
            browser_instance.playwright = await async_playwright().start()
            
            # Launch browser with the right channel
            launch_options = {
                'headless': False,
                'args': ['--disable-blink-features=AutomationControlled']
            }
            
            if browser == 'chrome':
                launch_options['channel'] = 'chrome'
            elif browser == 'edge':
                launch_options['channel'] = 'msedge'
                
            browser_instance.browser = await browser_instance.playwright.chromium.launch(**launch_options)
            
            # Create a new context
            browser_instance.context = await browser_instance.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            browser_instance.page = await browser_instance.context.new_page()
            
            print("Browser opened. Navigating to X.com...")
            
            # Navigate to X.com
            await browser_instance.page.goto('https://x.com')
            await browser_instance.page.wait_for_timeout(2000)
            
            print("\nPlease log in to Twitter/X in the browser window.")
            print("I'll check every few seconds if you've reached the home page...")
            print("Press Ctrl+C when done to save the session.\n")
            
            # Poll for login completion
            logged_in = False
            check_count = 0
            
            while not logged_in and check_count < 60:  # Check for up to 5 minutes
                try:
                    await browser_instance.page.wait_for_timeout(5000)  # Wait 5 seconds
                    current_url = browser_instance.page.url
                    
                    # Check if we're on the home page
                    if ('x.com/home' in current_url or 'twitter.com/home' in current_url) and 'login' not in current_url:
                        logged_in = True
                        print("\n✓ Home page detected! You're logged in.")
                        print("Saving session...")
                        await browser_instance._save_session()
                        print(f"Session successfully saved at: {browser_instance.session_file}")
                        break
                    else:
                        check_count += 1
                        if check_count % 6 == 0:  # Every 30 seconds
                            print(f"Still waiting for login... (checked {check_count} times)")
                            
                except KeyboardInterrupt:
                    print("\n\nInterrupted by user. Checking current state...")
                    current_url = browser_instance.page.url
                    
                    if ('x.com' in current_url or 'twitter.com' in current_url) and 'login' not in current_url:
                        print("You appear to be logged in. Saving session...")
                        await browser_instance._save_session()
                        print(f"Session saved at: {browser_instance.session_file}")
                    else:
                        print("You don't appear to be logged in. Session not saved.")
                    break
                    
            if not logged_in and check_count >= 60:
                print("\nTimeout waiting for login. Session not saved.")
                
        except Exception as e:
            print(f"Error during login: {e}")
        finally:
            print("\nClosing browser...")
            await browser_instance.close()
            
    asyncio.run(do_login())


@cli.command()
@click.option('--session', '-s', default='twitter_session.pkl', help='Session file path')  
@click.option('--browser', '-b', default='chrome', type=click.Choice(['chromium', 'chrome', 'edge']), help='Browser type to use')
def save_session(session: str, browser: str):
    """Manually save a browser session after logging in."""
    import asyncio
    from browser import TwitterBrowser
    
    async def manual_save():
        print(f"Opening {browser} browser...")
        print("This command lets you manually save a session at any point.\n")
        
        browser_instance = TwitterBrowser(session, headless=False, browser_type=browser)
        
        try:
            # Initialize and launch browser
            from playwright.async_api import async_playwright
            browser_instance.playwright = await async_playwright().start()
            
            launch_options = {
                'headless': False,
                'args': ['--disable-blink-features=AutomationControlled']
            }
            
            if browser == 'chrome':
                launch_options['channel'] = 'chrome'
            elif browser == 'edge':
                launch_options['channel'] = 'msedge'
                
            browser_instance.browser = await browser_instance.playwright.chromium.launch(**launch_options)
            
            # Create context
            browser_instance.context = await browser_instance.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            browser_instance.page = await browser_instance.context.new_page()
            
            print("Browser opened. Please:")
            print("1. Navigate to X.com or Twitter.com")
            print("2. Log in if not already logged in")
            print("3. Press Enter here when ready to save the session...")
            
            # Go to x.com to start
            await browser_instance.page.goto('https://x.com')
            
            input()  # Wait for user to press Enter
            
            # Check current state before saving
            current_url = browser_instance.page.url
            print(f"\nCurrent URL: {current_url}")
            
            if 'x.com' in current_url or 'twitter.com' in current_url:
                # Force save the session
                await browser_instance._save_session()
                print(f"✓ Session saved to {session}")
            else:
                print("Warning: You're not on a Twitter/X page.")
                save_anyway = input("Save anyway? (y/n): ")
                if save_anyway.lower() == 'y':
                    await browser_instance._save_session()
                    print(f"Session saved to {session}")
                else:
                    print("Session not saved.")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser_instance.close()
        
    asyncio.run(manual_save())


@cli.command()
@click.option('--json-file', '-j', default='memories.json', help='JSON memory file')
@click.option('--vector-db', '-v', default='./chroma_db', help='Vector database path')
def clear_memory(json_file: str, vector_db: str):
    """Clear all stored memories."""
    click.confirm('Are you sure you want to clear all memories?', abort=True)
    
    memory_store = MemoryStore(json_file=json_file, vector_db_path=vector_db)
    memory_store.clear()
    print("All memories cleared.")


@cli.command()
@click.option('--json-file', '-j', default='memories.json', help='JSON memory file')
@click.option('--limit', '-l', default=10, help='Number of memories to show')
def show_memories(json_file: str, limit: int):
    """Show recent memories."""
    memory_store = MemoryStore(json_file=json_file, use_vector_store=False)
    
    memories = memory_store.memories[-limit:] if len(memory_store.memories) > limit else memory_store.memories
    
    if not memories:
        print("No memories found.")
        return
        
    print(f"\nShowing {len(memories)} most recent memories:\n")
    
    for i, memory in enumerate(memories, 1):
        print(f"{i}. {memory.get('timestamp', 'No timestamp')}")
        print(f"   URL: {memory.get('perception', {}).get('url', 'Unknown')}")
        print(f"   Action: {memory.get('action', {}).get('action_type', 'Unknown')}")
        print(f"   Summary: {memory.get('summary', 'No summary')}")
        print()


@cli.command()
@click.argument('query')
@click.option('--json-file', '-j', default='memories.json', help='JSON memory file')
@click.option('--vector-db', '-v', default='./chroma_db', help='Vector database path')
@click.option('--results', '-r', default=5, help='Number of results to show')
def search_memories(query: str, json_file: str, vector_db: str, results: int):
    """Search memories for a specific query."""
    memory_store = MemoryStore(json_file=json_file, vector_db_path=vector_db)
    
    async def search():
        return await memory_store.search(query, n_results=results)
        
    found = asyncio.run(search())
    
    if not found:
        print(f"No memories found for query: {query}")
        return
        
    print(f"\nFound {len(found)} memories matching '{query}':\n")
    
    for i, summary in enumerate(found, 1):
        print(f"{i}. {summary}")
        print()


@cli.command()
def install_playwright():
    """Install Playwright browsers."""
    import subprocess
    
    print("Installing Playwright browsers...")
    try:
        subprocess.run(['playwright', 'install', 'chromium'], check=True)
        print("Playwright browsers installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Playwright browsers: {e}")
        print("Try running: playwright install chromium")


@cli.command()
@click.option('--session', '-s', default='twitter_session.pkl', help='Session file path')
@click.option('--browser', '-b', default='chrome', type=click.Choice(['chromium', 'chrome', 'edge']), help='Browser type to use')
def verify_session(session: str, browser: str):
    """Verify if the saved Twitter session is still valid."""
    import asyncio
    from browser import TwitterBrowser
    from pathlib import Path
    
    async def check_session():
        session_path = Path(session)
        
        if not session_path.exists():
            print(f"❌ No session file found at: {session}")
            print("Run 'python cli.py login' to create a new session.")
            return
            
        print(f"Found session file: {session}")
        print(f"Testing with {browser} browser...")
        
        browser_instance = TwitterBrowser(session, headless=True, browser_type=browser)
        
        try:
            await browser_instance.start()
            
            # Try to navigate to home
            await browser_instance.page.goto('https://x.com/home')
            await browser_instance.page.wait_for_load_state('networkidle', timeout=10000)
            
            # Check where we ended up
            current_url = browser_instance.page.url
            
            if 'home' in current_url and 'login' not in current_url:
                print("✅ Session is valid! You're logged in.")
                
                # Get some basic info
                title = await browser_instance.page.title()
                print(f"Page title: {title}")
                
            elif 'login' in current_url or 'flow' in current_url:
                print("❌ Session is expired or invalid.")
                print("You were redirected to the login page.")
                print("Run 'python cli.py login' to create a new session.")
                
            else:
                print(f"⚠️  Unclear session status. Current URL: {current_url}")
                print("You may need to log in again.")
                
        except Exception as e:
            print(f"❌ Error checking session: {e}")
            
        finally:
            await browser_instance.close()
            
    asyncio.run(check_session())


@cli.command()
def show_config():
    """Show the current model and configuration settings."""
    config.print_model_info()
    
    print("\nTo change models:")
    print("1. Make sure you have the model: ollama pull <model-name>")
    print("2. Edit config.py and change MODEL_NAME")
    print("3. Available models in config:")
    
    for model_name, settings in config.MODEL_SETTINGS.items():
        indicator = " (CURRENT)" if model_name == config.MODEL_NAME else ""
        print(f"   - {model_name}: {settings['description']}{indicator}")
    
    print(f"\nCurrent session file: {config.DEFAULT_SESSION_FILE}")
    print(f"Current browser: {config.DEFAULT_BROWSER}")
    print(f"Vector store enabled: {config.DEFAULT_USE_VECTOR_STORE}")


@cli.command()
@click.option('--headless/--no-headless', default=True, help='Run browser in headless mode')
@click.option('--session', '-s', default='twitter_session.pkl', help='Session file path')
@click.option('--browser', '-b', default='chrome', type=click.Choice(['chromium', 'chrome', 'edge']), help='Browser type to use')
def run_overnight(headless: bool, session: str, browser: str):
    """Run the agent for an extended period (1000 cycles by default)."""
    print(f"""
Twitter Agent - Overnight Mode
==============================
This will run the agent for 1000 cycles.

Browser: {browser} ({'headless' if headless else 'visible'})
Session file: {session}

The agent will:
- Explore Twitter autonomously
- Like and bookmark interesting content
- Search for topics it finds interesting
- Build up a memory of interactions
- Log all activities to the logs/ directory

Press Ctrl+C to stop gracefully.
==============================
""")
    
    confirm = click.confirm("Ready to start the overnight run?", default=True)
    if not confirm:
        print("Cancelled.")
        return
    
    agent = TwitterAgent(
        session_file=session,
        headless=headless,
        use_vector_store=True,
        max_cycles=1000,
        browser_type=browser
    )
    
    asyncio.run(agent.run())
    
    print("\nOvernight run complete! Check the logs/ directory for a full report.")


@cli.command()
def test_llm():
    """Test the LLM with a simple prompt to check JSON parsing."""
    import asyncio
    from llm import OllamaLLM
    from logger import AgentLogger
    
    async def test():
        print("Testing LLM JSON response...")
        config.print_model_info()
        
        llm = OllamaLLM()
        logger = AgentLogger()
        
        # Simple test context
        test_context = {
            'perception': {
                'url': 'https://x.com/home',
                'title': 'Home / X',
                'text': 'TWEETS: Elon Musk posted about AI. Tech news trending.',
                'elements': [
                    {'selector': '[data-perceive-id="0"]', 'text': 'Tweet', 'ariaLabel': 'Tweet button'},
                    {'selector': '[data-perceive-id="1"]', 'text': 'Home', 'ariaLabel': 'Home'},
                ]
            },
            'memories': ['Previously scrolled through tech tweets', 'Liked a post about AI']
        }
        
        print("\nSending test prompt to LLM...")
        try:
            action = await llm.decide_action(test_context, logger=logger)
            print(f"\n✅ SUCCESS! Parsed action:")
            print(f"   Action Type: {action.get('action_type')}")
            print(f"   Reasoning: {action.get('reasoning', 'No reasoning')}")
            print(f"   Full action: {action}")
        except Exception as e:
            print(f"\n❌ FAILED: {e}")
        
        # Clean up
        logger.log_session_end("Test completed")
    
    asyncio.run(test())


if __name__ == "__main__":
    cli() 