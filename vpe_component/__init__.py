import os
import streamlit.components.v1 as components

# Path to the frontend directory
_component_dir = os.path.join(os.path.dirname(__file__), "frontend")

# Declare the component
_vpe_component = components.declare_component(
    "vpe_component",
    path=_component_dir,
)

def vpe_component(ephemeralToken: str, key=None):
    """Wrapper exposed to Streamlit."""
    return _vpe_component(ephemeralToken=ephemeralToken, key=key)
