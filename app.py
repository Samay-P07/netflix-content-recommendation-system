"""
CineMatch Application Entry Point
Supports running directly via both:
  1) `python app.py`      (Launches browser and Streamlit server automatically)
  2) `streamlit run app.py` (Standard Streamlit & Cloud Hosting execution)
"""

import os
import sys

# Ensure repository root is on Python module search path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def is_running_in_streamlit() -> bool:
    """Checks whether the script is already running inside Streamlit's runtime."""
    try:
        from streamlit.runtime import exists
        return exists()
    except Exception:
        return False


if __name__ == "__main__":
    if not is_running_in_streamlit():
        # User executed `python app.py` from terminal!
        # Automatically launch Streamlit with browser.
        from streamlit.web import cli as stcli
        target_file = os.path.abspath(__file__)
        sys.argv = ["streamlit", "run", target_file]
        sys.exit(stcli.main())
    else:
        # Running under `streamlit run app.py` or Live Cloud Hosting
        from frontend.streamlit_app import main
        main()
