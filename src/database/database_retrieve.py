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
                SELECT s.*, a.username, a.email 
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
