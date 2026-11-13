from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta
from uuid import uuid4

from app.db.session import get_db
from app.db.models import User, Organization, OrganizationRole, UserStatus
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.auth import get_current_user, TokenData
from app.core.config import settings
from app.audit.service import get_audit_service, AuditService

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    org_name: Optional[str] = None  # For first user creating org


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    role: str
    org_id: str
    org_name: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Register a new user and optionally create an organization."""
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()

    correlation_id = getattr(req.state, "correlation_id", None)

    if existing_user:
        await audit_service.log_event(
            org_id=existing_user.org_id,
            actor_id=existing_user.id,
            action="user.register",
            resource_type="user",
            resource_id=existing_user.id,
            outcome="failure",
            correlation_id=correlation_id,
            metadata={"email": request.email, "reason": "email_already_registered"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create organization if this is the first user
    org = None
    if request.org_name:
        org = Organization(name=request.org_name)
        db.add(org)
        await db.flush()
    else:
        # For demo purposes, create a default org
        org = Organization(name="Default Organization")
        db.add(org)
        await db.flush()

    # Create user with admin role for first user in org
    user = User(
        id=uuid4(),
        org_id=org.id,
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        role=OrganizationRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    await db.commit()

    # Audit log for successful registration
    await audit_service.log_event(
        org_id=org.id,
        actor_id=user.id,
        action="user.register",
        resource_type="user",
        resource_id=user.id,
        outcome="success",
        correlation_id=correlation_id,
        metadata={"email": request.email, "org_name": org.name},
    )

    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "org_id": str(org.id), "roles": [user.role.value]},
        expires_delta=timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "org_id": str(org.id), "roles": [user.role.value]},
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Authenticate user and return tokens."""
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    correlation_id = getattr(req.state, "correlation_id", None)

    if not user or not verify_password(request.password, user.hashed_password):
        await audit_service.log_event(
            org_id=user.org_id if user else None,
            actor_id=user.id if user else None,
            action="user.login",
            resource_type="user",
            resource_id=user.id if user else None,
            outcome="failure",
            correlation_id=correlation_id,
            metadata={"email": request.email, "reason": "invalid_credentials"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != UserStatus.ACTIVE:
        await audit_service.log_event(
            org_id=user.org_id,
            actor_id=user.id,
            action="user.login",
            resource_type="user",
            resource_id=user.id,
            outcome="failure",
            correlation_id=correlation_id,
            metadata={"email": request.email, "reason": "account_revoked"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is revoked",
        )

    # Get organization name
    org_result = await db.execute(select(Organization).where(Organization.id == user.org_id))
    org = org_result.scalar_one()

    # Audit log for successful login
    await audit_service.log_event(
        org_id=org.id,
        actor_id=user.id,
        action="user.login",
        resource_type="user",
        resource_id=user.id,
        outcome="success",
        correlation_id=correlation_id,
        metadata={"email": request.email},
    )

    access_token = create_access_token(
        data={"sub": str(user.id), "org_id": str(org.id), "roles": [user.role.value]},
        expires_delta=timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "org_id": str(org.id), "roles": [user.role.value]},
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Refresh access token using refresh token."""
    payload = decode_token(request.refresh_token)
    correlation_id = getattr(req.state, "correlation_id", None)

    if not payload or payload.get("type") != "refresh":
        await audit_service.log_event(
            org_id=payload.get("org_id") if payload else None,
            actor_id=payload.get("sub") if payload else None,
            action="user.token_refresh",
            resource_type="token",
            resource_id=None,
            outcome="failure",
            correlation_id=correlation_id,
            metadata={"reason": "invalid_refresh_token"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    org_id = payload.get("org_id")
    roles = payload.get("roles", [])

    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or user.status != UserStatus.ACTIVE:
        await audit_service.log_event(
            org_id=org_id,
            actor_id=user_id,
            action="user.token_refresh",
            resource_type="token",
            resource_id=None,
            outcome="failure",
            correlation_id=correlation_id,
            metadata={"reason": "user_not_found_or_inactive"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Audit log for successful token refresh
    await audit_service.log_event(
        org_id=org_id,
        actor_id=user_id,
        action="user.token_refresh",
        resource_type="token",
        resource_id=None,
        outcome="success",
        correlation_id=correlation_id,
        metadata={},
    )

    access_token = create_access_token(
        data={"sub": str(user.id), "org_id": str(org_id), "roles": roles},
        expires_delta=timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "org_id": str(org_id), "roles": roles},
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user info with organization."""
    result = await db.execute(select(User).where(User.id == current_user.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    org_result = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = org_result.scalar_one_or_none()

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        org_id=str(user.org_id),
        org_name=org.name if org else "Unknown",
    )


@router.post("/logout")
async def logout(
    req: Request,
    current_user: TokenData = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Logout endpoint (client should discard tokens)."""
    correlation_id = getattr(req.state, "correlation_id", None)

    await audit_service.log_event(
        org_id=current_user.org_id,
        actor_id=current_user.user_id,
        action="user.logout",
        resource_type="user",
        resource_id=current_user.user_id,
        outcome="success",
        correlation_id=correlation_id,
        metadata={},
    )

    return {"message": "Logged out successfully"}