#!/usr/bin/env python3
"""
HR Policy Bot Launcher
======================

This script properly sets up the Python path and launches the application.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import and run the application
if __name__ == "__main__":
    from src.api.app_with_integrations import app, initialize_bot
    from threading import Thread
    import logging
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Start bot initialization in background
    init_thread = Thread(target=initialize_bot)
    init_thread.daemon = True
    init_thread.start()
    
    # Start Flask app
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Starting HR Policy Bot server on port {port}")
    logger.info(f"📱 Web interface: http://localhost:{port}")
    logger.info(f"📊 API status: http://localhost:{port}/api/status")
    
    try:
        app.run(host="0.0.0.0", port=port, debug=False)
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
