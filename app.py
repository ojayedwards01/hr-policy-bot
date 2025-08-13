#!/usr/bin/env python3
"""
HR Policy Bot - Main App Entry Point
====================================

This file serves as the main entry point for deployment platforms
that expect an app.py file in the root directory.
"""

import sys
import os
from pathlib import Path
from threading import Thread

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the Flask app from the src directory
try:
    from src.api.app_with_integrations import app, initialize_bot
    print("✅ Successfully imported Flask app")
    
    # Start bot initialization in background
    print("🚀 Starting bot initialization...")
    init_thread = Thread(target=initialize_bot)
    init_thread.daemon = True
    init_thread.start()
    print("✅ Bot initialization started in background")
    
except Exception as e:
    print(f"❌ Error importing Flask app: {e}")
    # Create a simple fallback app
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def hello():
        return "HR Bot is starting up... Please wait."
    
    @app.route('/health')
    def health():
        return {"status": "starting", "message": "App is loading"}

if __name__ == "__main__":
    print("🚀 Starting HR Bot server...")
    app.run(host="0.0.0.0", port=8080, debug=False) 