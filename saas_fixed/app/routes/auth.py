"""
Auth routes — login and token generation.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Employee, Organization
from app.schemas import LoginRequest, TokenResponse
from app.auth import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with email + password. Returns JWT with org_id baked in."""
    try:
        result = await db.execute(
            select(Employee).where(Employee.email == body.email.strip().lower())
        )
        employee = result.scalar()

        if not employee:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not employee.password_hash:
            raise HTTPException(status_code=401, detail="Account not activated — no password set")

        if not verify_password(body.password, employee.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        org_result = await db.execute(
            select(Organization).where(Organization.id == employee.org_id)
        )
        org = org_result.scalar()

        token = create_access_token({
            "employee_id": employee.id,
            "org_id": employee.org_id,
            "email": employee.email,
            "role": employee.role.value,
        })

        return TokenResponse(
            access_token=token,
            org_id=employee.org_id,
            org_name=org.name if org else "",
            employee_name=employee.name,
            employee_role=employee.role.value,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Login failed") from exc
