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

def authenticate_user(username, password):
    """Authenticate a user with username and password"""
    user = get_user_by_username(username)
    
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