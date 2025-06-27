import mysql.connector
import logging
from contextlib import contextmanager
from mysql.connector import pooling
from ..config import get_config

# Get configuration
config = get_config()

# Configure logging for database errors
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def handle_db_errors(default_return=None):
    """Decorator to handle database errors consistently"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except mysql.connector.Error as e:
                logger.error(f"Database error in {func.__name__}: {e}")
                return default_return
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator

# Database connection configuration from config class
DB_CONFIG = config.get_database_config()
POOL_CONFIG = config.get_pool_config()

# Create connection pool
try:
    connection_pool = pooling.MySQLConnectionPool(
        **DB_CONFIG,
        **POOL_CONFIG
    )
    logger.info("Database connection pool created successfully")
except mysql.connector.Error as e:
    logger.error(f"Error creating connection pool: {e}")
    connection_pool = None

@contextmanager
def get_db_connection():
    """Get a database connection from the pool with context manager"""
    if connection_pool is None:
        # Fallback to direct connection if pool failed
        conn = mysql.connector.connect(**DB_CONFIG)
    else:
        conn = connection_pool.get_connection()
    
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction error: {e}")
        raise
    finally:
        conn.close()

def test_database_connection():
    """Test database connection and return account count"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM account")
            count = cursor.fetchone()[0]
            print(f"✓ Database connected successfully. Found {count} accounts.")
            cursor.close()
            return True
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False