"""
Logging configuration for the Cinema application.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from .config import get_config

def init_logging(app):
    """Initialize logging for the Flask application."""
    config = get_config()
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure logging level based on environment
    if config.DEBUG:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Configure app logger
    app.logger.setLevel(log_level)
    
    # Remove default handlers
    app.logger.handlers.clear()
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    app.logger.addHandler(console_handler)
    
    # Add file handler for production
    if not config.DEBUG:
        file_handler = RotatingFileHandler(
            'logs/cinema.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(detailed_formatter)
        app.logger.addHandler(file_handler)
        
        # Log application startup
        app.logger.info('Cinema application startup')
    
    # Configure other loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    return app.logger
