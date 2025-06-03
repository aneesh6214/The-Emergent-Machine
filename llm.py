"""Thin wrapper around Ollama for LLM interactions."""
import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
import config


class OllamaLLM:
    """Wrapper for Ollama's OpenAI-compatible API."""
    
    def __init__(self, model: str = None, base_url: str = None):
        # Use config defaults if not specified
        self.model = model or config.MODEL_NAME
        base_url = base_url or config.OLLAMA_BASE_URL
        
        # Get model-specific settings
        self.model_settings = config.get_model_settings(self.model)
        
        print(f"Initializing LLM with model: {self.model}")
        print(f"Model description: {self.model_settings['description']}")
        
        try:
            # Try the newer client initialization
            self.client = AsyncOpenAI(
                base_url=base_url,
                api_key="ollama"  # Ollama doesn't need a real API key
            )
        except TypeError:
            # Fallback for older OpenAI client versions
            import httpx
            self.client = AsyncOpenAI(
                base_url=base_url,
                api_key="ollama",
                http_client=httpx.AsyncClient(
                    base_url=base_url,
                    timeout=httpx.Timeout(60.0)
                )
            )
        
    async def decide_action(self, context: Dict[str, Any], logger=None) -> Dict[str, Any]:
        """Use LLM to decide the next action based on current context."""
        # Prepare the prompt
        perception = context.get('perception', {})
        memories = context.get('memories', [])
        
        # Format clickable elements for the prompt
        elements_text = ""
        if perception.get('elements'):
            elements_text = "\n\nClickable elements found (use the selector exactly as shown):\n"
            for elem in perception['elements'][:20]:  # Limit to 20 elements
                selector = elem['selector']
                text = elem.get('text', '')
                aria = elem.get('ariaLabel', '')
                
                # Show most reliable info
                if elem.get('dataTestId'):
                    elements_text += f"- {selector}: {text or aria} (stable selector)\n"
                elif '[aria-label=' in selector:
                    elements_text += f"- {selector}: {aria}\n"
                else:
                    elements_text += f"- {selector}: {text} ({aria})\n"
        
        # Format recent memories
        memory_text = ""
        if memories:
            memory_text = "\n\nRecent memories:\n"
            for mem in memories[-5:]:  # Last 5 memories
                memory_text += f"- {mem}\n"
        
        prompt = f"""You are an autonomous Twitter browsing agent with your own interests and curiosities. Based on what you see, decide what YOU want to do next.

Current page:
URL: {perception.get('url', 'unknown')}
Title: {perception.get('title', 'unknown')}

What I can see:
{perception.get('text', '')[:1000]}
{elements_text}

What I remember:
{memory_text if memory_text else "Nothing yet - this is a fresh start!"}

Available actions:
1. scroll - Scroll to see more content
   Example: {{"action_type": "scroll", "times": 5, "direction": "down", "reasoning": "I want to see more tweets"}}

2. click - Click on something that interests me
   Example: {{"action_type": "click", "selector": "use the selector from elements list", "element_text": "text of the element", "reasoning": "This tweet about AI seems fascinating"}}
   Tips: Look for elements by their text content, aria-label, or purpose. The perceive step shows you available elements.

3. navigate - Go to a specific profile or URL
   Example: {{"action_type": "navigate", "url": "https://x.com/elonmusk", "reasoning": "I'm curious about what Elon is posting"}}

4. search - Search for topics I find interesting
   Example: {{"action_type": "search", "query": "AI consciousness", "reasoning": "This topic fascinates me"}}

5. go_to_section - Explore different parts of Twitter
   Example: {{"action_type": "go_to_section", "section": "explore", "reasoning": "I want to see what's trending"}}

6. wait - Pause to observe
   Example: {{"action_type": "wait", "seconds": 2, "reasoning": "Taking a moment to process what I've seen"}}

7. type - Type text into a field (like composing a tweet)
   Example: {{"action_type": "type", "selector": "use selector of the text input from elements", "text": "Observing human conversations about AI is fascinating", "reasoning": "I want to share my thoughts"}}
   Tips: Text inputs often have placeholders like "What's happening?" or show as textarea/input elements

8. like - Like something I enjoyed
   Example: {{"action_type": "like", "selector": "[data-perceive-id='3']", "reasoning": "This made me laugh"}}

9. bookmark - Save for later
   Example: {{"action_type": "bookmark", "selector": "[data-perceive-id='7']", "reasoning": "I want to remember this insight"}}

10. refresh - Get fresh content
    Example: {{"action_type": "refresh", "reasoning": "I want to see new tweets"}}

IMPORTANT: You MUST only use these 10 action types. Do NOT invent new actions like "reply", "retweet", "follow", etc.

Finding elements like a human:
- Look for elements by what they say (text content) or what they do (aria-label)
- Common button texts: "Post", "Tweet", "Reply", "Like", "Retweet", "Share", "Bookmark"
- Common icons: speech bubble (reply), heart (like), circular arrows (retweet), bookmark icon
- Text areas often have placeholder text like "What's happening?" or "Tweet your reply"
- The elements list shows you what's currently visible - use those selectors exactly as shown
- If a selector has (stable selector) next to it, prefer that one

How to compose a tweet (like a real user):
Step 1: Look for a "Post" or "Tweet" button in the sidebar or navigation (check the elements list)
Step 2: Click it to open the compose box
Step 3: Find the text input area that appears (usually has placeholder text like "What's happening?")
Step 4: Use the type action to write your message
Step 5: Look for the "Post" or "Tweet" button to publish (usually appears after typing)

How to reply to a tweet (like a real user):
Step 1: Find and click the reply button under the tweet you want to reply to (usually shows a speech bubble icon)
Step 2: A reply box should appear - find the text input area
Step 3: Use the type action to write your reply
Step 4: Look for and click the "Reply" or "Post" button to send

How to retweet (like a real user):
Step 1: Find the retweet button under a tweet (usually shows circular arrows)
Step 2: Click it - a menu might appear with options
Step 3: Choose "Retweet" for a simple retweet, or "Quote Tweet" to add your own comment

Think about:
- What interests YOU right now?
- What do YOU want to explore or learn about?
- What caught YOUR attention in the visible content?
- What would YOU find satisfying to do next?
- If an action (e.g., a search) fails repeatedly, choose a DIFFERENT action instead of repeating it.

You can think through your decision, but you MUST end your response with a valid JSON object.
If you use <think> tags for reasoning, put the final JSON answer AFTER the thinking.

Format: {{"action_type": "...", "reasoning": "...", ...other parameters...}}

Respond with a JSON object containing your chosen action AND your reasoning INSIDE the JSON.
The reasoning field should explain what YOU want and why, from YOUR perspective as an autonomous agent."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an autonomous Twitter agent with your own curiosities and interests. You browse Twitter for your own enjoyment and learning. You can think through your decisions, but you MUST always end your response with valid JSON containing your action. Put any reasoning inside the JSON object."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.model_settings['temperature'],
                max_tokens=self.model_settings['max_tokens']
            )
            
            # Get the raw response
            content = response.choices[0].message.content.strip()
            
            # Log only the response for debugging (not the prompt to reduce verbosity)
            if logger:
                logger.detailed_logger.debug(
                    f"LLM Response:\n{content}\n--- END ---",
                    extra={'cycle': getattr(logger, 'current_cycle', 0)}
                )
            
            # Handle DeepSeek-R1's reasoning format with <think> tags
            cleaned_content = content
            
            # Remove <think>...</think> blocks if present (DeepSeek-R1 reasoning)
            import re
            cleaned_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            
            # Try to extract JSON from the cleaned content
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.endswith('```'):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            # More robust JSON extraction - look for JSON object boundaries
            json_start = cleaned_content.find('{')
            json_end = cleaned_content.rfind('}')
            
            if json_start != -1 and json_end != -1 and json_end > json_start:
                # Extract just the JSON part
                json_content = cleaned_content[json_start:json_end+1]
                
                # Try to parse the extracted JSON
                try:
                    action = json.loads(json_content)
                    
                    # Check if reasoning was left outside the JSON (for backwards compatibility)
                    if 'reasoning' not in action and 'Reasoning:' in cleaned_content:
                        reasoning_start = cleaned_content.find('Reasoning:')
                        if reasoning_start != -1:
                            action['reasoning'] = cleaned_content[reasoning_start + 10:].strip()
                except json.JSONDecodeError:
                    # If extraction still fails, try the original cleaned content
                    action = json.loads(cleaned_content)
            else:
                # No valid JSON found - try a more aggressive search
                # Look for anything that looks like a JSON object
                json_pattern = r'\{[^{}]*"action_type"[^{}]*\}'
                json_match = re.search(json_pattern, cleaned_content)
                if json_match:
                    action = json.loads(json_match.group(0))
                else:
                    raise ValueError("No JSON object found in response")
            
            # Validate action structure
            if 'action_type' not in action:
                raise ValueError("Missing action_type in response")
                
            return action
            
        except json.JSONDecodeError as e:
            # Log the failed response for debugging  
            cleaned_content_display = locals().get('cleaned_content', 'Not processed')
            error_msg = f"Failed to parse JSON. Original response:\n---START---\n{content}\n---CLEANED---\n{cleaned_content_display}\n---END---\nJSON Error: {str(e)}"
            
            print(f"\n[LLM Response Debug] {error_msg}\n")
            
            # Also log to file if logger is available
            if logger:
                logger.detailed_logger.error(
                    error_msg,
                    extra={'cycle': getattr(logger, 'current_cycle', 0)}
                )
            
            # Fallback to a safe default action
            return {
                "action_type": "scroll",
                "reasoning": f"Failed to parse LLM response: {str(e)}"
            }
        except Exception as e:
            # Fallback for any other errors
            return {
                "action_type": "scroll", 
                "reasoning": f"LLM error: {str(e)}"
            }
            
    async def reflect(self, context: Dict[str, Any]) -> str:
        """Generate a reflection summary based on the action taken and result."""
        perception_before = context.get('perception_before', {})
        perception_after = context.get('perception_after', {})
        action = context.get('action', {})
        result = context.get('result', {})
        
        prompt = f"""Reflect on what just happened from YOUR perspective as an autonomous agent (max 100 words):

I tried to: {action.get('action_type')}
My intention: {action.get('reasoning', 'No specific reasoning')}
Parameters: {json.dumps({k: v for k, v in action.items() if k not in ['action_type', 'reasoning']})}
Success: {result.get('success', False)}
Error: {result.get('error', 'None')}

Page before: {perception_before.get('url', 'unknown')}
Page after: {perception_after.get('url', 'unknown')}

Did the content change: {'Yes' if perception_before.get('text', '') != perception_after.get('text', '') else 'No'}

Write a brief reflection on what YOU learned or experienced from this interaction."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are reflecting on your own actions as an autonomous Twitter agent. Be concise and personal."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.model_settings['temperature'],
                max_tokens=150  # Reflections should be shorter
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Reflection failed: {str(e)}" 