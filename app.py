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
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    url = f"http://127.0.0.1:{port}"

    print("=" * 65)
    print("🎬  CINEMATCH — AI-POWERED MOVIE & TV DISCOVERY PLATFORM")
    print(f"🚀  Running on: {url} (Interface: {host}:{port})")
    print("✨  High-Performance Asynchronous Web Application")
    print("=" * 65)

    # Launch browser automatically only on local interactive machines (not in Cloud/Docker/CI)
    is_cloud = any(os.getenv(k) for k in ["RENDER", "RAILWAY_ENVIRONMENT", "DYNO", "CI", "FLY_APP_NAME"])
    if not is_cloud:
        threading.Thread(target=open_browser_tab, args=(url,), daemon=True).start()

    uvicorn.run("backend.main:app", host=host, port=port, log_level="info", reload=False)


if __name__ == "__main__":
    main()
