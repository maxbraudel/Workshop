"""
Session management service for the Cinema application.
Handles session cleanup and background tasks.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from .config import get_config
from .database.database_modify import cleanup_expired_sessions

# Get configuration
config = get_config()

# Configure logging
logger = logging.getLogger(__name__)

class SessionManager:
    """Manages user sessions and background cleanup tasks."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.cleanup_interval_hours = config.SESSION_CLEANUP_INTERVAL_HOURS
        
    def start_background_tasks(self):
        """Start background tasks for session management."""
        try:
            # Schedule session cleanup
            self.scheduler.add_job(
                func=self._cleanup_expired_sessions,
                trigger=IntervalTrigger(hours=self.cleanup_interval_hours),
                id='session_cleanup',
                name='Clean up expired sessions',
                replace_existing=True
            )
            
            # Start the scheduler
            self.scheduler.start()
            logger.info(f"Session cleanup scheduled every {self.cleanup_interval_hours} hours")
            
        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")
    
    def stop_background_tasks(self):
        """Stop background tasks."""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Background tasks stopped")
        except Exception as e:
            logger.error(f"Error stopping background tasks: {e}")
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        try:
            logger.info("Starting session cleanup...")
            result = cleanup_expired_sessions()
            if result:
                logger.info("Session cleanup completed successfully")
            else:
                logger.warning("Session cleanup failed")
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
    
    def force_cleanup(self):
        """Force immediate cleanup of expired sessions."""
        self._cleanup_expired_sessions()

# Global session manager instance
session_manager = SessionManager()

def init_session_manager(app):
    """Initialize session manager with Flask app."""
    try:
        session_manager.start_background_tasks()
        
        # Register cleanup on app teardown
        @app.teardown_appcontext
        def shutdown_session_manager(exception=None):
            if exception:
                logger.error(f"App context teardown with exception: {exception}")
        
        # Register cleanup on app shutdown
        def cleanup():
            session_manager.stop_background_tasks()
        
        import atexit
        atexit.register(cleanup)
        
        logger.info("Session manager initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize session manager: {e}")

def get_session_manager():
    """Get the global session manager instance."""
    return session_manager
