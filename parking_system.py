"""
Smart Parking Management System - Primary Entry Point
"""

from run import open_browser
import uvicorn
import threading

if __name__ == "__main__":
    print("=" * 70)
    print("[*] SMART PARKING MANAGEMENT SYSTEM USING DATA STRUCTURES & ALGORITHMS")
    print("=" * 70)
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, log_level="info")
