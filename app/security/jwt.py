"""
JWT Token Handling
Access and Refresh Token creation and validation
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt

from app.core.config import settings


class TokenType:
    """Token type constants"""
    ACCESS = "access"
    REFRESH = "refresh"


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT access token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "type": TokenType.ACCESS,
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token
    
    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "type": TokenType.REFRESH,
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Decoded payload dictionary or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify an access token and return payload
    
    Args:
        token: JWT access token string
        
    Returns:
        Decoded payload if valid access token, None otherwise
    """
    payload = decode_token(token)
    if payload and payload.get("type") == TokenType.ACCESS:
        return payload
    return None


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a refresh token and return payload
    
    Args:
        token: JWT refresh token string
        
    Returns:
        Decoded payload if valid refresh token, None otherwise
    """
    payload = decode_token(token)
    if payload and payload.get("type") == TokenType.REFRESH:
        return payload
    return None


def create_tokens(user_id: int, email: str, role: str) -> Dict[str, str]:
    """
    Create both access and refresh tokens for a user
    
    Args:
        user_id: User's database ID
        email: User's email address
        role: User's role name
        
    Returns:
        Dictionary with access_token and refresh_token
    """
    token_data = {
        "sub": str(user_id),
        "email": email,
        "role": role
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
