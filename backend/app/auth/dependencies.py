from typing import Optional
from fastapi import Depends, HTTPException, status
from app.core.config import settings
from app.users.schemas import UserResponse


async def get_current_user() -> Optional[UserResponse]:
    """
    FastAPI dependency placeholder for user authentication.
    When ENABLE_AUTH is False, returns a system default user representation.
    """
    if not settings.ENABLE_AUTH:
        # Auth disabled for MVP - return default system context
        return UserResponse(
            id="sys_default_user",
            email="admin@aiinvoicereader.local",
            full_name="System Default User",
            is_active=True,
            is_superuser=True,
            created_at="2026-01-01T00:00:00Z",
        )
    
    # Future activation: Extract token from Authorization header and decode
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )
