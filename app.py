from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from src.config import get_config
from src.session_manager import init_session_manager
from src.middleware import init_middleware, login_required, logout_required
from src.error_handlers import init_error_handlers
from src.logging_config import init_logging
from src.database import (
    test_database_connection,
    authenticate_user,
    create_session_token,
    invalidate_session_token,
    validate_session_token,
    get_all_movies,
    get_movies_with_showings,
    get_movies_with_showings_by_date,
    get_user_by_id,
    add_account,
    modify_account_profile,
    modify_account_password,
    validate_signup_data,
    validate_signup_identifiers,
    validate_signup_passwords,
    validate_login_data
)

# Get configuration
config = get_config()

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['DEBUG'] = config.DEBUG

# Initialize components
init_logging(app)
init_middleware(app)
init_session_manager(app)
init_error_handlers(app)

# Test database connection
test_database_connection()

@app.route('/')
def index():
    # Store this page as the last non-auth page
    session['last_non_auth_page'] = url_for('index')
    return render_template('index.html', storeUrl=True)

@app.route('/movies')
def movies():
    # Store this page as the last non-auth page
    session['last_non_auth_page'] = url_for('movies')
    
    # Check if this is an AJAX request for a specific date
    selected_date = request.args.get('date')
    
    # Get movies with their showings from the database
    try:
        if selected_date:
            # Get movies for specific date
            movies_list = get_movies_with_showings_by_date(selected_date)
        else:
            # Get movies for today by default
            from datetime import date
            today = date.today().isoformat()
            movies_list = get_movies_with_showings_by_date(today)
            
        if movies_list is None:  # Database error occurred
            flash('Server unavailable, please try again later.', 'error')
            movies_list = []  # Show empty list instead of crashing
    except Exception as e:
        flash('Server unavailable, please try again later.', 'error')
        print(f"Movies page error: {e}")  # Log for debugging
        movies_list = []
    
    # If this is an AJAX request, return JSON
    if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'movies': movies_list})
    
    return render_template('movies.html', movies=movies_list, storeUrl=True)

@app.route('/login', methods=['GET', 'POST'])
@logout_required
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Validate login credentials using the new function
        try:
            login_result = validate_login_data(email, password)
            
            if login_result['success']:
                # Login successful - create session token and store in database
                user = login_result['user']
                ip_address = request.remote_addr
                user_agent = request.headers.get('User-Agent')
                session_token = create_session_token(user['id'], ip_address, user_agent)
                
                if session_token:
                    # Store session info in Flask session
                    session['logged_in'] = True
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['session_token'] = session_token
                    
                    # Show success message
                    flash('Login successful! Welcome back, ' + user['username'] + '!', 'success')
                    
                    # Smart redirect: use stored non-auth page or default to home
                    redirect_url = session.get('last_non_auth_page', url_for('index'))
                    return redirect(redirect_url)
                else:
                    flash('Server unavailable, please try again later.', 'error')
            else:
                # Show the specific error message
                flash(login_result['error'], 'error')
        except Exception as e:
            # Unexpected error
            flash('Server unavailable, please try again later.', 'error')
            print(f"Login error: {e}")  # Log for debugging
    
    # GET request - show login form
    # Store the referrer URL in session for redirect after login (only if it's not an auth page)
    if request.referrer and not is_auth_page(request.referrer):
        session['last_non_auth_page'] = request.referrer
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # Store the referrer URL before clearing the session (only if it's not an auth page)
    redirect_url = request.referrer if request.referrer and not is_auth_page(request.referrer) else None
    
    # Invalidate the session token in the database
    if 'session_token' in session:
        invalidate_session_token(session['session_token'])
    
    # Clear the session
    session.clear()
    flash('You have been logged out.', 'info')
    
    # Smart redirect: avoid redirecting to auth pages
    if redirect_url:
        return redirect(redirect_url)
    else:
        return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
@logout_required
def signup():
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('firstName', '').strip()
        last_name = request.form.get('lastName', '').strip()
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirmPassword', '')
        
        # Validate the form data
        try:
            validation_errors = validate_signup_data(first_name, last_name, email, username, password, confirm_password)
            
            if validation_errors:
                for error in validation_errors:
                    flash(error, 'error')
                return render_template('signup.html')
            
            # Try to create the account
            result = add_account(first_name, last_name, email, username, password)
            
            if result and result['success']:
                user = result['user']
                
                # Log the user in automatically after successful signup
                ip_address = request.remote_addr
                user_agent = request.headers.get('User-Agent')
                session_token = create_session_token(user['id'], ip_address, user_agent)
                
                if session_token:
                    # Store session info in Flask session
                    session['logged_in'] = True
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['session_token'] = session_token
                    
                    # Show success message
                    flash(f'Welcome to Cinemacousas, {user["first_name"]}! Your account has been created successfully.', 'success')
                    
                    # Smart redirect: get non-auth page from session or go to home
                    redirect_url = session.get('last_non_auth_page', url_for('index'))
                    return redirect(redirect_url)
                else:
                    flash('Account created successfully, but there was an error logging you in. Please try logging in manually.', 'info')
                    return redirect(url_for('login'))
            elif result:
                # Account creation failed with a specific error message
                flash(result['error'], 'error')
                return render_template('signup.html')
            else:
                # Database error occurred
                flash('Server unavailable, please try again later.', 'error')
                return render_template('signup.html')
        except Exception as e:
            # Catch any other unexpected errors
            flash('Server unavailable, please try again later.', 'error')
            print(f"Signup error: {e}")  # Log for debugging
            return render_template('signup.html')
    
    # GET request - show signup form
    # Store the referrer URL in session for redirect after signup (only if it's not an auth page)
    if request.referrer and not is_auth_page(request.referrer):
        session['last_non_auth_page'] = request.referrer
    
    return render_template('signup.html')

