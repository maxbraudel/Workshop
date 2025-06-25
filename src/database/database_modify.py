import mysql.connector
import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from .database import get_db_connection, handle_db_errors, logger

@handle_db_errors(default_return=None)
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
    finally:
        cursor.close()
        conn.close()

@handle_db_errors(default_return=False)
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
        return True
    finally:
        cursor.close()
        conn.close()

@handle_db_errors(default_return=None)
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
    finally:
        cursor.close()
        conn.close()

@handle_db_errors(default_return=False)
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
        logger.info(f"Cleaned up {affected_rows} expired sessions.")
        return True
    finally:
        cursor.close()
        conn.close()

def add_account(first_name, last_name, email, username, password):
    """Create a new user account with full details"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
        logger.error(f"Database integrity error in add_account: {e}")
        if "email" in str(e).lower():
            return {"success": False, "error": "Email address is already registered"}
        elif "username" in str(e).lower():
            return {"success": False, "error": "Username is already taken"}
        else:
            return {"success": False, "error": "Account creation failed due to duplicate data"}
    except mysql.connector.Error as e:
        logger.error(f"Database error in add_account: {e}")
        return {"success": False, "error": "Server unavailable, please try again later."}
    except Exception as e:
        logger.error(f"Unexpected error in add_account: {e}")
        return {"success": False, "error": "Server unavailable, please try again later."}
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
