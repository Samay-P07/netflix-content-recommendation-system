"""
CineMatch Application Entry Point
Delegates execution to frontend.streamlit_app for modularity.
"""

import os
import sys

# Ensure repository root is on Python module search path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from frontend.streamlit_app import *
