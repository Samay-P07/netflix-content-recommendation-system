"""
Vercel Serverless Function Entry Point for CineMatch
Exports the FastAPI ASGI application for @vercel/python runtime.
"""

import os
import sys

# Ensure root directory is on Python search path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

# Vercel looks for 'app' by default
