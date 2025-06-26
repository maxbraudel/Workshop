from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
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
    get_showing_by_id,
    get_seats_for_showing,
    get_booking_by_id,
    get_customers_for_booking,
    get_bookings_by_account_id,
    create_complete_booking,
    create_complete_booking_secure,
    check_seats_availability,
    get_age_pricing,
    calculate_booking_price,
    get_user_by_id,
    add_account,
    modify_account_profile,
    modify_account_password,
    validate_signup_data,
    validate_signup_identifiers,
    validate_signup_passwords,
    validate_login_data,
    is_showing_expired
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

# Custom Jinja2 filter to convert seconds to time format
@app.template_filter('seconds_to_time')
def seconds_to_time(seconds):
    """Convert seconds (float) to HH:MM time format"""
    if seconds is None:
        return '00:00'
    
    # Convert seconds to hours and minutes
    total_minutes = int(seconds // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    
    return f"{hours:02d}:{minutes:02d}"

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
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
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

@app.route('/showing/<int:showing_id>/seats')
def showing_seats(showing_id):
    """Display seat selection page for a showing"""
    try:
        # Get showing details
        showing = get_showing_by_id(showing_id)
        if not showing:
            flash('Showing not found.', 'error')
            return redirect(url_for('movies'))
        
        # Check if showing has expired
        if is_showing_expired(showing):
            abort(404)
        
        # Get seats for the showing
        seats = get_seats_for_showing(showing_id)
        if seats is None:
            flash('Unable to load seats. Please try again.', 'error')
            return redirect(url_for('movies'))
        
        return render_template('showing_seats.html', 
                             showing=showing, 
                             seats=seats)
    
    except Exception as e:
        # Re-raise HTTP exceptions (like abort(404)) to let Flask handle them properly
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            raise e
        
        flash('Server unavailable, please try again later.', 'error')
        print(f"Showing seats error: {e}")
        return redirect(url_for('movies'))

@app.route('/booking/spectators', methods=['POST'])
def booking_spectators():
    """Handle spectator information entry"""
    try:
        # Get data from the form
        showing_id = request.form.get('showing_id')
        selected_seats = request.form.getlist('selected_seats')
        
        if not showing_id or not selected_seats:
            flash('Invalid booking data.', 'error')
            return redirect(url_for('movies'))
        
        # Convert seat IDs to integers
        try:
            selected_seats = [int(seat_id) for seat_id in selected_seats]
        except ValueError:
            flash('Invalid seat selection.', 'error')
            return redirect(url_for('movies'))
        
        # Verify seats are still available
        if not check_seats_availability(selected_seats, showing_id):
            flash('Some selected seats are no longer available.', 'error')
            return redirect(url_for('showing_seats', showing_id=showing_id))
        
        # Get showing info
        showing = get_showing_by_id(showing_id)
        
        if not showing:
            flash('Booking information unavailable.', 'error')
            return redirect(url_for('movies'))
        
        # Check if showing has expired
        if is_showing_expired(showing):
            abort(404)
        
        # Get seat details for the selected seats
        all_seats = get_seats_for_showing(showing_id)
        selected_seat_details = [seat for seat in all_seats if seat['id'] in selected_seats]
        
        # Get logged-in user information for prefilling booker details
        from flask import g
        current_user = None
        if hasattr(g, 'current_user') and g.current_user:
            current_user = g.current_user
        
        return render_template('booking_spectators.html',
                             showing=showing,
                             selected_seats=selected_seat_details,
                             num_spectators=len(selected_seats),
                             current_user=current_user)
    
    except Exception as e:
        # Re-raise HTTP exceptions (like abort(404)) to let Flask handle them properly
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            raise e
        
        flash('Server unavailable, please try again later.', 'error')
        print(f"Booking spectators error: {e}")
        return redirect(url_for('movies'))

@app.route('/api/calculate_price', methods=['POST'])
def calculate_price():
    """API endpoint to calculate booking price on the server side"""
    try:
        # Debug: Log the incoming request
        print(f"DEBUG: Price calculation request received")
        print(f"DEBUG: Request content type: {request.content_type}")
        print(f"DEBUG: Request data: {request.get_data()}")
        
        data = request.get_json()
        print(f"DEBUG: Parsed JSON data: {data}")
        
        showing_id = data.get('showing_id') if data else None
        spectators = data.get('spectators', []) if data else []
        
        print(f"DEBUG: showing_id: {showing_id}, spectators: {spectators}")
        
        if not showing_id or not spectators:
            print("DEBUG: Missing required data - showing_id or spectators")
            return jsonify({'success': False, 'error': 'Missing required data'})
        
        # Get showing info to retrieve base price
        print(f"DEBUG: Getting showing by ID: {showing_id}")
        showing = get_showing_by_id(showing_id)
        print(f"DEBUG: Showing result: {showing}")
        
        if not showing:
            print("DEBUG: Showing not found")
            return jsonify({'success': False, 'error': 'Showing not found'})
        
        # Check if baseprice field exists
        if 'baseprice' not in showing:
            print(f"DEBUG: baseprice field not found in showing. Available fields: {list(showing.keys())}")
            return jsonify({'success': False, 'error': 'Base price not available'})
        
        base_price = showing['baseprice']
        print(f"DEBUG: Base price: {base_price}")
        
        # Calculate total price using secure server-side function
        print(f"DEBUG: Calling calculate_booking_price with showing_id={showing_id}, spectators={spectators}")
        price_result = calculate_booking_price(showing_id, spectators)
        print(f"DEBUG: Price calculation result: {price_result}")
        
        if price_result is None:
            print("DEBUG: Price calculation returned None")
            return jsonify({'success': False, 'error': 'Unable to calculate price'})
        
        result = {
            'success': True,
            'total_price': price_result['total_price'],
            'base_price': price_result['base_price'],
            'spectator_count': len(spectators),
            'price_breakdown': price_result['price_breakdown']
        }
        print(f"DEBUG: Returning successful result: {result}")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Price calculation error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'})

@app.route('/booking/confirm', methods=['POST'])
def booking_confirm():
    """Process the complete booking"""
    try:
        # Get form data
        showing_id = request.form.get('showing_id')
        selected_seats = request.form.getlist('selected_seats')
        
        # Validate showing exists and hasn't expired
        if showing_id:
            showing = get_showing_by_id(showing_id)
            if not showing:
                flash('Showing not found.', 'error')
                return redirect(url_for('movies'))
            
            if is_showing_expired(showing):
                abort(404)
        
        # Booker information
        booker_email = request.form.get('booker_email')
        booker_first_name = request.form.get('booker_first_name')
        booker_last_name = request.form.get('booker_last_name')
        
        # Spectator information
        num_spectators = len(selected_seats) if selected_seats else 0
        spectators = []
        
        # Convert seat IDs to integers first so we can get seat information
        try:
            selected_seat_ids = [int(seat_id) for seat_id in selected_seats]
        except ValueError:
            flash('Invalid booking data.', 'error')
            return redirect(url_for('movies'))
        
        # Get seat information to determine PMR status
        all_seats = get_seats_for_showing(showing_id)
        seat_info_map = {seat['id']: seat for seat in all_seats}
        
        for i in range(num_spectators):
            # Calculate age from birth date
            birth_date_str = request.form.get(f'spectator_{i}_birth_date')
            if birth_date_str:
                from datetime import date
                birth_date = date.fromisoformat(birth_date_str)
                today = date.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            else:
                age = 0
            
            # Get PMR status from seat type instead of form checkbox
            seat_id = selected_seat_ids[i]
            seat_info = seat_info_map.get(seat_id, {})
            is_pmr = 1 if seat_info.get('type') == 'pmr' else 0
            
            spectator = {
                'firstname': request.form.get(f'spectator_{i}_first_name'),
                'lastname': request.form.get(f'spectator_{i}_last_name'),
                'age': age,
                'pmr': is_pmr
            }
            spectators.append(spectator)
        
        # Validate required fields
        if not all([showing_id, booker_email, booker_first_name, booker_last_name]):
            flash('Please fill in all required booker information.', 'error')
            return redirect(url_for('movies'))
        
        for i, spectator in enumerate(spectators):
            if not all([spectator['firstname'], spectator['lastname']]):
                flash(f'Please fill in all information for spectator {i+1}.', 'error')
                return redirect(url_for('movies'))
        
        # Create the booking - use logged-in user's account_id if available
        from flask import g
        
        # Check if user is logged in and get their account_id
        if hasattr(g, 'current_user') and g.current_user:
            account_id = g.current_user['id']
        else:
            # For anonymous bookings, we'll use None and let the database function handle it
            account_id = None
        
        # Prepare booker information
        booker_info = {
            'first_name': booker_first_name,
            'last_name': booker_last_name,
            'email': booker_email
        }
        
        # Use the secure booking function that calculates prices server-side
        booking_result = create_complete_booking_secure(showing_id, account_id, spectators, selected_seat_ids, booker_info)
        
        if booking_result and booking_result.get('success'):
            booking_id = booking_result['booking_id']
            flash('Booking confirmed successfully!', 'success')
            return redirect(url_for('booking_tickets', booking_id=booking_id))
        else:
            error_msg = booking_result.get('error', 'The selected seats may no longer be available.') if booking_result else 'Booking failed.'
            flash(f'Booking failed. {error_msg}', 'error')
            return redirect(url_for('showing_seats', showing_id=showing_id))
    
    except Exception as e:
        # Re-raise HTTP exceptions (like abort(404)) to let Flask handle them properly
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            raise e
        
        flash('Server unavailable, please try again later.', 'error')
        print(f"Booking confirm error: {e}")
        return redirect(url_for('movies'))

@app.route('/booking/<int:booking_id>/tickets')
def booking_tickets(booking_id):
    """Display booking confirmation and tickets"""
    try:
        # Get booking details
        booking = get_booking_by_id(booking_id)
        if not booking:
            flash('Booking not found.', 'error')
            return redirect(url_for('movies'))
        
        # Get customers/spectators for this booking
        customers = get_customers_for_booking(booking_id)
        
        return render_template('booking_tickets.html', 
                             booking=booking, 
                             customers=customers)
    
    except Exception as e:
        flash('Server unavailable, please try again later.', 'error')
        print(f"Booking tickets error: {e}")
        return redirect(url_for('movies'))

@app.route('/my-tickets')
@login_required
def my_tickets():
    """Display user's non-expired booking history"""
    try:
        from flask import g
        
        # Get user ID from g.current_user (set by middleware)
        if not hasattr(g, 'current_user') or not g.current_user:
            flash('Session error. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        user_id = g.current_user['id']
        
        # Get only non-expired bookings for this user
        bookings = get_bookings_by_account_id(user_id, expired=False)
        
        # Add today's date for comparison in template
        from datetime import date
        today = date.today()
        
        # Ensure all booking dates are date objects for proper comparison
        for booking in bookings:
            if hasattr(booking['date'], 'date'):
                # If it's a datetime object, extract the date part
                booking['date'] = booking['date'].date()
        
        return render_template('my_tickets.html', bookings=bookings, today=today)
    
    except Exception as e:
        flash('Server unavailable, please try again later.', 'error')
        print(f"My tickets error: {e}")
        return redirect(url_for('index'))

@app.route('/expired-tickets')
@login_required
def expired_tickets():
    """Display user's expired booking history"""
    try:
        from flask import g
        
        # Get user ID from g.current_user (set by middleware)
        if not hasattr(g, 'current_user') or not g.current_user:
            flash('Session error. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        user_id = g.current_user['id']
        
        # Get only expired bookings for this user
        bookings = get_bookings_by_account_id(user_id, expired=True)
        
        # Add today's date for comparison in template
        from datetime import date
        today = date.today()
        
        # Ensure all booking dates are date objects for proper comparison
        for booking in bookings:
            if hasattr(booking['date'], 'date'):
                # If it's a datetime object, extract the date part
                booking['date'] = booking['date'].date()
        
        return render_template('expired_tickets.html', bookings=bookings, today=today)
    
    except Exception as e:
        flash('Server unavailable, please try again later.', 'error')
        print(f"Expired tickets error: {e}")
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

