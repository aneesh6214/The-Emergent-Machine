"""Configuration settings for the Twitter Agent."""

# ===== LLM Configuration =====
# Available models (make sure to `ollama pull` them first):
# - "deepseek-r1:7b"     - Best reasoning, fast on RTX 4070 (recommended)
# - "deepseek-r1:32b"    - Even better reasoning, slower (uses RAM + GPU)
# - "qwq:32b"            - Alternative reasoning model
# - "phi4:14b"           - Microsoft's latest
# - "mixtral:8x7b"       - Original model (not recommended)

MODEL_NAME = "deepseek-r1:7b"
OLLAMA_BASE_URL = "http://localhost:11434/v1"

# ===== Agent Configuration =====
DEFAULT_MAX_CYCLES = 10
DEFAULT_HEADLESS = True
DEFAULT_BROWSER = "chrome"  # chrome, edge, or chromium

# ===== Memory Configuration =====
DEFAULT_USE_VECTOR_STORE = True
MEMORY_JSON_FILE = "memories.json"
VECTOR_DB_PATH = "./chroma_db"

# ===== Session Configuration =====
DEFAULT_SESSION_FILE = "twitter_session.pkl"

# ===== Logging Configuration =====
LOG_DIRECTORY = "logs"
MAX_LOG_SIZE_MB = 50

# ===== Model-Specific Settings =====
MODEL_SETTINGS = {
    "deepseek-r1:7b": {
        "temperature": 0.7,
        "max_tokens": 8000,
        "description": "Fast reasoning model, runs entirely on RTX 4070"
    },
    "deepseek-r1:32b": {
        "temperature": 0.7,
        "max_tokens": 250,
        "description": "Better reasoning, slower, uses RAM + GPU"
    },
    "qwq:32b": {
        "temperature": 0.7,
        "max_tokens": 200,
        "description": "Alternative reasoning model from Qwen"
    },
    "phi4:14b": {
        "temperature": 0.7,
        "max_tokens": 200,
        "description": "Microsoft's latest instruction-following model"
    },
    "mixtral:8x7b": {
        "temperature": 0.7,
        "max_tokens": 200,
        "description": "Original model (not recommended)"
    }
}

def get_model_settings(model_name: str = None) -> dict:
    """Get settings for the specified model."""
    if model_name is None:
        model_name = MODEL_NAME
    
    return MODEL_SETTINGS.get(model_name, {
        "temperature": 0.7,
        "max_tokens": 200,
        "description": "Unknown model"
    })

def print_model_info():
    """Print information about the current model."""
    settings = get_model_settings()
    print(f"""
Current Model Configuration:
===========================
Model: {MODEL_NAME}
Description: {settings['description']}
Temperature: {settings['temperature']}
Max Tokens: {settings['max_tokens']}
Ollama URL: {OLLAMA_BASE_URL}
===========================
""") 