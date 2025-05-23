# recent_perception.py
# Module to track the most recent perception from the bot.

_recent_perception = None


def set_recent_perception(perception: str):
    """Set the most recent perception."""
    global _recent_perception
    _recent_perception = perception


def get_recent_perception() -> str:
    """Get the most recent perception."""
    return _recent_perception 