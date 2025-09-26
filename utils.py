import os
import hashlib
import base64
import json
from datetime import datetime, timedelta
import numpy as np
import cv2
from PIL import Image
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_session_token():
    """Generate a secure session token"""
    return hashlib.sha256(os.urandom(32)).hexdigest()

def validate_image_format(uploaded_file):
    """Validate if uploaded file is a valid image format"""
    valid_formats = ['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif']
    
    if uploaded_file.name:
        file_extension = uploaded_file.name.lower().split('.')[-1]
        return file_extension in valid_formats
    
    return False

def sanitize_filename(filename):
    """Sanitize filename to prevent security issues"""
    # Remove or replace dangerous characters
    import re
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename[:255]  # Limit length
    return filename

def calculate_file_hash(file_data):
    """Calculate SHA256 hash of file data"""
    return hashlib.sha256(file_data).hexdigest()

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def validate_confidence_score(score):
    """Validate confidence score is within valid range"""
    try:
        score = float(score)
        return 0.0 <= score <= 1.0
    except (ValueError, TypeError):
        return False

def format_datetime(dt):
    """Format datetime for display"""
    if dt is None:
        return "N/A"
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_relative_time(dt):
    """Get relative time string (e.g., '2 hours ago')"""
    if dt is None:
        return "N/A"
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt
    
    now = datetime.now()
    if dt.tzinfo:
        from datetime import timezone
        now = now.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

def validate_email(email):
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username format"""
    import re
    # Username should be 3-50 characters, alphanumeric and underscore only
    pattern = r'^[a-zA-Z0-9_]{3,50}$'
    return re.match(pattern, username) is not None

def validate_password_strength(password):
    """Validate password strength"""
    errors = []
    
    if len(password) < 6:
        errors.append("Password must be at least 6 characters long")
    
    if len(password) > 128:
        errors.append("Password must be less than 128 characters")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    return len(errors) == 0, errors

def log_user_activity(user_id, activity, details=None):
    """Log user activity for audit purposes"""
    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'activity': activity,
            'details': details
        }
        logger.info(f"User Activity: {json.dumps(log_entry)}")
    except Exception as e:
        logger.error(f"Failed to log user activity: {e}")

def safe_json_loads(json_string, default=None):
    """Safely load JSON string with default fallback"""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}

def safe_json_dumps(obj, default=None):
    """Safely dump object to JSON string"""
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return json.dumps(default if default is not None else {})

def create_error_response(message, code=None):
    """Create standardized error response"""
    return {
        'success': False,
        'error': message,
        'code': code,
        'timestamp': datetime.now().isoformat()
    }

def create_success_response(data=None, message=None):
    """Create standardized success response"""
    return {
        'success': True,
        'data': data,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }

def mask_sensitive_data(data, fields_to_mask=['password', 'password_hash', 'api_key', 'secret']):
    """Mask sensitive fields in data for logging"""
    if isinstance(data, dict):
        masked = data.copy()
        for field in fields_to_mask:
            if field in masked:
                masked[field] = '***MASKED***'
        return masked
    return data

def get_client_ip():
    """Get client IP address (for audit logging)"""
    # This would be implemented based on the deployment environment
    # For now, return a placeholder
    return "127.0.0.1"

def rate_limit_check(user_id, action, max_attempts=5, window_minutes=60):
    """Check if user has exceeded rate limits"""
    # In a production environment, this would use Redis or database
    # For now, return True (no rate limiting)
    return True

def cleanup_old_files(days_old=30):
    """Clean up old temporary files"""
    try:
        # This would implement cleanup logic for old files
        # For now, just log the attempt
        logger.info(f"Cleanup requested for files older than {days_old} days")
        return True
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return False

def validate_database_connection():
    """Validate database connection is working"""
    try:
        from database import get_db_connection
        conn = get_db_connection()
        if conn:
            conn.close()
            return True
        return False
    except Exception as e:
        logger.error(f"Database connection validation failed: {e}")
        return False

def generate_report_filename(user_id, report_type):
    """Generate standardized report filename"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{report_type}_user{user_id}_{timestamp}.pdf"

def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj

class ConfigManager:
    """Manage application configuration"""
    
    @staticmethod
    def get_config(key, default=None):
        """Get configuration value from environment"""
        return os.getenv(key, default)
    
    @staticmethod
    def get_database_url():
        """Get database URL from environment"""
        return os.getenv("DATABASE_URL")
    
    @staticmethod
    def get_session_secret():
        """Get session secret from environment"""
        return os.getenv("SESSION_SECRET", "default_secret_change_in_production")
    
    @staticmethod
    def is_development():
        """Check if running in development mode"""
        return os.getenv("ENVIRONMENT", "production").lower() == "development"
    
    @staticmethod
    def get_max_file_size():
        """Get maximum file size for uploads"""
        return int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB default
