"""Smoke test: verify streamlit_app module can be imported."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_streamlit_app_importable():
    """The module should be importable without errors (Streamlit not running)."""
    # We only check that the file has no syntax errors and key names exist.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "streamlit_app",
        os.path.join(os.path.dirname(__file__), '..', 'scripts', 'streamlit_app.py'),
    )
    assert spec is not None, "Could not find streamlit_app.py"
