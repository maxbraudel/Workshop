import mysql.connector
import re
from werkzeug.security import check_password_hash
from .database import get_db_connection, logger
from .database_retrieve import get_user_by_email

def validate_signup_identifiers(first_name, last_name, email, username, birthday=None):
    """Validate signup form identifiers (first name, last name, email, username, birthday)"""
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
    
    if username and not re.match("^[a-zA-Z0-9_]+$", username):
        errors.append("Username can only contain letters, numbers, and underscores")
    
    # Birthday validation
    if birthday:
        try:
            from datetime import datetime, date
            birth_date = datetime.strptime(birthday, '%Y-%m-%d').date()
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            if age < 13:
                errors.append("You must be at least 13 years old to create an account")
            elif age > 120:
                errors.append("Please enter a valid birth date")
        except ValueError:
            errors.append("Please enter a valid birth date")
    
    # Check database constraints if basic validation passes
    if not errors:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if email already exists
                cursor.execute("SELECT id FROM account WHERE email = %s", (email,))
                if cursor.fetchone():
                    errors.append("Email address is already registered")
                
                # Check if username already exists
                cursor.execute("SELECT id FROM account WHERE username = %s", (username,))
                if cursor.fetchone():
                    errors.append("Username is already taken")
                
                cursor.close()
                    
        except mysql.connector.Error as e:
            logger.error(f"Database error in validate_signup_identifiers: {e}")
            errors.append("Server unavailable, please try again later")
        except Exception as e:
            logger.error(f"Unexpected error in validate_signup_identifiers: {e}")
            errors.append("Server unavailable, please try again later")
    
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

def validate_signup_data(first_name, last_name, email, username, password, confirm_password, birthday=None):
    """Validate complete signup form data (for backward compatibility)"""
    errors = []
    
    # Validate identifiers
    identifier_errors = validate_signup_identifiers(first_name, last_name, email, username, birthday)
    errors.extend(identifier_errors)
    
    # Validate passwords
    password_errors = validate_signup_passwords(password, confirm_password)
    errors.extend(password_errors)
    
    return errors

def validate_login_data(email, password):
    """
    Validate login credentials and return specific error information
    Returns a dictionary with 'success', 'user', and 'error' keys
    """
    # Basic input validation
    if not email or not email.strip():
        return {"success": False, "error": "Please enter your email address", "user": None}
    
    if not password or not password.strip():
        return {"success": False, "error": "Please enter your password", "user": None}
    
    # Try to get user from database
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Check if email exists in database
            cursor.execute("SELECT id, email, username, password_hash FROM account WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if not user:
                # Email not found in database
                return {"success": False, "error": "No account found with this email address", "user": None}
            
            # Email exists, check password
            if check_password_hash(user['password_hash'], password):
                # Password is correct
                return {"success": True, "error": None, "user": user}
            else:
                # Password is incorrect
                return {"success": False, "error": "Incorrect password", "user": None}
            
    except mysql.connector.Error as e:
        # Database connection or query error
        logger.error(f"Database error in validate_login_data: {e}")
        return {"success": False, "error": "Server unavailable, please try again later", "user": None}
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in validate_login_data: {e}")
        return {"success": False, "error": "Server unavailable, please try again later", "user": None}
    finally:
        if 'cursor' in locals():
            cursor.close()
