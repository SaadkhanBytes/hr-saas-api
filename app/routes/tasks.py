"""
Leave requests route — fully tenant-scoped.
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import LeaveRequest, Employee

router = APIRouter(prefix="/api/leaves", tags=["leaves"])


@router.get("")
async def list_leaves(request: Request, db: AsyncSession = Depends(get_db)):
    """List leave requests for the current organization."""
    org_id = request.state.org_id
    result = await db.execute(
        select(LeaveRequest).where(LeaveRequest.org_id == org_id).order_by(LeaveRequest.created_at.desc())
    )
    leaves = result.scalars().all()

    leave_list = []
    for l in leaves:
        emp_result = await db.execute(select(Employee.name).where(Employee.id == l.employee_id))
        emp_name = emp_result.scalar()
        leave_list.append({
            "id": l.id,
            "org_id": l.org_id,
            "employee_id": l.employee_id,
            "employee_name": emp_name,
            "leave_type": l.leave_type.value,
            "start_date": l.start_date.isoformat(),
            "end_date": l.end_date.isoformat(),
            "reason": l.reason,
            "status": l.status.value,
            "created_at": l.created_at.isoformat(),
        })
    return leave_list


@router.put("/{leave_id}")
async def update_leave_status(leave_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """Approve or reject a leave request (scoped to current org)."""
    org_id = request.state.org_id
    result = await db.execute(
        select(LeaveRequest).where(LeaveRequest.id == leave_id, LeaveRequest.org_id == org_id)
    )
    leave = result.scalar()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    body = await request.json()
    if "status" in body:
        leave.status = body["status"]
    await db.flush()
    return {"message": "Leave updated", "id": leave.id}
