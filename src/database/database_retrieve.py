from .database import get_db_connection, handle_db_errors, logger

@handle_db_errors(default_return=None)
def get_user_by_id(user_id):
    """Get user from database by ID with full profile information"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT id, email, username, first_name, last_name, created_at, password_modified_at, profile_modified_at FROM account WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            return user
        finally:
            cursor.close()

@handle_db_errors(default_return=None)
def get_user_by_username(username):
    """Get user from database by username"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT id, email, username, password_hash FROM account WHERE username = %s", (username,))
            user = cursor.fetchone()
            return user
        finally:
            cursor.close()

@handle_db_errors(default_return=None)
def get_user_by_email(email):
    """Get user from database by email"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT id, email, username, password_hash FROM account WHERE email = %s", (email,))
            user = cursor.fetchone()
            return user
        finally:
            cursor.close()

@handle_db_errors(default_return=None)
def validate_session_token(session_token):
    """Validate if a session token is active and not expired"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT s.*, a.username, a.email, a.first_name, a.last_name 
                FROM account_session s
                JOIN account a ON s.account_id = a.id
                WHERE s.session_token = %s 
                AND s.is_active = TRUE 
                AND (s.expires_at IS NULL OR s.expires_at > NOW())
            """, (session_token,))
            
            return cursor.fetchone()
        finally:
            cursor.close()

@handle_db_errors(default_return=[])
def get_user_sessions(user_id):
    """Get all active sessions for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT session_token, created_at, expires_at, ip_address, user_agent
                FROM account_session 
                WHERE account_id = %s AND is_active = TRUE
                ORDER BY created_at DESC
            """, (user_id,))
            
            return cursor.fetchall()
        finally:
            cursor.close()

@handle_db_errors(default_return=[])
def get_all_movies():
    """Get all movies from the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT * FROM movie ORDER BY name")
            movies = cursor.fetchall()
            return movies
        finally:
            cursor.close()

@handle_db_errors(default_return=[])
def get_movies_with_showings():
    """Get all movies with their showings"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get all movies
            cursor.execute("SELECT * FROM movie ORDER BY name")
            movies = cursor.fetchall()
            
            # For each movie, get its showings
            for movie in movies:
                cursor.execute("""
                    SELECT id, date, starttime, baseprice, room_id 
                    FROM showing 
                    WHERE movie_id = %s 
                    ORDER BY date, starttime
                """, (movie['id'],))
                showings = cursor.fetchall()
                
                # Convert timedelta objects to total seconds for JSON serialization
                for showing in showings:
                    if hasattr(showing['starttime'], 'total_seconds'):
                        showing['starttime'] = showing['starttime'].total_seconds()
                
                movie['showings'] = showings
            
            return movies
        finally:
            cursor.close()

@handle_db_errors(default_return=[])
def get_movies_with_showings_by_date(target_date):
    """Get movies that have showings on a specific date"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get movies that have showings on the target date
            cursor.execute("""
                SELECT DISTINCT m.* 
                FROM movie m
                INNER JOIN showing s ON m.id = s.movie_id
                WHERE DATE(s.date) = %s
                ORDER BY m.name
            """, (target_date,))
            movies = cursor.fetchall()
            
            # For each movie, get its showings for the target date
            for movie in movies:
                cursor.execute("""
                    SELECT id, date, starttime, baseprice, room_id 
                    FROM showing 
                    WHERE movie_id = %s AND DATE(date) = %s
                    ORDER BY starttime
                """, (movie['id'], target_date))
                showings = cursor.fetchall()
                
                # Convert timedelta objects to total seconds for JSON serialization
                for showing in showings:
                    if hasattr(showing['starttime'], 'total_seconds'):
                        showing['starttime'] = showing['starttime'].total_seconds()
                
                movie['showings'] = showings
            
            return movies
        finally:
            cursor.close()

@handle_db_errors(default_return=None)
def get_showing_by_id(showing_id):
    """Get showing details by ID with movie and room information"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT s.*, m.name as movie_name, m.duration, m.director, m.cast, m.synopsis,
                       r.name as room_name, r.nb_rows, r.nb_columns
                FROM showing s
                JOIN movie m ON s.movie_id = m.id
                JOIN room r ON s.room_id = r.id
                WHERE s.id = %s
            """, (showing_id,))
            
            showing = cursor.fetchone()
            
            if showing and hasattr(showing['starttime'], 'total_seconds'):
                showing['starttime'] = showing['starttime'].total_seconds()
                
            return showing
        finally:
            cursor.close()

