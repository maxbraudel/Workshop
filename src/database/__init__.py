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
    DB_CONFIG,
    logger
)

# Import retrieve functions
from .database_retrieve import (
    get_user_by_id,
    get_user_by_username,
    get_user_by_email,
    validate_session_token,
    get_movies_with_showings_by_date,
    get_showing_by_id,
    get_seats_for_showing,
    get_age_pricing,
    calculate_booking_price,
    get_booking_by_id,
    get_customers_for_booking,
    get_bookings_by_account_id,
    is_showing_expired,
    get_movie_poster,
    get_poster_image_data
)

# Import validation functions
from .database_validate import (
    validate_signup_identifiers,
    validate_signup_passwords,
    validate_signup_data,
    validate_login_data
)

# Import modify functions
from .database_modify import (
    create_session_token,
    invalidate_session_token,
    cleanup_expired_sessions,
    add_account,
    modify_account_profile,
    modify_account_password,
    check_seats_availability,
    create_complete_booking_secure
)

__all__ = [
    # Core database
    'get_db_connection',
    'test_database_connection',
    'handle_db_errors',
    'DB_CONFIG',
    'logger',
    
    # Retrieve functions
    'get_user_by_id',
    'get_user_by_username',
    'get_user_by_email',
    'validate_session_token',
    'get_movies_with_showings_by_date',
    'get_showing_by_id',
    'get_seats_for_showing',
    'get_age_pricing',
    'calculate_booking_price',
    'get_booking_by_id',
    'get_customers_for_booking',
    'get_bookings_by_account_id',
    'is_showing_expired',
    'get_movie_poster',
    'get_poster_image_data',
    
    # Validation functions
    'validate_signup_identifiers',
    'validate_signup_passwords',
    'validate_signup_data',
    'validate_login_data',
    
    # Modify functions
    'create_session_token',
    'invalidate_session_token',
    'cleanup_expired_sessions',
    'add_account',
    'modify_account_profile',
    'modify_account_password',
    'check_seats_availability',
    'create_complete_booking_secure'
]
