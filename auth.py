import hashlib
import secrets
import sqlite3
from typing import Optional, Dict

def hash_password(password: str, salt: str = None) -> tuple:
    """Hash password using PBKDF2 with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Use PBKDF2 with SHA256
    password_hash = hashlib.pbkdf2_hmac('sha256', 
                                      password.encode('utf-8'), 
                                      salt.encode('utf-8'), 
                                      100000)  # 100,000 iterations
    
    return password_hash.hex(), salt

def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verify password against hash"""
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == password_hash

def register_user(username: str, email: str, password: str) -> bool:
    """Register a new user"""
    conn = sqlite3.connect('finai.db')
    cursor = conn.cursor()
    
    try:
        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return False
        
        # Hash password
        password_hash, salt = hash_password(password)
        
        # Insert new user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, salt, profile_complete)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, password_hash, salt, False))
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user login"""
    conn = sqlite3.connect('finai.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, username, email, password_hash, salt, profile_complete
            FROM users WHERE username = ?
        """, (username,))
        
        user_data = cursor.fetchone()
        
        if user_data and verify_password(password, user_data[3], user_data[4]):
            return {
                'id': user_data[0],
                'username': user_data[1],
                'email': user_data[2],
                'profile_complete': user_data[5]
            }
        
        return None
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def update_user_profile_status(user_id: int, complete: bool = True):
    """Update user profile completion status"""
    conn = sqlite3.connect('finai.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE users SET profile_complete = ? WHERE id = ?
        """, (complete, user_id))
        
        conn.commit()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()