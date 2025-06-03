"""Playwright browser helpers for Twitter interaction."""
import json
import pickle
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import asyncio
import random

# Try to import playwright-stealth
try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    print("playwright-stealth not available, using basic anti-detection only")


class TwitterBrowser:
    """Handles browser automation for Twitter using Playwright."""
    
    def __init__(self, session_file: str = "twitter_session.pkl", headless: bool = True, browser_type: str = "chromium"):
        self.session_file = Path(session_file)
        self.headless = headless
        self.browser_type = browser_type  # chromium, chrome, or edge
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def start(self):
        """Start the browser and load or create session."""
        self.playwright = await async_playwright().start()
        
        # Launch options for better stealth
        launch_options = {
            'headless': self.headless,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--start-maximized',
            ]
        }
        
        # Try to use real Chrome or Edge if available
        if self.browser_type == "chrome":
            try:
                # Try to find Chrome installation
                launch_options['channel'] = 'chrome'
                self.browser = await self.playwright.chromium.launch(**launch_options)
                print("Using Google Chrome")
            except:
                print("Chrome not found, falling back to Chromium")
                self.browser = await self.playwright.chromium.launch(**launch_options)
        elif self.browser_type == "edge":
            try:
                # Try to find Edge installation
                launch_options['channel'] = 'msedge'
                self.browser = await self.playwright.chromium.launch(**launch_options)
                print("Using Microsoft Edge")
            except:
                print("Edge not found, falling back to Chromium")
                self.browser = await self.playwright.chromium.launch(**launch_options)
        else:
            self.browser = await self.playwright.chromium.launch(**launch_options)
            print("Using Chromium")
        
        if self.session_file.exists():
            await self._load_session()
        else:
            await self._create_session()
            
    async def _create_session(self):
        """Create new browser context and prompt for login."""
        print("No saved session found. Please log in to Twitter.")
        
        # Create context with stealth settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            screen={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            color_scheme='light',
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            java_script_enabled=True,
            accept_downloads=False,
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
        )
        
        # Add stealth scripts to context
        await self.context.add_init_script("""
            // Override the navigator.webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override plugins to look more realistic
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format", 
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    }
                ]
            });
            
            // Override permissions API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Fix chrome runtime
            if (!window.chrome) {
                window.chrome = {};
            }
            if (!window.chrome.runtime) {
                window.chrome.runtime = {};
            }
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Override platform
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
            
            // Fix WebGL Vendor
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
        """)
        
        self.page = await self.context.new_page()
        
        # Apply stealth mode if available
        if STEALTH_AVAILABLE:
            await stealth_async(self.page)
        
        # Set additional headers for the page
        await self.page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9'
        })
        
        # Navigate to Twitter login with a more natural approach
        await self.page.goto('https://twitter.com', wait_until='networkidle')
        await self.page.wait_for_timeout(2000)  # Wait a bit to look more human
        
        # Check if we need to click login
        try:
            login_button = await self.page.query_selector('a[href="/login"]')
            if login_button:
                await login_button.click()
                await self.page.wait_for_load_state('networkidle')
        except:
            pass
            
        print("Please log in to Twitter in the browser window...")
        
        # Wait for successful login (user should be redirected to home)
        try:
            # Wait for either twitter.com/home or x.com/home
            await self.page.wait_for_function(
                """() => {
                    const url = window.location.href;
                    return url.includes('twitter.com/home') || url.includes('x.com/home');
                }""",
                timeout=300000
            )
            print("Login successful! Saving session...")
        except Exception as e:
            # Fallback: if we're already on a twitter/x.com page after timeout, assume logged in
            current_url = self.page.url
            if 'twitter.com' in current_url or 'x.com' in current_url:
                print("Detected Twitter page, assuming logged in. Saving session...")
            else:
                raise Exception(f"Login timeout or failed: {e}")
        
        # Save session
        await self._save_session()
        print("Session saved successfully!")
        
    async def _load_session(self):
        """Load saved browser session."""
        with open(self.session_file, 'rb') as f:
            storage_state = pickle.load(f)
            
        self.context = await self.browser.new_context(
            storage_state=storage_state,
            viewport={'width': 1920, 'height': 1080},
            screen={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
        )
        
        # Add the same stealth scripts to loaded context
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    }
                ]
            });
            
            if (!window.chrome) {
                window.chrome = {};
            }
            if (!window.chrome.runtime) {
                window.chrome.runtime = {};
            }
        """)
        
        self.page = await self.context.new_page()
        
        # Apply stealth mode if available
        if STEALTH_AVAILABLE:
            await stealth_async(self.page)
        
    async def _save_session(self):
        """Save current browser session."""
        storage_state = await self.context.storage_state()
        with open(self.session_file, 'wb') as f:
            pickle.dump(storage_state, f)
            
    async def perceive(self) -> Dict[str, Any]:
        """Extract visible text and basic DOM structure from current page."""
        if not self.page:
            raise RuntimeError("Browser not initialized")
            
        # Get current URL
        url = self.page.url
        
        # Get page title
        title = await self.page.title()
        
        # Wait a bit for dynamic content to load
        await self.page.wait_for_timeout(1000)
        
        # Get visible text content - improved to skip style/script tags and get tweets
        text_content = await self.page.evaluate('''
            () => {
                const skipTags = ['SCRIPT', 'STYLE', 'NOSCRIPT', 'META', 'LINK'];
                
                // First, try to get tweet content specifically
                const tweets = [];
                const tweetElements = document.querySelectorAll('[data-testid="tweet"], article');
                tweetElements.forEach(tweet => {
                    const tweetText = tweet.innerText;
                    if (tweetText && tweetText.length > 10) {
                        tweets.push(tweetText.substring(0, 300) + "...");
                    }
                });
                
                if (tweets.length > 0) {
                    return "TWEETS: " + tweets.slice(0, 5).join(' ||| ');
                }
                
                // Fallback to general text extraction
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    {
                        acceptNode: (node) => {
                            const parent = node.parentElement;
                            if (!parent) return NodeFilter.FILTER_REJECT;
                            
                            // Skip style, script, etc.
                            if (skipTags.includes(parent.tagName)) {
                                return NodeFilter.FILTER_REJECT;
                            }
                            
                            const style = window.getComputedStyle(parent);
                            if (style.display === 'none' || style.visibility === 'hidden') {
                                return NodeFilter.FILTER_REJECT;
                            }
                            
                            const text = node.textContent.trim();
                            if (!text || text.length < 2) return NodeFilter.FILTER_REJECT;
                            
                            // Skip CSS-like content
                            if (text.includes('{') || text.includes('}') || text.includes(':') && text.includes(';')) {
                                return NodeFilter.FILTER_REJECT;
                            }
                            
                            return NodeFilter.FILTER_ACCEPT;
                        }
                    }
                );
                
                const texts = [];
                let node;
                while (node = walker.nextNode()) {
                    const text = node.textContent.trim();
                    if (text.length > 2 && !text.startsWith('<style>')) {
                        texts.push(text);
                    }
                }
                
                return texts.slice(0, 100).join(' ');
            }
        ''')
        
        # Get basic DOM structure with clickable elements
        dom_elements = await self.page.evaluate('''
            () => {
                const elements = [];
                const clickables = document.querySelectorAll('a, button, [role="button"], [role="link"], [data-testid*="reply"], [data-testid*="retweet"], [data-testid*="like"], [data-testid="tweet"]');
                
                clickables.forEach((el, index) => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0 && rect.top < window.innerHeight) {
                        // Try to use stable selectors
                        let selector = null;
                        
                        // Prefer data-testid as it's most stable
                        const testId = el.getAttribute('data-testid');
                        if (testId) {
                            selector = `[data-testid="${testId}"]`;
                        } else if (el.id) {
                            selector = `#${el.id}`;
                        } else if (el.getAttribute('aria-label')) {
                            const ariaLabel = el.getAttribute('aria-label').replace(/"/g, '\\"');
                            selector = `[aria-label="${ariaLabel}"]`;
                        } else {
                            // Fallback to temporary ID
                            el.setAttribute('data-perceive-id', index);
                            selector = `[data-perceive-id="${index}"]`;
                        }
                        
                        elements.push({
                            selector: selector,
                            tag: el.tagName.toLowerCase(),
                            text: el.textContent.trim().substring(0, 50),
                            href: el.href || null,
                            role: el.getAttribute('role'),
                            ariaLabel: el.getAttribute('aria-label'),
                            dataTestId: testId || null,
                            isVisible: rect.top >= 0 && rect.top < window.innerHeight
                        });
                    }
                });
                
                return elements;
            }
        ''')
        
        return {
            'url': url,
            'title': title,
            'text': text_content,
            'elements': dom_elements
        }
        
    async def act(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a browser action based on the provided action dict."""
        if not self.page:
            raise RuntimeError("Browser not initialized")
            
        action_type = action.get('action_type')
        result = {'success': False, 'error': None}
        
        # Add human-like random delay before action (300-1500ms)
        pre_action_delay = random.randint(300, 1500)
        await self.page.wait_for_timeout(pre_action_delay)
        
        try:
            if action_type == 'scroll':
                # Support parameterized scrolling
                times = action.get('times', 1)
                direction = action.get('direction', 'down')
                
                for i in range(times):
                    if direction == 'down':
                        await self.page.evaluate('window.scrollBy(0, window.innerHeight * 0.8)')
                    else:  # up
                        await self.page.evaluate('window.scrollBy(0, -window.innerHeight * 0.8)')
                    # Human-like variable pause between scrolls
                    await self.page.wait_for_timeout(random.randint(300, 800))
                    
                result['success'] = True
                result['details'] = f"Scrolled {direction} {times} times"
                
            elif action_type == 'click':
                selector = action.get('selector')
                if selector:
                    try:
                        # First try the direct selector
                        await self.page.click(selector, timeout=2000)
                        await self.page.wait_for_load_state('networkidle', timeout=3000)
                        result['success'] = True
                    except Exception as e:
                        # If direct click fails, try to find element with text
                        element_text = action.get('element_text', '')
                        if element_text and len(element_text) > 5:
                            try:
                                # Try clicking by text content
                                await self.page.click(f'text="{element_text[:30]}"', timeout=2000)
                                await self.page.wait_for_load_state('networkidle', timeout=3000)
                                result['success'] = True
                                result['details'] = "Clicked using text fallback"
                            except:
                                result['error'] = f"Element not found: {selector} (also tried text: {element_text[:30]})"
                        else:
                            result['error'] = f"Element not found: {selector}"
                else:
                    result['error'] = "No selector provided for click action"
                    
            elif action_type == 'navigate':
                url = action.get('url')
                if url:
                    await self.page.goto(url)
                    await self.page.wait_for_load_state('networkidle', timeout=10000)
                    result['success'] = True
                else:
                    result['error'] = "No URL provided for navigate action"
                    
            elif action_type == 'search':
                query = action.get('query')
                if query:
                    try:
                        # Try multiple possible search selectors
                        search_selectors = [
                            '[data-testid="SearchBox_Search_Input"]',
                            'input[placeholder*="Search"]',
                            'input[aria-label*="Search"]',
                            '[role="search"] input'
                        ]
                        
                        clicked = False
                        for search_selector in search_selectors:
                            try:
                                await self.page.click(search_selector, timeout=1500)
                                clicked = True
                                break
                            except:
                                continue
                        
                        if not clicked:
                            result['error'] = "Could not find search box"
                            return result
                            
                        await self.page.wait_for_timeout(random.randint(400, 800))
                        
                        # Clear and type search query
                        await self.page.keyboard.press('Control+A')
                        await self.page.keyboard.press('Delete')
                        await self.page.type(search_selector, query, delay=random.randint(50, 150))
                        await self.page.wait_for_timeout(random.randint(400, 800))
                        
                        # Press Enter
                        await self.page.keyboard.press('Enter')
                        await self.page.wait_for_load_state('networkidle', timeout=5000)
                        
                        result['success'] = True
                        result['details'] = f"Searched for: {query}"
                    except Exception as e:
                        result['error'] = f"Search failed: {str(e)}"
                else:
                    result['error'] = "No query provided for search action"
                    
            elif action_type == 'go_to_section':
                section = action.get('section', 'home')
                section_urls = {
                    'home': 'https://x.com/home',
                    'explore': 'https://x.com/explore',
                    'notifications': 'https://x.com/notifications',
                    'messages': 'https://x.com/messages',
                    'bookmarks': 'https://x.com/i/bookmarks',
                    'profile': 'https://x.com/profile'
                }
                
                if section in section_urls:
                    await self.page.goto(section_urls[section])
                    await self.page.wait_for_load_state('networkidle', timeout=10000)
                    result['success'] = True
                    result['details'] = f"Navigated to {section}"
                else:
                    result['error'] = f"Unknown section: {section}"
                    
            elif action_type == 'wait':
                seconds = action.get('seconds', 2)
                # Add some randomness to wait times
                actual_wait = seconds * 1000 + random.randint(-200, 200)
                await self.page.wait_for_timeout(max(500, actual_wait))
                result['success'] = True
                result['details'] = f"Waited for ~{seconds} seconds"
                    
            elif action_type == 'type':
                selector = action.get('selector')
                text = action.get('text')
                if selector and text:
                    # Clear the field first, then type
                    await self.page.fill(selector, '')
                    await self.page.wait_for_timeout(random.randint(200, 500))
                    await self.page.type(selector, text, delay=random.randint(50, 150))
                    await self.page.wait_for_timeout(random.randint(300, 700))
                    result['success'] = True
                    result['details'] = f"Typed text into {selector}: '{text[:50]}...'"
                else:
                    result['error'] = "Missing selector or text for type action"
                    
            elif action_type == 'like':
                selector = action.get('selector')
                if selector:
                    try:
                        # First click the provided selector to focus on the tweet
                        await self.page.click(selector, timeout=2000)
                        await self.page.wait_for_timeout(random.randint(300, 600))
                        
                        # Try to find and click the like button within the tweet
                        # Use the parent element to scope the search
                        parent = await self.page.query_selector(selector)
                        if parent:
                            like_button = await parent.query_selector('[data-testid="like"]')
                            if like_button:
                                await like_button.click()
                                result['success'] = True
                                result['details'] = "Liked tweet"
                            else:
                                # Maybe it's already liked
                                unlike_button = await parent.query_selector('[data-testid="unlike"]')
                                if unlike_button:
                                    result['success'] = True
                                    result['details'] = "Tweet was already liked"
                                else:
                                    result['error'] = "Could not find like button in tweet"
                        else:
                            result['error'] = "Could not find tweet element"
                    except Exception as e:
                        result['error'] = f"Failed to like: {str(e)[:100]}"
                else:
                    result['error'] = "No selector provided for like action"
                    
            elif action_type == 'bookmark':
                selector = action.get('selector')
                if selector:
                    try:
                        # First click the provided selector to focus on the tweet
                        await self.page.click(selector, timeout=2000)
                        await self.page.wait_for_timeout(random.randint(300, 600))
                        
                        # Try to find and click the bookmark button within the tweet
                        parent = await self.page.query_selector(selector)
                        if parent:
                            bookmark_button = await parent.query_selector('[data-testid="bookmark"]')
                            if bookmark_button:
                                await bookmark_button.click()
                                result['success'] = True
                                result['details'] = "Bookmarked tweet"
                            else:
                                # Maybe it's already bookmarked
                                unbookmark_button = await parent.query_selector('[data-testid="removeBookmark"]')
                                if unbookmark_button:
                                    result['success'] = True
                                    result['details'] = "Tweet was already bookmarked"
                                else:
                                    result['error'] = "Could not find bookmark button in tweet"
                        else:
                            result['error'] = "Could not find tweet element"
                    except Exception as e:
                        result['error'] = f"Failed to bookmark: {str(e)[:100]}"
                else:
                    result['error'] = "No selector provided for bookmark action"
                    
            elif action_type == 'refresh':
                await self.page.reload()
                await self.page.wait_for_load_state('networkidle', timeout=10000)
                result['success'] = True
                result['details'] = "Page refreshed"
                    
            else:
                result['error'] = f"Unknown action type: {action_type}"
                
        except Exception as e:
            result['error'] = str(e)
            
        # Add human-like random delay after action (200-1000ms)
        post_action_delay = random.randint(200, 1000)
        await self.page.wait_for_timeout(post_action_delay)
            
        return result
        
    async def close(self):
        """Close browser and cleanup."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()


async def load_session(session_file: str = "twitter_session.pkl", headless: bool = True, browser_type: str = "chrome") -> TwitterBrowser:
    """Load or create a Twitter browser session."""
    browser = TwitterBrowser(session_file, headless, browser_type)
    await browser.start()
    
    # Navigate to home if we loaded an existing session
    if browser.session_file.exists():
        # Try x.com first (Twitter's new domain)
        try:
            await browser.page.goto('https://x.com/home')
            await browser.page.wait_for_load_state('networkidle', timeout=10000)
            
            # Check if we were redirected to login
            current_url = browser.page.url
            if 'login' in current_url or 'flow' in current_url:
                print("Session expired or invalid. Please log in again.")
                # Give user time to log in manually if not headless
                if not browser.headless:
                    print("Please log in manually in the browser window...")
                    await browser.page.wait_for_function(
                        """() => {
                            const url = window.location.href;
                            return url.includes('/home') && !url.includes('login');
                        }""",
                        timeout=300000
                    )
                    print("Login detected, continuing...")
        except:
            # Fallback to twitter.com
            await browser.page.goto('https://twitter.com/home')
            await browser.page.wait_for_load_state('networkidle', timeout=10000)
        
    return browser 