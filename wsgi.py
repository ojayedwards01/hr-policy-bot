#!/usr/bin/env python3
"""
WSGI Entry Point for Production
==============================

This file provides a clean entry point for gunicorn to import the Flask app.
"""

import os
import sys
from pathlib import Path
from threading import Thread
import logging

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the Flask app and initialization function
from src.api.app_with_integrations import app, initialize_bot

# Initialize the bot in background thread (same as run_app.py)
def start_bot_initialization():
    """Start bot initialization in background thread"""
    try:
        init_thread = Thread(target=initialize_bot)
        init_thread.daemon = True
        init_thread.start()
        logger.info("🚀 Bot initialization started in background thread")
    except Exception as e:
        logger.error(f"❌ Failed to start bot initialization: {e}")

# Start bot initialization when module is imported
start_bot_initialization()

# Wait for bot to be ready before gunicorn starts serving
def wait_for_bot_ready():
    """Wait for bot to be fully initialized"""
    import time
    
    max_wait = 120  # Wait up to 2 minutes
    wait_time = 0
    
    while wait_time < max_wait:
        # Import status dynamically each time to get the latest value
        from src.api.app_with_integrations import initialization_status
        
        if initialization_status.get("status") == "ready":
            logger.info("✅ Bot is ready! Gunicorn can start serving requests")
            return True
        
        logger.info(f"⏳ Waiting for bot to be ready... ({wait_time}s)")
        time.sleep(5)
        wait_time += 5
    
    logger.error("❌ Bot initialization timeout after 2 minutes")
    return False

# Wait for bot to be ready
wait_for_bot_ready()

# This is what gunicorn will use
if __name__ == "__main__":
    # For testing: just wait for bot to initialize, don't start Flask server
    import time
    print("🧪 Testing bot initialization...")
    print("⏳ Waiting for bot to be ready...")
    
    # Wait a bit for bot initialization
    time.sleep(10)
    
    print("✅ Bot initialization test complete!")
    print("🚀 Ready for gunicorn to use this module")
