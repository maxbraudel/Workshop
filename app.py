from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import (
    test_database_connection,
    authenticate_user,
    create_session_token,
    invalidate_session_token,
    validate_session_token,
    get_all_movies,
    add_account,
    validate_signup_data,
    validate_signup_identifiers,
    validate_signup_passwords
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Required for sessions

# Test database connection
test_database_connection()

@app.route('/')
def index():
    return render_template('index.html', storeUrl=True)

@app.route('/movies')
def movies():
    # Get all movies from the database
    movies_list = get_all_movies()
    return render_template('movies.html', movies=movies_list, storeUrl=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Authenticate user using database function
        user = authenticate_user(email, password)
        
        if user:
            # Login successful - create session token and store in database
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
                
                # Get the redirect URL from session (stored when GET request was made)
                redirect_url = session.pop('login_redirect_url', None)
                
                # Redirect to previous URL or home page
                if redirect_url and redirect_url != request.url and redirect_url != url_for('login'):
                    return redirect(redirect_url)
                else:
                    return redirect(url_for('index'))
            else:
                flash('Error creating session. Please try again.', 'error')
        else:
            # Login failed
            flash('Invalid email or password!', 'error')
    
    # GET request - show login form
    # Store the referrer URL in session for redirect after login
    if request.referrer and request.referrer != request.url:
        session['login_redirect_url'] = request.referrer
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Store the referrer URL before clearing the session
    redirect_url = request.referrer
    
    # Invalidate the session token in the database
    if 'session_token' in session:
        invalidate_session_token(session['session_token'])
    
    # Clear the session
    session.clear()
    flash('You have been logged out.', 'info')
    
    # Redirect back to previous page or home if no referrer
    if redirect_url and redirect_url != request.url:
        return redirect(redirect_url)
    else:
        return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
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
        validation_errors = validate_signup_data(first_name, last_name, email, username, password, confirm_password)
        
        if validation_errors:
            for error in validation_errors:
                flash(error, 'error')
            return render_template('signup.html')
        
        # Try to create the account
        result = add_account(first_name, last_name, email, username, password)
        
        if result['success']:
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
                
                # Redirect to home page
                return redirect(url_for('index'))
            else:
                flash('Account created successfully, but there was an error logging you in. Please try logging in manually.', 'info')
                return redirect(url_for('login'))
        else:
            # Account creation failed
            flash(result['error'], 'error')
            return render_template('signup.html')
    
    # GET request - show signup form
    return render_template('signup.html')

@app.route('/validate_identifiers', methods=['POST'])
def validate_identifiers():
    """AJAX endpoint to validate identifiers before proceeding to password step"""
    first_name = request.form.get('firstName', '').strip()
    last_name = request.form.get('lastName', '').strip()
    email = request.form.get('email', '').strip().lower()
    username = request.form.get('username', '').strip()
    
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

# Helper function to check if user is logged in
def is_logged_in():
    return 'logged_in' in session and session['logged_in']

# Make is_logged_in available in all templates
@app.context_processor
def inject_user():
    return dict(
        is_logged_in=is_logged_in(),
        current_user=session.get('username', None)
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5500)

