#!/usr/bin/env python3
"""
Online Learning Portal – Web Application Server
Starts the FastAPI application with Uvicorn.

Usage:
    python run_app.py
"""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import uvicorn

def main():
    print("=" * 60)
    print("  Online Learning Portal – Hybrid NoSQL Web Application")
    print("  Backend: MongoDB 7.x + Neo4j 5.x")
    print("  Server:  http://127.0.0.1:8000")
    print("  API Docs: http://127.0.0.1:8000/docs")
    print("=" * 60)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")

if __name__ == "__main__":
    main()
