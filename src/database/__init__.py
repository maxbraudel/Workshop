"""
Database package for the Cinema application.
This package provides database connectivity and operations split into modules:

- database: Core database connection and utilities
- database_retrieve: Functions to retrieve data from the database
- database_validate: Functions to validate data according to database rules
- database_modify: Functions to modify/add data to the database
"""

# Import core database functionality
from .database import (
    get_db_connection,
    test_database_connection,
    handle_db_errors,
    analyze_movie_table,
    DB_CONFIG,
    logger
)

# Import retrieve functions
from .database_retrieve import (
    get_user_by_username,
    get_user_by_email,
    validate_session_token,
    get_user_sessions,
    get_all_movies
)

# Import validation functions
from .database_validate import (
    validate_signup_identifiers,
    validate_signup_passwords,
    validate_signup_data,
    validate_login_data,
    authenticate_user
)

# Import modify functions
from .database_modify import (
    create_session_token,
    invalidate_session_token,
    create_user,
    cleanup_expired_sessions,
    add_account
)

__all__ = [
    # Core database
    'get_db_connection',
    'test_database_connection',
    'handle_db_errors',
    'analyze_movie_table',
    'DB_CONFIG',
    'logger',
    
    # Retrieve functions
    'get_user_by_username',
    'get_user_by_email',
    'validate_session_token',
    'get_user_sessions',
    'get_all_movies',
    
    # Validation functions
    'validate_signup_identifiers',
    'validate_signup_passwords',
    'validate_signup_data',
    'validate_login_data',
    'authenticate_user',
    
    # Modify functions
    'create_session_token',
    'invalidate_session_token',
    'create_user',
    'cleanup_expired_sessions',
    'add_account'
]
