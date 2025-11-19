import os
import streamlit.components.v1 as components

# Declare the component
_component_func = components.declare_component(
    "vpe_component",
    path=os.path.join(os.path.dirname(__file__), "index.html")
)

def vpe_component(ephemeral_token: str, key: str = None):
    """
    Calls the custom component and returns the transcript (list of messages)
    once JS calls Streamlit.setComponentValue().
    """
    return _component_func(ephemeralToken=ephemeral_token, key=key)
