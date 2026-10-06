"""
Launcher Script for Smart Parking Management System
Runs uvicorn dev server on port 8000 and opens default web browser.
"""

import sys
import webbrowser
import time
import threading
import uvicorn

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    print("=" * 70)
    print("[*] SMART PARKING MANAGEMENT SYSTEM (DSA MINI-PROJECT)")
    print("=" * 70)
    print("Starting Web Server at http://127.0.0.1:8000 ...")
    print("Press Ctrl+C to stop the server.")
    print("=" * 70)

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")
