"""
Organizations route — public (no tenant context needed).
Lists all orgs for the org switcher UI.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Organization

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


@router.get("")
async def list_organizations(db: AsyncSession = Depends(get_db)):
    """List all organizations (used by the org switcher)."""
    result = await db.execute(
        select(Organization).order_by(Organization.name)
    )
    orgs = result.scalars().all()
    return [
        {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "plan": org.plan.value,
            "created_at": org.created_at.isoformat(),
        }
        for org in orgs
    ]