@app.route('/validate_identifiers', methods=['POST'])
def validate_identifiers():
    """AJAX endpoint to validate identifiers before proceeding to password step"""
    first_name = request.form.get('firstName', '').strip()
    last_name = request.form.get('lastName', '').strip()
    email = request.form.get('email', '').strip().lower()
    username = request.form.get('username', '').strip()
    
    try:
        # Validate the identifiers
        validation_errors = validate_signup_identifiers(first_name, last_name, email, username)
        
        if validation_errors:
            return jsonify({
                'success': False,
                'errors': validation_errors
            })
        else:
            return jsonify({
                'success': True,
                'message': 'All identifiers are valid!'
            })
    except Exception as e:
        print(f"Identifier validation error: {e}")
        return jsonify({
            'success': False,
            'errors': ['Server unavailable, please try again later.']
        })

@app.route('/get_cancel_redirect')
def get_cancel_redirect():
    """API endpoint to get the correct redirect URL for cancel buttons"""
    redirect_url = session.get('last_non_auth_page', url_for('index'))
    return jsonify({'redirect_url': redirect_url})

@app.route('/profile')
@login_required
def profile():
    """User profile page - requires authentication"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            flash('Session error. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        # Get user information from database
        user = get_user_by_id(user_id)
        if not user:
            flash('User information not found.', 'error')
            return redirect(url_for('index'))
        
        return render_template('profile.html', user=user)
    except Exception as e:
        flash('Server unavailable, please try again later.', 'error')
        print(f"Profile page error: {e}")  # Log for debugging
        return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page - requires authentication"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            flash('Session error. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        # Get user information from database
        user = get_user_by_id(user_id)
        if not user:
            flash('User information not found.', 'error')
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            # Handle form submissions
            form_type = request.form.get('form_type')
            
            if form_type == 'profile':
                # Handle profile update
                first_name = request.form.get('first_name', '').strip()
                last_name = request.form.get('last_name', '').strip()
                email = request.form.get('email', '').strip().lower()
                username = request.form.get('username', '').strip()
                
                # Basic validation
                if not all([first_name, last_name, email, username]):
                    flash('All fields are required.', 'error')
                    return render_template('settings.html', user=user)
                
                # Validate email format
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    flash('Please enter a valid email address.', 'error')
                    return render_template('settings.html', user=user)
                
                # Validate username (alphanumeric and underscore only, 3-20 chars)
                username_pattern = r'^[a-zA-Z0-9_]{3,20}$'
                if not re.match(username_pattern, username):
                    flash('Username must be 3-20 characters long and contain only letters, numbers, and underscores.', 'error')
                    return render_template('settings.html', user=user)
                
                # Update profile in database
                result = modify_account_profile(user_id, first_name, last_name, email, username)
                
                if result and result['success']:
                    # Update session username if it changed
                    if username != session.get('username'):
                        session['username'] = username
                    
                    flash('Profile updated successfully!', 'success')
                    # Redirect to refresh the page with updated data
                    return redirect(url_for('settings'))
                elif result:
                    flash(result['error'], 'error')
                else:
                    flash('Server unavailable, please try again later.', 'error')
                
            elif form_type == 'password':
                # Handle password change
                current_password = request.form.get('current_password', '')
                new_password = request.form.get('new_password', '')
                confirm_password = request.form.get('confirm_password', '')
                
                # Basic validation
                if not all([current_password, new_password, confirm_password]):
                    flash('All password fields are required.', 'error')
                    return render_template('settings.html', user=user)
                
                if new_password != confirm_password:
                    flash('New passwords do not match.', 'error')
                    return render_template('settings.html', user=user)
                
                # Validate new password strength
                if len(new_password) < 8:
                    flash('New password must be at least 8 characters long.', 'error')
                    return render_template('settings.html', user=user)
                
                # Update password in database
                result = modify_account_password(user_id, current_password, new_password)
                
                if result and result['success']:
                    flash('Password updated successfully!', 'success')
                    # Redirect to refresh the page
                    return redirect(url_for('settings'))
                elif result:
                    flash(result['error'], 'error')
                else:
                    flash('Server unavailable, please try again later.', 'error')
        
        return render_template('settings.html', user=user)
    except Exception as e:
        flash('Server unavailable, please try again later.', 'error')
        print(f"Settings page error: {e}")  # Log for debugging
        return redirect(url_for('index'))

# Helper function to check if a URL is an authentication page
def is_auth_page(url):
    """Check if a URL is a login or signup page"""
    if not url:
        return False
    
    # Parse the URL to get the path
    from urllib.parse import urlparse
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    # Check if it's a login or signup page
    return path.endswith('/login') or path.endswith('/signup') or '/login' in path or '/signup' in path

if __name__ == '__main__':
    app.run(debug=config.DEBUG, host='0.0.0.0', port=5500)

