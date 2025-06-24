import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
from datetime import datetime, timedelta

# Database connection configuration
DB_CONFIG = {
    "host": "82.66.24.184",
    "port": 3305,
    "user": "cinemacousas",
    "password": "password",
    "database": "Cinemacousas"
}

def get_db_connection():
    """Create a new database connection"""
    return mysql.connector.connect(**DB_CONFIG)

def test_database_connection():
    """Test database connection and return account count"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM account")
        count = cursor.fetchone()[0]
        print(f"✓ Database connected successfully. Found {count} accounts.")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def get_user_by_username(username):
    """Get user from database by username"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, email, username, password_hash FROM account WHERE username = %s", (username,))
        user = cursor.fetchone()
        return user
    except Exception as e:
        print(f"Error getting user: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_by_email(email):
    """Get user from database by email"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, email, username, password_hash FROM account WHERE email = %s", (email,))
        user = cursor.fetchone()
        return user
    except Exception as e:
        print(f"Error getting user: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def create_session_token(account_id, ip_address=None, user_agent=None):
    """Create a new session token in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Generate a secure session token
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)  # Session expires in 24 hours
        
        cursor.execute("""
            INSERT INTO account_session (account_id, session_token, expires_at, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s)
        """, (account_id, session_token, expires_at, ip_address, user_agent))
        
        conn.commit()
        return session_token
    except Exception as e:
        print(f"Error creating session: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def invalidate_session_token(session_token):
    """Mark a session token as inactive"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE account_session 
            SET is_active = FALSE 
            WHERE session_token = %s
        """, (session_token,))
        conn.commit()
    except Exception as e:
        print(f"Error invalidating session: {e}")
    finally:
        cursor.close()
        conn.close()

def validate_session_token(session_token):
    """Validate if a session token is active and not expired"""
    conn = get_db_connection()
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
    except Exception as e:
        print(f"Error validating session: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def create_user(username, email, password):
    """Create a new user account"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Hash the password
        password_hash = generate_password_hash(password)
        
        cursor.execute("""
            INSERT INTO account (username, email, password_hash)
            VALUES (%s, %s, %s)
        """, (username, email, password_hash))
        
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error creating user: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def authenticate_user(email, password):
    """Authenticate a user with email and password"""
    user = get_user_by_email(email)
    
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None

def cleanup_expired_sessions():
    """Clean up expired sessions from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE account_session 
            SET is_active = FALSE 
            WHERE expires_at < NOW() AND is_active = TRUE
        """)
        conn.commit()
        affected_rows = cursor.rowcount
        print(f"Cleaned up {affected_rows} expired sessions.")
    except Exception as e:
        print(f"Error cleaning up sessions: {e}")
    finally:
        cursor.close()
        conn.close()

def get_user_sessions(user_id):
    """Get all active sessions for a user"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT session_token, created_at, expires_at, ip_address, user_agent
            FROM account_session 
            WHERE account_id = %s AND is_active = TRUE
            ORDER BY created_at DESC
        """, (user_id,))
        
        return cursor.fetchall()
    except Exception as e:
        print(f"Error getting user sessions: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_all_movies():
    """Get all movies from the database"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM movie ORDER BY name")
        movies = cursor.fetchall()
        return movies
    except Exception as e:
        print(f"Error getting movies: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def analyze_movie_table():
    """Analyze the movie table structure and sample data"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get table structure
        cursor.execute("DESCRIBE movie")
        columns = cursor.fetchall()
        print("Movie table structure:")
        for col in columns:
            print(f"  {col['Field']}: {col['Type']} (Null: {col['Null']}, Key: {col['Key']})")
        
        # Get sample data
        cursor.execute("SELECT * FROM movie LIMIT 3")
        sample_movies = cursor.fetchall()
        print("\nSample movie data:")
        for movie in sample_movies:
            print(f"  Movie: {movie}")
            
        return columns, sample_movies
    except Exception as e:
        print(f"Error analyzing movie table: {e}")
        return [], []
    finally:
        cursor.close()
        conn.close()

def add_account(first_name, last_name, email, username, password):
    """Create a new user account with full details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if email already exists
        cursor.execute("SELECT id FROM account WHERE email = %s", (email,))
        if cursor.fetchone():
            return {"success": False, "error": "Email address is already registered"}
        
        # Check if username already exists
        cursor.execute("SELECT id FROM account WHERE username = %s", (username,))
        if cursor.fetchone():
            return {"success": False, "error": "Username is already taken"}
        
        # Hash the password
        password_hash = generate_password_hash(password)
        
        # Insert new account
        cursor.execute("""
            INSERT INTO account (first_name, last_name, email, username, password_hash)
            VALUES (%s, %s, %s, %s, %s)
        """, (first_name, last_name, email, username, password_hash))
        
        conn.commit()
        user_id = cursor.lastrowid
        
        # Return the created user data
        cursor.execute("SELECT id, first_name, last_name, email, username FROM account WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        
        return {
            "success": True, 
            "user": {
                "id": user_data[0],
                "first_name": user_data[1],
                "last_name": user_data[2],
                "email": user_data[3],
                "username": user_data[4]
            }
        }
        
    except mysql.connector.IntegrityError as e:
        if "email" in str(e).lower():
            return {"success": False, "error": "Email address is already registered"}
        elif "username" in str(e).lower():
            return {"success": False, "error": "Username is already taken"}
        else:
            return {"success": False, "error": "Account creation failed due to duplicate data"}
    except Exception as e:
        print(f"Error creating account: {e}")
        return {"success": False, "error": "An error occurred while creating your account. Please try again."}
    finally:
        cursor.close()
        conn.close()

def validate_signup_identifiers(first_name, last_name, email, username):
    """Validate signup form identifiers (first name, last name, email, username)"""
    errors = []
    
    # Name validation
    if not first_name or len(first_name.strip()) < 2:
        errors.append("First name must be at least 2 characters long")
    
    if not last_name or len(last_name.strip()) < 2:
        errors.append("Last name must be at least 2 characters long")
    
    # Email validation (basic)
    if not email or "@" not in email or "." not in email:
        errors.append("Please enter a valid email address")
    
    # Username validation
    if not username or len(username) < 3:
        errors.append("Username must be at least 3 characters long")
    
    import re
    if username and not re.match("^[a-zA-Z0-9_]+$", username):
        errors.append("Username can only contain letters, numbers, and underscores")
    
    # Check database constraints if basic validation passes
    if not errors:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check if email already exists
            cursor.execute("SELECT id FROM account WHERE email = %s", (email,))
            if cursor.fetchone():
                errors.append("Email address is already registered")
            
            # Check if username already exists
            cursor.execute("SELECT id FROM account WHERE username = %s", (username,))
            if cursor.fetchone():
                errors.append("Username is already taken")
                
        except Exception as e:
            print(f"Error checking database constraints: {e}")
            errors.append("Unable to verify email and username availability. Please try again.")
        finally:
            cursor.close()
            conn.close()
    
    return errors

def validate_signup_passwords(password, confirm_password):
    """Validate signup form passwords"""
    errors = []
    
    # Password validation
    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if password != confirm_password:
        errors.append("Passwords do not match")
    
    return errors

def validate_signup_data(first_name, last_name, email, username, password, confirm_password):
    """Validate complete signup form data (for backward compatibility)"""
    errors = []
    
    # Validate identifiers
    identifier_errors = validate_signup_identifiers(first_name, last_name, email, username)
    errors.extend(identifier_errors)
    
    # Validate passwords
    password_errors = validate_signup_passwords(password, confirm_password)
    errors.extend(password_errors)
    
    return errors