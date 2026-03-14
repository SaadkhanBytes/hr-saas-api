"""
Leave requests route — tenant-scoped, role-gated for approvals, paginated.
"""

from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import LeaveRequest, Employee, ADMIN_ROLES
from app.schemas import LeaveCreate, LeaveUpdateStatus
from app.auth import get_current_user

router = APIRouter(prefix="/api/leaves", tags=["leaves"])


@router.get("")
async def list_leaves(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _user: Employee = Depends(get_current_user),
    status: str = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    """List leave requests — paginated, filterable by status."""
    org_id = request.state.org_id
    try:
        q = (
            select(LeaveRequest, Employee.name)
            .join(Employee, LeaveRequest.employee_id == Employee.id)
            .where(LeaveRequest.org_id == org_id)
        )
        if status:
            q = q.where(LeaveRequest.status == status)
        q = q.order_by(LeaveRequest.created_at.desc())
        q = q.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(q)
        rows = result.all()

        return [
            {
                "id": lr.id,
                "org_id": lr.org_id,
                "employee_id": lr.employee_id,
                "employee_name": emp_name,
                "leave_type": lr.leave_type.value,
                "start_date": lr.start_date.isoformat(),
                "end_date": lr.end_date.isoformat(),
                "reason": lr.reason,
                "status": lr.status.value,
                "created_at": lr.created_at.isoformat(),
            }
            for lr, emp_name in rows
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch leave requests") from exc


@router.post("", status_code=201)
async def create_leave(
    body: LeaveCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Employee = Depends(get_current_user),
):
    """Submit a leave request."""
    org_id = request.state.org_id
    try:
        # Verify the employee belongs to this org
        result = await db.execute(
            select(Employee).where(Employee.id == body.employee_id, Employee.org_id == org_id)
        )
        if not result.scalar():
            raise HTTPException(status_code=404, detail="Employee not found in this organization")

        lr = LeaveRequest(
            org_id=org_id,
            employee_id=body.employee_id,
            leave_type=body.leave_type,
            start_date=body.start_date,
            end_date=body.end_date,
            reason=body.reason,
        )
        db.add(lr)
        await db.flush()
        return {"id": lr.id, "status": lr.status.value, "message": "Leave request submitted"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to create leave request") from exc


@router.put("/{leave_id}")
async def update_leave_status(
    leave_id: int,
    body: LeaveUpdateStatus,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Employee = Depends(get_current_user),
):
    """Approve or reject a leave request — admin roles only."""
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Only managers and above can approve or reject leave requests")

    org_id = request.state.org_id
    try:
        result = await db.execute(
            select(LeaveRequest).where(LeaveRequest.id == leave_id, LeaveRequest.org_id == org_id)
        )
        leave = result.scalar()
        if not leave:
            raise HTTPException(status_code=404, detail="Leave request not found")

        leave.status = body.status
        await db.flush()
        return {"message": "Leave updated", "id": leave.id, "status": body.status}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to update leave request") from exc
