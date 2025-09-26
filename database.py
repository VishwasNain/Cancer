import psycopg2
import os
from datetime import datetime
import json

def get_db_connection():
    """Get database connection using environment variables"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("PGHOST", "localhost"),
            database=os.getenv("PGDATABASE", "lung_cancer_db"),
            user=os.getenv("PGUSER", "postgres"),
            password=os.getenv("PGPASSWORD", "password"),
            port=os.getenv("PGPORT", "5432")
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = None
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create images table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medical_images (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                filename VARCHAR(255) NOT NULL,
                image_data BYTEA NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image_type VARCHAR(50),
                file_size INTEGER
            )
        """)
        
        # Create analysis results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id SERIAL PRIMARY KEY,
                image_id INTEGER REFERENCES medical_images(id),
                user_id INTEGER REFERENCES users(id),
                prediction VARCHAR(100) NOT NULL,
                confidence_score FLOAT NOT NULL,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                detailed_results JSON,
                processing_time FLOAT
            )
        """)
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def store_image(user_id, filename, image_data, image_type, file_size):
    """Store medical image in database"""
    conn = get_db_connection()
    cursor = None
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO medical_images (user_id, filename, image_data, image_type, file_size)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (user_id, filename, image_data, image_type, file_size))
        
        result = cursor.fetchone()
        if not result:
            return None
        image_id = result[0]
        conn.commit()
        return image_id
        
    except Exception as e:
        print(f"Error storing image: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def store_analysis_result(image_id, user_id, prediction, confidence_score, detailed_results, processing_time):
    """Store analysis result in database"""
    conn = get_db_connection()
    cursor = None
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analysis_results (image_id, user_id, prediction, confidence_score, detailed_results, processing_time)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (image_id, user_id, prediction, confidence_score, json.dumps(detailed_results), processing_time))
        
        result = cursor.fetchone()
        if not result:
            return None
        result_id = result[0]
        conn.commit()
        return result_id
        
    except Exception as e:
        print(f"Error storing analysis result: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_user_images(user_id):
    """Get all images for a specific user"""
    conn = get_db_connection()
    cursor = None
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mi.id, mi.filename, mi.upload_date, mi.image_type, mi.file_size,
                   ar.prediction, ar.confidence_score, ar.analysis_date
            FROM medical_images mi
            LEFT JOIN analysis_results ar ON mi.id = ar.image_id
            WHERE mi.user_id = %s
            ORDER BY mi.upload_date DESC
        """, (user_id,))
        
        results = cursor.fetchall()
        return results
        
    except Exception as e:
        print(f"Error getting user images: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_all_users():
    """Get all users (admin function)"""
    conn = get_db_connection()
    cursor = None
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, role, created_at
            FROM users
            ORDER BY created_at DESC
        """)
        
        results = cursor.fetchall()
        return results
        
    except Exception as e:
        print(f"Error getting users: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_all_images():
    """Get all images across all users (admin function)"""
    conn = get_db_connection()
    cursor = None
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mi.id, u.username, mi.filename, mi.upload_date, mi.image_type,
                   ar.prediction, ar.confidence_score, ar.analysis_date
            FROM medical_images mi
            JOIN users u ON mi.user_id = u.id
            LEFT JOIN analysis_results ar ON mi.id = ar.image_id
            ORDER BY mi.upload_date DESC
        """)
        
        results = cursor.fetchall()
        return results
        
    except Exception as e:
        print(f"Error getting all images: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_image_data(image_id):
    """Get image data by ID"""
    conn = get_db_connection()
    cursor = None
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT image_data, filename, image_type
            FROM medical_images
            WHERE id = %s
        """, (image_id,))
        
        result = cursor.fetchone()
        return result
        
    except Exception as e:
        print(f"Error getting image data: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
