from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import (
    test_database_connection,
    authenticate_user,
    create_session_token,
    invalidate_session_token,
    validate_session_token,
    get_all_movies
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
        username = request.form['username']
        password = request.form['password']
        
        # Authenticate user using database function
        user = authenticate_user(username, password)
        
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
            flash('Invalid username or password!', 'error')
    
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

