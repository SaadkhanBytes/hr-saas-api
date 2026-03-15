"""
Organizations route — public (no tenant context needed).
Handles org registration and listing.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Organization, Employee, Department, EmployeeRole
from app.schemas import RegisterRequest
from app.auth import hash_password, create_access_token

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


@router.post("/register", status_code=201)
async def register_organization(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new organization + admin user in one step.
    Returns a JWT so the user is logged in immediately after signup.
    """
    try:
        org = Organization(name=body.org_name, slug=body.org_slug, industry=body.industry)
        db.add(org)
        await db.flush()

        admin = Employee(
            org_id=org.id,
            name=body.admin_name,
            email=body.email,
            password_hash=hash_password(body.password),
            department=Department.HR,
            role=EmployeeRole.CXO,
            position="Admin",
        )
        db.add(admin)
        await db.flush()

        token = create_access_token({
            "employee_id": admin.id,
            "org_id": org.id,
            "email": admin.email,
            "role": admin.role.value,
        })

        return {
            "access_token": token,
            "token_type": "bearer",
            "org_id": org.id,
            "org_name": org.name,
            "employee_name": admin.name,
            "employee_role": admin.role.value,
            "message": f"Organization '{org.name}' created successfully!",
        }
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Organization slug or email already exists")
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Registration failed") from exc


@router.get("")
async def list_organizations(db: AsyncSession = Depends(get_db)):
    """List all organizations (used by the org switcher)."""
    result = await db.execute(select(Organization).order_by(Organization.name))
    orgs = result.scalars().all()
    return [
        {"id": org.id, "name": org.name, "slug": org.slug, "plan": org.plan.value, "created_at": org.created_at.isoformat()}
        for org in orgs
    ]
