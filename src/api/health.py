"""
Health endpoint module for Docker container health checks
"""

from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)

@health_bp.route('/', methods=['GET'])
def health_check():
    """Simple health check endpoint that returns OK if the server is running"""
    return jsonify({
        "status": "ok", 
        "message": "HR Bot server is running"
    }), 200
