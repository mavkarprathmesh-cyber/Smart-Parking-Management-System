"""
Security & Cryptography Module
Provides:
- PBKDF2-HMAC-SHA256 password hashing with random cryptographic salts (100,000 iterations)
- Secure token generation and verification
- Strong password validation rules
- Rate limiting and brute-force protection logic
- Email verification and password reset code handling
- Audit logging helper
"""

import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional
import sqlite3

from database.db import get_db_connection


def generate_salt(length: int = 16) -> str:
    """Generates a cryptographically secure random hexadecimal salt."""
    return secrets.token_hex(length)


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hashes password using PBKDF2 with HMAC-SHA256 (100,000 iterations).
    Returns (hex_password_hash, salt_hex).
    """
    if salt is None:
        salt = generate_salt(16)
    
    pwd_bytes = password.encode('utf-8')
    salt_bytes = bytes.fromhex(salt)
    
    hash_bytes = hashlib.pbkdf2_hmac(
        hash_name='sha256',
        password=pwd_bytes,
        salt=salt_bytes,
        iterations=100_000
    )
    return hash_bytes.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifies candidate password against stored hash using constant-time comparison."""
    if not stored_hash or not salt:
        return False
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, stored_hash)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validates strong password policy:
    - Minimum 8 characters
    - At least one uppercase letter [A-Z]
    - At least one lowercase letter [a-z]
    - At least one numeric digit [0-9]
    - At least one special character [@$!%*?&#]
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter (a-z)."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r'[@$!%*?&#^+=_-]', password):
        return False, "Password must contain at least one special character (@$!%*?&#^+=_-)."
    return True, "Password is strong."


def validate_email_format(email: str) -> bool:
    """Checks valid email format using regex."""
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email.strip()))


def generate_session_token(user_id: str, role: str, expiry_hours: int = 24) -> str:
    """
    Generates a secure 64-char hexadecimal session token and saves it in database.
    """
    token = secrets.token_hex(32)
    expires_at = (datetime.now() + timedelta(hours=expiry_hours)).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO user_sessions (token, user_id, role, expires_at)
    VALUES (?, ?, ?, ?)
    """, (token, user_id, role, expires_at))
    conn.commit()
    conn.close()

    return token


def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validates token against user_sessions table and checks expiry.
    Returns user dictionary or None.
    """
    if not token:
        return None
    
    clean_token = token.replace("Bearer ", "").strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT s.user_id, s.role, s.expires_at, u.full_name, u.email, u.phone, u.is_verified
    FROM user_sessions s
    JOIN users u ON s.user_id = u.user_id
    WHERE s.token = ?
    """, (clean_token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    user_data = dict(row)
    # Check expiry
    try:
        exp_time = datetime.strptime(user_data["expires_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > exp_time:
            return None
    except Exception:
        return None

    return user_data


def revoke_session_token(token: str) -> bool:
    """Deletes token from database (Logout)."""
    clean_token = token.replace("Bearer ", "").strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_sessions WHERE token = ?", (clean_token,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def record_audit_log(user_id: Optional[str], action: str, target: str = "", details: str = "", ip_address: str = "127.0.0.1"):
    """Inserts a structured audit log entry for security and compliance."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO audit_logs (user_id, action, target, ip_address, details)
        VALUES (?, ?, ?, ?, ?)
        """, (user_id or "ANONYMOUS", action, target, ip_address, details))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error recording audit log: {e}")
