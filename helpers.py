"""
Helper functions for formatting, display, and general utilities.
"""

import re
import numpy as np
from config import PRETTY_PRINT

def format_prompt_for_display(prompt: str) -> str:
    """Format the prompt for display, truncating memories if PRETTY_PRINT is enabled.
    
    When PRETTY_PRINT is True, memory bullet points will be truncated to 5 characters
    followed by ellipsis to make logs more readable.
    """
    if not PRETTY_PRINT:
        return prompt
        
    # Pattern to match memory bullet points in the input section
    memory_pattern = r'(• )(.+?)($|\n)'
    
    def truncate_memory(match):
        bullet = match.group(1)  # The "• " part
        memory_text = match.group(2)  # The content after the bullet
        line_end = match.group(3)  # Newline or end of string
        
        # Show exactly 5 characters as requested
        if len(memory_text) > 5:
            return f"{bullet}{memory_text[:5]}...{line_end}"
        return f"{bullet}{memory_text}{line_end}"
    
    # Only apply formatting to the Input section with bullet points
    sections = prompt.split("[Input]")
    if len(sections) > 1:
        pre_input = sections[0]
        input_and_post = "[Input]" + sections[1]
        
        # Only process bullet points in the input section
        formatted_input = re.sub(memory_pattern, truncate_memory, input_and_post)
        return pre_input + formatted_input
    
    return prompt


def strip_surrounding_quotes(text: str) -> str:
    """Remove surrounding quotes from text if present."""
    if not text:
        return text
        
    # Handle triple quotes - must check these first
    if len(text) >= 6:
        if text.startswith('"""') and text.endswith('"""'):
            return text[3:-3]
        
        if text.startswith("'''") and text.endswith("'''"):
            return text[3:-3]
    
    # Handle double quotes
    if len(text) >= 4:
        if text.startswith('""') and text.endswith('""'):
            return text[2:-2]
        
        if text.startswith("''") and text.endswith("''"):
            return text[2:-2]
        
    # Handle single quotes
    if len(text) >= 2:
        if text.startswith('"') and text.endswith('"'):
            return text[1:-1]
        
        if text.startswith("'") and text.endswith("'"):
            return text[1:-1]
        
    return text


def cosine_similarity(vec1, vec2):
    """Calculate the cosine similarity between two vectors.
    
    Returns a value between 0 and 1, where 1 means identical vectors
    and 0 means orthogonal vectors.
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
        return 0.0
        
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)) 