@handle_db_errors(default_return=[])
def get_seats_for_showing(showing_id):
    """Get all seats for a showing with their reservation status"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        try:
            # First get the room_id from the showing
            cursor.execute("SELECT room_id FROM showing WHERE id = %s", (showing_id,))
            showing = cursor.fetchone()
            
            if not showing:
                return []
            
            room_id = showing['room_id']
            
            # Get all seats for this room with their reservation status
            cursor.execute("""
                SELECT s.id, s.type, s.seat_row, s.seat_column,
                       CASE WHEN sr.seat_id IS NOT NULL THEN 1 ELSE 0 END as is_occupied
                FROM seat s
                LEFT JOIN seatreservation sr ON s.id = sr.seat_id AND sr.showing_id = %s
                WHERE s.room_id = %s
                ORDER BY s.seat_row, s.seat_column
            """, (showing_id, room_id))
            
            return cursor.fetchall()
        finally:
            cursor.close()

@handle_db_errors(default_return=[])
def get_age_pricing():
    """Get all age pricing rules"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT id, name, agemin, agemax, factor
                FROM ageprice
                ORDER BY agemin
            """)
            return cursor.fetchall()
        finally:
            cursor.close()

@handle_db_errors(default_return=None)
def calculate_booking_price(showing_id, spectators):
    """
    Calculate total booking price server-side based on showing base price and spectator ages
    
    Args:
        showing_id: ID of the showing
        spectators: List of dictionaries with 'age' key
    
    Returns:
        Dictionary with total_price and price_breakdown
    """
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Get showing base price
            cursor.execute("""
                SELECT baseprice 
                FROM showing 
                WHERE id = %s
            """, (showing_id,))
            
            showing = cursor.fetchone()
            if not showing:
                return None
                
            # Convert base price from cents to euros
            base_price_cents = float(showing['baseprice'])
            base_price = base_price_cents / 100.0  # Convert cents to euros
            
            # Get age pricing rules
            cursor.execute("""
                SELECT id, name, agemin, agemax, factor
                FROM ageprice
                ORDER BY agemin
            """)
            
            age_rules = cursor.fetchall()
            
            if not age_rules:
                return None
            
            total_price = 0.0
            price_breakdown = []
            
            # Calculate price for each spectator
            for spectator in spectators:
                age = int(spectator['age'])
                
                # Find appropriate age rule
                applicable_rule = None
                for rule in age_rules:
                    if rule['agemin'] <= age <= rule['agemax']:
                        applicable_rule = rule
                        break
                
                if not applicable_rule:
                    # Fallback to adult pricing if no rule matches
                    applicable_rule = next((r for r in age_rules if r['name'] == 'Adulte'), age_rules[0])
                
                # Calculate price for this spectator (already in euros)
                spectator_price = base_price * float(applicable_rule['factor'])
                total_price += spectator_price
                
                price_breakdown.append({
                    'age': age,
                    'category': applicable_rule['name'],
                    'factor': float(applicable_rule['factor']),
                    'price': round(spectator_price, 2)
                })
            
            return {
                'total_price': round(total_price, 2),
                'base_price': base_price,
                'spectator_count': len(spectators),
                'price_breakdown': price_breakdown
            }
            
        finally:
            cursor.close()

@handle_db_errors(default_return=None)
def get_booking_by_id(booking_id):
    """Get booking details with showing and movie information"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT b.*, s.date, s.starttime, s.baseprice,
                       m.name as movie_name, m.duration,
                       r.name as room_name
                FROM booking b
                JOIN showing s ON b.showing_id = s.id
                JOIN movie m ON s.movie_id = m.id
                JOIN room r ON s.room_id = r.id
                WHERE b.id = %s
            """, (booking_id,))
            
            booking = cursor.fetchone()
            
            if booking and hasattr(booking['starttime'], 'total_seconds'):
                booking['starttime'] = booking['starttime'].total_seconds()
                
            return booking
        finally:
            cursor.close()

@handle_db_errors(default_return=[])
def get_customers_for_booking(booking_id):
    """Get all customers/spectators for a booking with their seat information"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT c.*, s.seat_row, s.seat_column, s.type as seat_type
                FROM customer c
                JOIN seatreservation sr ON c.id = sr.customer_id
                JOIN seat s ON sr.seat_id = s.id
                WHERE c.booking_id = %s
                ORDER BY s.seat_row, s.seat_column
            """, (booking_id,))
            
            return cursor.fetchall()
        finally:
            cursor.close()

@handle_db_errors(default_return=[])
def get_bookings_by_account_id(account_id):
    """Get all bookings for a specific account with movie and showing information"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT b.id, b.price, b.account_id, b.showing_id,
                       s.date, s.starttime, s.baseprice,
                       m.name as movie_name, m.duration,
                       r.name as room_name,
                       COUNT(c.id) as num_spectators
                FROM booking b
                JOIN showing s ON b.showing_id = s.id
                JOIN movie m ON s.movie_id = m.id
                JOIN room r ON s.room_id = r.id
                LEFT JOIN customer c ON b.id = c.booking_id
                WHERE b.account_id = %s
                GROUP BY b.id, b.price, b.account_id, b.showing_id, s.date, s.starttime, s.baseprice, m.name, m.duration, r.name
                ORDER BY s.date DESC, s.starttime DESC
            """, (account_id,))
            
            bookings = cursor.fetchall()
            
            # Convert timedelta objects to total seconds for display
            for booking in bookings:
                if hasattr(booking['starttime'], 'total_seconds'):
                    booking['starttime'] = booking['starttime'].total_seconds()
                    
            return bookings
        finally:
            cursor.close()
