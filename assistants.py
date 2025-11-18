# assistants.py - Simplified for Mrs. Miller only

ASSISTANT_MAP = {
    "Mrs. Miller (High Value Care 04)": "asst_pWDA8oyZfpvRGWyYDoWhakj1",
}

def get_assistant_id(actor_name):
    """Get assistant ID by actor name."""
    return ASSISTANT_MAP.get(actor_name)