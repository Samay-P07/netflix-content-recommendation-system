"""
CineMatch Application Entry Point
Launches the high-performance, lightweight CineMatch web discovery platform.
Execution: `python app.py`
"""

import os
import sys
import time
import threading
import webbrowser
import uvicorn

# Ensure repository root is on Python module search path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def open_browser_tab(url: str, delay: float = 1.2):
    """Opens the user's default browser once the server is listening."""
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main():
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    url = f"http://{host}:{port}"

    print("=" * 65)
    print("🎬  CINEMATCH — AI-POWERED MOVIE & TV DISCOVERY PLATFORM")
    print(f"🚀  Running on: {url}")
    print("✨  High-Performance Asynchronous Web Application")
    print("=" * 65)

    # Launch browser automatically on localhost
    if host in ["127.0.0.1", "localhost"]:
        threading.Thread(target=open_browser_tab, args=(url,), daemon=True).start()

    uvicorn.run("backend.main:app", host=host, port=port, log_level="info", reload=False)


if __name__ == "__main__":
    main()
