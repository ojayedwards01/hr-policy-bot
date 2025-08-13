import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.getcwd())

# Import the Flask app
from src.api.app_with_integrations import app

# Gunicorn configuration
bind = "0.0.0.0:8080"
workers = 2
timeout = 300
worker_class = "sync" 