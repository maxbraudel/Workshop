"""
Error handling module for the Cinema application.
Provides custom error pages and logging.
"""

from flask import render_template, request, jsonify
import logging

logger = logging.getLogger(__name__)

def init_error_handlers(app):
    """Initialize error handlers for the Flask app."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        logger.warning(f"404 error: {request.url}")
        
        # Return JSON for API requests
        if request.is_json or '/api/' in request.path:
            return jsonify({
                'error': 'Not Found',
                'message': 'The requested resource was not found.'
            }), 404
        
        # Return HTML for regular requests
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"500 error: {error}")
        
        # Return JSON for API requests
        if request.is_json or '/api/' in request.path:
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred. Please try again later.'
            }), 500
        
        # Return HTML for regular requests
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 errors."""
        logger.warning(f"403 error: {request.url}")
        
        # Return JSON for API requests
        if request.is_json or '/api/' in request.path:
            return jsonify({
                'error': 'Forbidden',
                'message': 'You do not have permission to access this resource.'
            }), 403
        
        # Return HTML for regular requests
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle 400 errors."""
        logger.warning(f"400 error: {request.url}")
        
        # Return JSON for API requests
        if request.is_json or '/api/' in request.path:
            return jsonify({
                'error': 'Bad Request',
                'message': 'The request was malformed or invalid.'
            }), 400
        
        # Return HTML for regular requests
        return render_template('errors/400.html'), 400
