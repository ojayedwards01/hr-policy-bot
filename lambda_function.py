import json
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.getcwd())

# Import Flask app and bot
from src.api.app_with_integrations import app, initialize_bot

# Initialize bot globally (will be reused across invocations)
def initialize_bot_once():
    """Initialize bot once and reuse across Lambda invocations"""
    try:
        initialize_bot()
        return True
    except Exception as e:
        print(f"Bot initialization failed: {e}")
        return False

# Initialize bot on cold start
bot_initialized = initialize_bot_once()

def lambda_handler(event, context):
    """
    AWS Lambda handler function
    Handles API Gateway events and routes to Flask app
    """
    try:
        # Parse the API Gateway event
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        headers = event.get('headers', {})
        query_string_parameters = event.get('queryStringParameters', {})
        body = event.get('body', '')
        
        # Convert API Gateway event to Flask request format
        from flask import Request
        from werkzeug.test import EnvironBuilder
        
        # Build environment for Flask
        environ = EnvironBuilder(
            method=http_method,
            path=path,
            headers=headers,
            query_string=query_string_parameters,
            input_stream=body if body else None
        ).get_environ()
        
        # Create Flask request
        with app.request_context(environ):
            # Process the request through Flask
            response = app.full_dispatch_request()
            
            # Convert Flask response to API Gateway format
            return {
                'statusCode': response.status_code,
                'headers': dict(response.headers),
                'body': response.get_data(as_text=True)
            }
            
    except Exception as e:
        print(f"Lambda handler error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }

# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'httpMethod': 'GET',
        'path': '/api/status',
        'headers': {},
        'queryStringParameters': {}
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))

