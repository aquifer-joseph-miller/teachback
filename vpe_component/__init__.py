import os
import streamlit.components.v1 as components

# Directory where index.html lives
_COMPONENT_DIR = os.path.dirname(__file__)

# Declare the component once, pointing at the folder that contains index.html
_vpe_component = components.declare_component(
    "vpe_component",
    path=_COMPONENT_DIR,
)

def vpe_component(ephemeralToken: str, key: str | None = None):
    """
    Call the custom VPE component.

    Args:
        ephemeralToken: The Realtime API ephemeral token from app.py
        key: Optional Streamlit key

    Returns:
        None until JS calls Streamlit.setComponentValue(...),
        then the transcript (list of {role, content} dicts).
    """
    return _vpe_component(ephemeralToken=ephemeralToken, key=key)
