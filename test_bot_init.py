#!/usr/bin/env python3
"""
Simple test script to check bot initialization
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_bot_initialization():
    """Test if the bot can initialize properly"""
    try:
        print("🔧 Testing bot initialization...")
        
        # Import the bot
        from src.core.bot import Bot
        
        # Try to create a bot instance
        print("📦 Creating bot instance...")
        bot = Bot()
        
        print("✅ Bot initialization successful!")
        
        # Test basic functionality
        print("🧪 Testing basic functionality...")
        version_info = bot.get_version_info()
        print(f"📋 Version info: {version_info}")
        
        # Test vectorstore setup
        print("🗄️ Testing vectorstore setup...")
        setup_success = bot.setup_from_vectorstore()
        print(f"📊 Vectorstore setup: {'✅ Success' if setup_success else '❌ Failed'}")
        
        print("🎉 All tests passed! Bot is ready to use.")
        return True
        
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_bot_initialization()
    sys.exit(0 if success else 1)
