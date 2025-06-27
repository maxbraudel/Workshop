"""
Middleware for session validation and security.
"""

from functools import wraps
from flask import session, request, redirect, url_for, flash, g
from .database.database_retrieve import validate_session_token
import logging

logger = logging.getLogger(__name__)

def validate_user_session():
    """Validate the current user's session."""
    if 'session_token' in session and 'user_id' in session:
        session_data = validate_session_token(session['session_token'])
        if session_data:
            # Session is valid, store user info in g for easy access
            g.current_user = {
                'id': session_data['account_id'],
                'username': session_data['username'],
                'email': session_data['email'],
                'first_name': session_data.get('first_name'),
                'last_name': session_data.get('last_name'),
                'birthday': session_data.get('birthday')
            }
            return True
        else:
            # Session is invalid, clear it
            session.clear()
            return False
    return False

def login_required(f):
    """Decorator to require login for specific routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not validate_user_session():
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges for specific routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not validate_user_session():
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('login'))
        
        # Check if user is admin (you'll need to add this field to your database)
        # For now, we'll just check if they're logged in
        # TODO: Implement proper admin role checking
        
        return f(*args, **kwargs)
    return decorated_function

def logout_required(f):
    """Decorator to require that user is NOT logged in (for login/signup pages)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if validate_user_session():
            # User is already logged in, redirect to home
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def booking_login_required(f):
    """Decorator to require login for booking routes with specific message."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not validate_user_session():
            # Store the current booking URL as the last non-auth page for redirect after login
            from flask import request, session
            session['last_non_auth_page'] = request.url
            flash('You must be logged in to buy a ticket.', 'info')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def init_middleware(app):
    """Initialize middleware with Flask app."""
    
    @app.before_request
    def before_request():
        """Run before each request to validate session."""
        # Skip session validation for static files
        if request.endpoint and request.endpoint.startswith('static'):
            return
        
        # Validate session for all requests
        validate_user_session()
        
        # Log request for debugging (only in development)
        if app.config.get('DEBUG'):
            logger.debug(f"Request: {request.method} {request.path}")
    
    @app.context_processor
    def inject_user():
        """Inject user information into all templates."""
        user = getattr(g, 'current_user', None)
        return dict(
            is_logged_in=user is not None,
            current_user=user.get('username') if user else None,
            current_user_id=user.get('id') if user else None
        )
