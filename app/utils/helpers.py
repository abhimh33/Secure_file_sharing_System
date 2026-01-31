"""
Utility Functions
Common helper functions used across the application
"""

import uuid
import hashlib
from datetime import datetime
from typing import Optional


def generate_uuid() -> str:
    """Generate a unique UUID string"""
    return uuid.uuid4().hex


def generate_file_hash(content: bytes) -> str:
    """Generate SHA-256 hash of file content"""
    return hashlib.sha256(content).hexdigest()


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove unsafe characters"""
    # Remove path separators and other unsafe characters
    unsafe_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    result = filename
    for char in unsafe_chars:
        result = result.replace(char, '_')
    return result


def is_valid_content_type(content_type: str, allowed_types: Optional[list] = None) -> bool:
    """Check if content type is allowed"""
    if allowed_types is None:
        return True  # Allow all types
    return content_type in allowed_types


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to ISO string"""
    if dt:
        return dt.isoformat()
    return None


def parse_datetime(dt_string: str) -> Optional[datetime]:
    """Parse ISO datetime string to datetime object"""
    try:
        return datetime.fromisoformat(dt_string)
    except (ValueError, TypeError):
        return None
