import mysql.connector
import logging

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

@handle_db_errors(default_return=([], []))
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
    finally:
        cursor.close()
        conn.close()