"""
app/routes/auth.py — Authentication endpoints.
POST /api/auth/login            — public, returns JWT (rate-limited 10/min)
POST /api/auth/forgot-password  — public, initiates password reset (rate-limited 5/hr)
POST /api/auth/reset-password   — public, completes password reset (rate-limited 10/hr)
"""
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import Employee, Organization, PasswordResetToken
from app.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    TokenResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])

from app.limiter import limiter


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate a user and return a JWT access token."""
    result = await db.execute(
        select(Employee).where(Employee.email == data.email.lower().strip())
    )
    employee = result.scalars().first()

    if not employee or not verify_password(data.password, employee.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    # Fetch org for response
    org_result = await db.execute(select(Organization).where(Organization.id == employee.org_id))
    org = org_result.scalars().first()

    token = create_access_token({
        "employee_id": employee.id,
        "org_id": employee.org_id,
        "email": employee.email,
        "role": employee.role.value,
    })

    return TokenResponse(
        access_token=token,
        employee={
            "id": employee.id,
            "org_id": employee.org_id,
            "name": employee.name,
            "email": employee.email,
            "role": employee.role.value,
            "department": employee.department.value,
            "org_name": org.name if org else "",
            "org_slug": org.slug if org else "",
        },
    )


@router.post("/forgot-password")
@limiter.limit("5/hour")
async def forgot_password(request: Request, data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Initiate a password reset. Always returns 200 to prevent user enumeration."""
    result = await db.execute(
        select(Employee).where(Employee.email == data.email.lower().strip())
    )
    employee = result.scalars().first()

    if employee:
        # Invalidate all existing unused tokens for this employee
        await db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.employee_id == employee.id,
                PasswordResetToken.used == False,  # noqa: E712
            )
            .values(used=True)
        )

        # Generate a secure token
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        reset_token = PasswordResetToken(
            employee_id=employee.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        db.add(reset_token)
        await db.flush()

        # TODO: Replace this with real email sending when an email provider is configured.
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        reset_url = f"{frontend_url}/reset-password?token={token}"
        print(f"[DEV] Password reset URL: {reset_url}")

    return {"message": "If that email exists, a reset link was sent"}


@router.post("/reset-password")
@limiter.limit("10/hour")
async def reset_password(request: Request, data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Complete a password reset using a valid token."""
    token_hash = hashlib.sha256(data.token.encode()).hexdigest()

    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used == False,  # noqa: E712
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
    )
    reset_token = result.scalars().first()

    if not reset_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    # Update employee password
    emp_result = await db.execute(
        select(Employee).where(Employee.id == reset_token.employee_id)
    )
    employee = emp_result.scalars().first()

    if not employee:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    employee.password_hash = hash_password(data.new_password)

    # Mark token as used
    reset_token.used = True

    await db.flush()
    await db.refresh(employee)
    await db.refresh(reset_token)

    return {"message": "Password reset successfully"}
