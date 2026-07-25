from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from app.core.config import settings


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Placeholder for JWT token creation.
    Will be fully wired when authentication module is activated.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire.timestamp()})
    
    # Placeholder return string (use PyJWT or python-jose when auth is enabled)
    return f"jwt_mock_token_{to_encode.get('sub', 'anonymous')}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Placeholder password verification."""
    return plain_password == hashed_password


def get_password_hash(password: str) -> str:
    """Placeholder password hashing."""
    return f"hashed_{password}"
