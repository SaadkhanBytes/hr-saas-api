"""
app/routes/orgs.py — Organization registration and listing.
POST /api/organizations/register — public, creates org + admin employee, returns JWT
GET  /api/organizations           — auth required, lists all organizations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, get_current_user, hash_password
from app.database import get_db
from app.models import Employee, EmployeeRole, EmployeeStatus, Organization, Department
from app.schemas import OrgRegisterRequest, OrgResponse, TokenResponse

router = APIRouter(prefix="/api/organizations", tags=["Organizations"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_organization(data: OrgRegisterRequest, db: AsyncSession = Depends(get_db)):
    # Create organization
    org = Organization(
        name=data.name,
        slug=data.slug.lower().strip(),
        plan=data.plan,
        industry=data.industry,
    )
    db.add(org)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Organization slug already exists")

    # Create admin employee
    admin = Employee(
        org_id=org.id,
        name=data.admin_name,
        email=data.admin_email.lower().strip(),
        password_hash=hash_password(data.admin_password),
        department=Department.operations,
        role=EmployeeRole.cxo,
        status=EmployeeStatus.active,
    )
    db.add(admin)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists in this organization")

    token = create_access_token({
        "employee_id": admin.id,
        "org_id": org.id,
        "email": admin.email,
        "role": admin.role.value,
    })

    return TokenResponse(
        access_token=token,
        employee={
            "id": admin.id,
            "org_id": org.id,
            "name": admin.name,
            "email": admin.email,
            "role": admin.role.value,
            "department": admin.department.value,
            "org_name": org.name,
            "org_slug": org.slug,
        },
    )


@router.get("", response_model=list[OrgResponse])
async def list_organizations(
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all organizations. Requires authentication."""
    result = await db.execute(select(Organization).order_by(Organization.created_at.desc()))
    orgs = result.scalars().all()
    return orgs
