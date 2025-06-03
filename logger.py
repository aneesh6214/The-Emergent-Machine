"""Logging system for Twitter Agent with statistics tracking."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
import time


class AgentLogger:
    """Handles logging for the Twitter agent with multiple log levels and statistics."""
    
    def __init__(self, log_dir: str = "logs", max_log_size_mb: int = 50):
        """Initialize the logger with multiple output files."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create timestamp for this session
        self.session_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Statistics tracking
        self.stats = {
            'start_time': time.time(),
            'total_cycles': 0,
            'actions': defaultdict(int),
            'sections_visited': defaultdict(int),
            'errors': defaultdict(int),
            'likes_given': 0,
            'bookmarks_saved': 0,
            'searches_performed': 0,
            'profiles_viewed': 0,
            'avg_cycle_time': 0,
            'cycle_times': deque(maxlen=100),  # Keep last 100 cycle times
            'memory_milestones': [],
            'interesting_finds': []
        }
        
        # Setup different log files
        self._setup_loggers()
        
        self.current_cycle = 0
        
    def _setup_loggers(self):
        """Setup different loggers for different purposes."""
        # Summary logger - high-level decisions and outcomes
        self.summary_logger = self._create_logger(
            'summary',
            f'twitter_agent_{self.session_id}_summary.log',
            logging.INFO
        )
        
        # Detailed logger - all actions and responses
        self.detailed_logger = self._create_logger(
            'detailed',
            f'twitter_agent_{self.session_id}_detailed.log',
            logging.DEBUG
        )
        
        # Error logger - errors and warnings only
        self.error_logger = self._create_logger(
            'errors',
            f'twitter_agent_{self.session_id}_errors.log',
            logging.WARNING
        )
        
    def _create_logger(self, name: str, filename: str, level: int) -> logging.Logger:
        """Create a logger with rotating file handler."""
        logger = logging.getLogger(f'twitter_agent.{name}')
        logger.setLevel(level)
        
        # Create formatter
        if name == 'summary':
            formatter = logging.Formatter(
                '%(asctime)s | Cycle %(cycle)d | %(message)s',
                datefmt='%H:%M:%S'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | Cycle %(cycle)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # File handler
        handler = logging.FileHandler(self.log_dir / filename, encoding='utf-8')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
        
    def log_cycle_start(self, cycle: int):
        """Log the start of a new cycle."""
        self.current_cycle = cycle
        self.cycle_start_time = time.time()
        self.stats['total_cycles'] = cycle
        
        self.summary_logger.info(
            "Starting new exploration cycle",
            extra={'cycle': cycle}
        )
        
    def log_perception(self, perception: Dict[str, Any]):
        """Log what the agent perceives."""
        url = perception.get('url', 'unknown')
        text_preview = perception.get('text', '')[:200]
        elements_count = len(perception.get('elements', []))
        
        # Track sections
        if 'explore' in url:
            self.stats['sections_visited']['explore'] += 1
        elif 'notifications' in url:
            self.stats['sections_visited']['notifications'] += 1
        elif 'messages' in url:
            self.stats['sections_visited']['messages'] += 1
        elif '/status/' in url:
            self.stats['profiles_viewed'] += 1
        
        self.detailed_logger.debug(
            f"Perceived: {url} | {elements_count} elements | Text preview: {text_preview}...",
            extra={'cycle': self.current_cycle}
        )
        
    def log_action_decision(self, action: Dict[str, Any], reasoning: str = None):
        """Log the agent's action decision."""
        action_type = action.get('action_type', 'unknown')
        self.stats['actions'][action_type] += 1
        
        # Build action description
        desc_parts = [f"Action: {action_type}"]
        
        if action_type == 'scroll':
            desc_parts.append(f"{action.get('times', 1)} times {action.get('direction', 'down')}")
        elif action_type == 'search':
            desc_parts.append(f"Query: '{action.get('query', '')}'")
            self.stats['searches_performed'] += 1
        elif action_type == 'go_to_section':
            desc_parts.append(f"Section: {action.get('section', '')}")
        elif action_type == 'click':
            desc_parts.append(f"Element: {action.get('selector', '')}")
        elif action_type == 'type':
            desc_parts.append(f"Text: '{action.get('text', '')[:30]}...' into {action.get('selector', '')}")
        elif action_type == 'like':
            self.stats['likes_given'] += 1
        elif action_type == 'bookmark':
            self.stats['bookmarks_saved'] += 1
            
        action_desc = " | ".join(desc_parts)
        
        if reasoning:
            action_desc += f" | Reasoning: {reasoning}"
            
        self.summary_logger.info(action_desc, extra={'cycle': self.current_cycle})
        self.detailed_logger.info(
            f"Parsed Json: {json.dumps(action, indent=2)}",
            extra={'cycle': self.current_cycle}
        )
        
    def log_action_result(self, result: Dict[str, Any]):
        """Log the result of an action."""
        success = result.get('success', False)
        
        if success:
            details = result.get('details', 'Action completed')
            self.detailed_logger.debug(
                f"Action result: SUCCESS | {details}",
                extra={'cycle': self.current_cycle}
            )
        else:
            error = result.get('error', 'Unknown error')
            self.stats['errors'][error[:50]] += 1
            self.error_logger.error(
                f"Action failed: {error}",
                extra={'cycle': self.current_cycle}
            )
            
    def log_reflection(self, reflection: str):
        """Log the agent's reflection on what happened."""
        # Extract interesting finds from reflection
        if any(keyword in reflection.lower() for keyword in ['interesting', 'surprising', 'notable', 'important']):
            self.stats['interesting_finds'].append({
                'cycle': self.current_cycle,
                'reflection': reflection[:200],
                'timestamp': datetime.now().isoformat()
            })
            
        self.summary_logger.info(
            f"Reflection: {reflection[:300]}...",
            extra={'cycle': self.current_cycle}
        )
        
    def log_memory_milestone(self, total_memories: int):
        """Log memory milestones."""
        milestones = [10, 25, 50, 100, 200, 500, 1000]
        
        for milestone in milestones:
            if total_memories == milestone:
                self.stats['memory_milestones'].append({
                    'count': milestone,
                    'cycle': self.current_cycle,
                    'timestamp': datetime.now().isoformat()
                })
                self.summary_logger.info(
                    f"Memory milestone reached: {milestone} memories stored",
                    extra={'cycle': self.current_cycle}
                )
                break
                
    def log_cycle_end(self):
        """Log the end of a cycle and update statistics."""
        cycle_time = time.time() - self.cycle_start_time
        self.stats['cycle_times'].append(cycle_time)
        
        # Calculate average cycle time
        if self.stats['cycle_times']:
            self.stats['avg_cycle_time'] = sum(self.stats['cycle_times']) / len(self.stats['cycle_times'])
            
        self.detailed_logger.debug(
            f"Cycle completed in {cycle_time:.2f} seconds",
            extra={'cycle': self.current_cycle}
        )
        
        # Every 10 cycles, log statistics summary
        if self.current_cycle % 10 == 0:
            self._log_statistics_summary()
            
    def _log_statistics_summary(self):
        """Log a summary of statistics."""
        runtime = time.time() - self.stats['start_time']
        hours = runtime / 3600
        
        summary = f"""
=== Statistics Summary (Cycle {self.current_cycle}) ===
Runtime: {hours:.2f} hours
Actions taken: {sum(self.stats['actions'].values())}
Most common action: {max(self.stats['actions'].items(), key=lambda x: x[1])[0] if self.stats['actions'] else 'none'}
Likes given: {self.stats['likes_given']}
Bookmarks saved: {self.stats['bookmarks_saved']}
Searches performed: {self.stats['searches_performed']}
Average cycle time: {self.stats['avg_cycle_time']:.2f} seconds
Error rate: {sum(self.stats['errors'].values()) / max(1, self.current_cycle):.2%}
==========================================
"""
        self.summary_logger.info(summary, extra={'cycle': self.current_cycle})
        
        # Also save detailed stats to JSON
        self._save_stats_json()
        
    def _save_stats_json(self):
        """Save detailed statistics to JSON file."""
        stats_file = self.log_dir / f'twitter_agent_{self.session_id}_stats.json'
        
        # Convert defaultdicts to regular dicts for JSON serialization
        stats_copy = self.stats.copy()
        stats_copy['actions'] = dict(stats_copy['actions'])
        stats_copy['sections_visited'] = dict(stats_copy['sections_visited'])
        stats_copy['errors'] = dict(stats_copy['errors'])
        stats_copy['cycle_times'] = list(stats_copy['cycle_times'])
        stats_copy['runtime_hours'] = (time.time() - self.stats['start_time']) / 3600
        stats_copy['last_updated'] = datetime.now().isoformat()
        
        with open(stats_file, 'w') as f:
            json.dump(stats_copy, f, indent=2)
            
    def log_session_end(self, reason: str = "Completed"):
        """Log the end of the session with final statistics."""
        runtime = time.time() - self.stats['start_time']
        hours = runtime / 3600
        
        final_summary = f"""
=== Session Complete ===
Session ID: {self.session_id}
Total runtime: {hours:.2f} hours
Total cycles: {self.stats['total_cycles']}
Total actions: {sum(self.stats['actions'].values())}
Reason: {reason}

Action breakdown:
{json.dumps(dict(self.stats['actions']), indent=2)}

Interesting finds: {len(self.stats['interesting_finds'])}
Memory milestones reached: {[m['count'] for m in self.stats['memory_milestones']]}
========================
"""
        self.summary_logger.info(final_summary, extra={'cycle': self.current_cycle})
        
        # Save final statistics
        self._save_stats_json()
        
        # Close all handlers
        for logger in [self.summary_logger, self.detailed_logger, self.error_logger]:
            for handler in logger.handlers:
                handler.close()
                logger.removeHandler(handler) 