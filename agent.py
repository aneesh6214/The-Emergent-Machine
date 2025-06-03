"""Twitter browsing agent using LangGraph."""
import asyncio
from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END
from browser import TwitterBrowser
from llm import OllamaLLM
from memory import MemoryStore
from logger import AgentLogger


class AgentState(TypedDict):
    """State passed between graph nodes."""
    browser: TwitterBrowser
    llm: OllamaLLM
    memory_store: MemoryStore
    perception: Dict[str, Any]
    memories: List[str]
    action: Dict[str, Any]
    action_result: Dict[str, Any]
    reflection: str
    cycle_count: int
    max_cycles: int
    logger: AgentLogger


class TwitterAgent:
    """Main agent orchestrating the perceive-recall-reflect-act-store cycle."""
    
    def __init__(self, 
                 session_file: str = "twitter_session.pkl",
                 headless: bool = True,
                 use_vector_store: bool = True,
                 max_cycles: int = 10,
                 browser_type: str = "chrome"):
        self.session_file = session_file
        self.headless = headless
        self.use_vector_store = use_vector_store
        self.max_cycles = max_cycles
        self.browser_type = browser_type
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("perceive", self.perceive)
        workflow.add_node("recall", self.recall)
        workflow.add_node("reflect", self.reflect)
        workflow.add_node("act", self.act)
        workflow.add_node("store", self.store)
        
        # Add edges
        workflow.set_entry_point("perceive")
        workflow.add_edge("perceive", "recall")
        workflow.add_edge("recall", "reflect")
        workflow.add_edge("reflect", "act")
        workflow.add_edge("act", "store")
        
        # Conditional edge from store
        workflow.add_conditional_edges(
            "store",
            self.should_continue,
            {
                "continue": "perceive",
                "end": END
            }
        )
        
        return workflow.compile()
        
    async def perceive(self, state: AgentState) -> AgentState:
        """Get current page state from browser."""
        state['logger'].log_cycle_start(state['cycle_count'] + 1)
        
        print("\nPerceiving page state...")
        perception = await state['browser'].perceive()
        
        # Log perception
        state['logger'].log_perception(perception)
        
        # Summarize perception for display
        url = perception['url']
        elements_count = len(perception.get('elements', []))
        text_preview = perception['text'][:200] if perception['text'] else 'No text found'
        
        print(f"URL: {url}")
        print(f"Found {elements_count} clickable elements")
        print(f"Text preview: {text_preview}...")
        
        state['perception'] = perception
        return state
        
    async def recall(self, state: AgentState) -> AgentState:
        """Retrieve relevant memories based on current perception."""
        print("\nRecalling relevant memories...")
        
        # Create query from current perception
        query = f"{state['perception']['url']} {state['perception']['text'][:500]}"
        
        # Search for relevant memories
        memories = await state['memory_store'].search(query, n_results=5)
        
        print(f"Retrieved {len(memories)} relevant memories")
        
        state['memories'] = memories
        return state
        
    async def reflect(self, state: AgentState) -> AgentState:
        """Use LLM to decide the next action."""
        print("\nReflecting on next action...")
        
        # Prepare context for LLM
        context = {
            'perception': state['perception'],
            'memories': state['memories']
        }
        
        # Get action decision from LLM
        action = await state['llm'].decide_action(context, logger=state['logger'])
        
        # Log the decision
        reasoning = action.get('reasoning', 'No reasoning provided')
        state['logger'].log_action_decision(action, reasoning)
        
        print(f"Decided action: {action['action_type']}")
        print(f"Reasoning: {reasoning}")
        
        state['action'] = action
        return state
        
    async def act(self, state: AgentState) -> AgentState:
        """Execute the chosen action."""
        print(f"\nExecuting action: {state['action']['action_type']}...")
        
        # Store perception before action
        perception_before = state['perception'].copy()
        
        # Execute action
        result = await state['browser'].act(state['action'])
        
        # Log action result
        state['logger'].log_action_result(result)
        
        if result['success']:
            print("Action executed successfully")
        else:
            print(f"Action failed: {result['error']}")
            
        # Get perception after action
        await asyncio.sleep(1)  # Brief pause to let page update
        perception_after = await state['browser'].perceive()
        
        # Generate reflection on what happened
        reflection_context = {
            'perception_before': perception_before,
            'perception_after': perception_after,
            'action': state['action'],
            'result': result
        }
        
        reflection = await state['llm'].reflect(reflection_context)
        
        # Log reflection
        state['logger'].log_reflection(reflection)
        
        state['action_result'] = result
        state['perception'] = perception_after
        state['reflection'] = reflection
        
        print(f"Reflection: {reflection}")
        
        return state
        
    async def store(self, state: AgentState) -> AgentState:
        """Store the interaction in memory."""
        print("\nStoring memory...")
        
        # Create memory entry
        memory = {
            'perception': {
                'url': state['perception']['url'],
                'title': state['perception']['title'],
                'text_preview': state['perception']['text'][:500]
            },
            'action': state['action'],
            'result': state['action_result'],
            'summary': state['reflection']
        }
        
        # Store memory
        await state['memory_store'].add(memory)
        
        # Log memory milestone if applicable
        total_memories = len(state['memory_store'].memories)
        state['logger'].log_memory_milestone(total_memories)
        
        # Increment cycle count
        state['cycle_count'] += 1
        
        # Log cycle end
        state['logger'].log_cycle_end()
        
        print(f"Memory stored. Total memories: {total_memories}")
        
        return state
        
    def should_continue(self, state: AgentState) -> str:
        """Decide whether to continue or end the agent loop."""
        if state['cycle_count'] >= state['max_cycles']:
            print(f"\nReached maximum cycles ({state['max_cycles']}). Ending.")
            state['logger'].log_session_end("Maximum cycles reached")
            return "end"
            
        # Check for session validity every 50 cycles
        if state['cycle_count'] % 50 == 0:
            print("\nPerforming session health check...")
            # You could add actual session validation here
            
        # Could add other termination conditions here
        # e.g., if a specific goal is reached
        
        return "continue"
        
    async def run(self, max_cycles: Optional[int] = None):
        """Run the agent for a specified number of cycles."""
        if max_cycles is None:
            max_cycles = self.max_cycles
            
        print(f"Starting Twitter agent (max {max_cycles} cycles)...")
        
        # Initialize logger
        logger = AgentLogger()
        
        # Initialize components
        browser = TwitterBrowser(self.session_file, self.headless, self.browser_type)
        await browser.start()
        
        try:
            # Navigate to Twitter home if session exists
            if browser.session_file.exists():
                await browser.page.goto('https://twitter.com/home')
                await browser.page.wait_for_load_state('networkidle', timeout=10000)
                
            # Initialize other components
            llm = OllamaLLM()
            memory_store = MemoryStore(use_vector_store=self.use_vector_store)
            
            # Create initial state
            initial_state: AgentState = {
                'browser': browser,
                'llm': llm,
                'memory_store': memory_store,
                'perception': {},
                'memories': [],
                'action': {},
                'action_result': {},
                'reflection': '',
                'cycle_count': 0,
                'max_cycles': max_cycles,
                'logger': logger
            }
            
            # Run the graph
            final_state = await self.graph.ainvoke(
                initial_state,
                config={"recursion_limit": max_cycles * 10}  # Increased to allow for all nodes in all cycles
            )
            
            print("\nAgent completed.")
            print(f"Final URL: {final_state['perception'].get('url', 'unknown')}")
            print(f"Total cycles: {final_state['cycle_count']}")
            
            # Log final statistics
            logger.log_session_end("Completed successfully")
            
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            logger.log_session_end("Interrupted by user")
        except Exception as e:
            print(f"\nError occurred: {e}")
            logger.log_session_end(f"Error: {str(e)}")
            raise
        finally:
            await browser.close()
            
            
async def main():
    """Test the agent."""
    agent = TwitterAgent(headless=False, max_cycles=5, browser_type="chrome")
    await agent.run()
    

if __name__ == "__main__":
    asyncio.run(main()) 