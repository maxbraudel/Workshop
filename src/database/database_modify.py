import mysql.connector
import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from .database import get_db_connection, handle_db_errors, logger
from ..config import get_config

# Get configuration
config = get_config()

@handle_db_errors(default_return=None)
def create_session_token(account_id, ip_address=None, user_agent=None):
    """Create a new session token in the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # Generate a secure session token
            session_token = secrets.token_urlsafe(32)
            session_lifetime_hours = config.SESSION_LIFETIME_HOURS
            expires_at = datetime.now() + timedelta(hours=session_lifetime_hours)
            
            cursor.execute("""
                INSERT INTO account_session (account_id, session_token, expires_at, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            """, (account_id, session_token, expires_at, ip_address, user_agent))
            
            conn.commit()
            return session_token
        finally:
            cursor.close()

@handle_db_errors(default_return=False)
def invalidate_session_token(session_token):
    """Mark a session token as inactive"""
    with get_db_connection() as conn:
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

@handle_db_errors(default_return=None)
def create_user(username, email, password):
    """Create a new user account"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # Hash the password
            password_hash = generate_password_hash(password)
            
            cursor.execute("""
                INSERT INTO account (username, email, password_hash, password_modified_at)
                VALUES (%s, %s, %s, NOW())
            """, (username, email, password_hash))
            
            conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()

@handle_db_errors(default_return=False)
def cleanup_expired_sessions():
    """Clean up expired sessions from the database"""
    with get_db_connection() as conn:
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

def add_account(first_name, last_name, email, username, password):
    """Create a new user account with full details"""
    try:
        with get_db_connection() as conn:
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
                INSERT INTO account (first_name, last_name, email, username, password_hash, password_modified_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (first_name, last_name, email, username, password_hash))
            
            conn.commit()
            user_id = cursor.lastrowid
            
            # Return the created user data
            cursor.execute("SELECT id, first_name, last_name, email, username FROM account WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            
            cursor.close()
            
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

@handle_db_errors(default_return=None)
def modify_account_profile(user_id, first_name, last_name, email, username):
    """Update user profile information"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if email already exists for another user
            cursor.execute("SELECT id FROM account WHERE email = %s AND id != %s", (email, user_id))
            if cursor.fetchone():
                return {"success": False, "error": "Email address is already registered by another user"}
            
            # Check if username already exists for another user
            cursor.execute("SELECT id FROM account WHERE username = %s AND id != %s", (username, user_id))
            if cursor.fetchone():
                return {"success": False, "error": "Username is already taken by another user"}
            
            # Update account information
            cursor.execute("""
                UPDATE account 
                SET first_name = %s, last_name = %s, email = %s, username = %s, profile_modified_at = NOW()
                WHERE id = %s
            """, (first_name, last_name, email, username, user_id))
            
            conn.commit()
            affected_rows = cursor.rowcount
            
            if affected_rows == 0:
                return {"success": False, "error": "User not found"}
            
            # Return the updated user data
            cursor.execute("SELECT id, first_name, last_name, email, username FROM account WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            
            cursor.close()
            
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
        logger.error(f"Database integrity error in modify_account_profile: {e}")
        if "email" in str(e).lower():
            return {"success": False, "error": "Email address is already registered by another user"}
        elif "username" in str(e).lower():
            return {"success": False, "error": "Username is already taken by another user"}
        else:
            return {"success": False, "error": "Profile update failed due to duplicate data"}
    except mysql.connector.Error as e:
        logger.error(f"Database error in modify_account_profile: {e}")
        return {"success": False, "error": "Server unavailable, please try again later."}
    except Exception as e:
        logger.error(f"Unexpected error in modify_account_profile: {e}")
        return {"success": False, "error": "Server unavailable, please try again later."}

@handle_db_errors(default_return=None)
def modify_account_password(user_id, current_password, new_password):
    """Update user password after verifying current password"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get current password hash
            cursor.execute("SELECT password_hash FROM account WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                return {"success": False, "error": "User not found"}
            
            current_password_hash = user_data[0]
            
            # Verify current password
            from werkzeug.security import check_password_hash
            if not check_password_hash(current_password_hash, current_password):
                return {"success": False, "error": "Current password is incorrect"}
            
            # Hash the new password
            from werkzeug.security import generate_password_hash
            new_password_hash = generate_password_hash(new_password)
            
            # Update password
            cursor.execute("""
                UPDATE account 
                SET password_hash = %s, password_modified_at = NOW()
                WHERE id = %s
            """, (new_password_hash, user_id))
            
            conn.commit()
            affected_rows = cursor.rowcount
            
            cursor.close()
            
            if affected_rows == 0:
                return {"success": False, "error": "Password update failed"}
            
            return {"success": True, "message": "Password updated successfully"}
            
    except mysql.connector.Error as e:
        logger.error(f"Database error in modify_account_password: {e}")
        return {"success": False, "error": "Server unavailable, please try again later."}
    except Exception as e:
        logger.error(f"Unexpected error in modify_account_password: {e}")
        return {"success": False, "error": "Server unavailable, please try again later."}
