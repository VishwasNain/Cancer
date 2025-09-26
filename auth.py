import hashlib
import psycopg2
from database import get_db_connection

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, email, password, role='user'):
    """Create a new user"""
    conn = get_db_connection()
    cursor = None
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        password_hash = hash_password(password)
        
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
        """, (username, email, password_hash, role))
        
        conn.commit()
        return True
        
    except psycopg2.IntegrityError:
        # Username or email already exists
        return False
    except Exception as e:
        print(f"Error creating user: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def authenticate_user(username, password):
    """Authenticate user and return user data"""
    conn = get_db_connection()
    cursor = None
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        password_hash = hash_password(password)
        
        cursor.execute("""
            SELECT id, username, email, role
            FROM users
            WHERE username = %s AND password_hash = %s
        """, (username, password_hash))
        
        user_data = cursor.fetchone()
        
        if user_data:
            return {
                'id': user_data[0],
                'username': user_data[1],
                'email': user_data[2],
                'role': user_data[3]
            }
        return None
        
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_user_role(user_id):
    """Get user role by ID"""
    conn = get_db_connection()
    cursor = None
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
        
    except Exception as e:
        print(f"Error getting user role: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
