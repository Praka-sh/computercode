from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.core.security import decode_token
from app.core.config import settings

security = HTTPBearer(auto_error=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


class TokenData:
    def __init__(self, user_id: str, org_id: str, roles: list[str]):
        self.user_id = user_id
        self.org_id = org_id
        self.roles = roles


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> TokenData:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    org_id = payload.get("org_id")
    roles = payload.get("roles", [])

    if not user_id or not org_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
        )

    return TokenData(user_id=user_id, org_id=org_id, roles=roles)


async def get_current_org(
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> str:
    """Get the organization ID from the authenticated user's token.
    Server-side derivation - never trust client-provided org_id."""
    return current_user.org_id


def require_role(*required_roles: str):
    """Dependency that requires specific roles."""
    async def role_checker(current_user: Annotated[TokenData, Depends(get_current_user)]) -> TokenData:
        if not any(role in current_user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {required_roles}",
            )
        return current_user
    return role_checker