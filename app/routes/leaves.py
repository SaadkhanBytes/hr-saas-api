"""
app/routes/leaves.py — Leave request management.
GET  /api/leaves      — auth, paginated, status filter
POST /api/leaves      — auth, submit leave request
PUT  /api/leaves/{id} — auth + admin only, approve/reject
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import ADMIN_ROLES, Employee, LeaveRequest
from app.schemas import LeaveCreateRequest, LeaveResponse, LeaveUpdateRequest

router = APIRouter(prefix="/api/leaves", tags=["Leaves"])


@router.get("", response_model=list[LeaveResponse])
async def list_leaves(
    request: Request,
    leave_status: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List leave requests. Admins see all org leaves; non-admins see only their own."""
    org_id = request.state.org_id

    query = (
        select(LeaveRequest, Employee.name.label("employee_name"))
        .join(Employee, LeaveRequest.employee_id == Employee.id)
        .where(LeaveRequest.org_id == org_id)
    )

    # Non-admin users only see their own leave requests
    if current_user.role not in ADMIN_ROLES:
        query = query.where(LeaveRequest.employee_id == current_user.id)

    if leave_status:
        query = query.where(LeaveRequest.status == leave_status)

    query = query.order_by(LeaveRequest.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    return [
        LeaveResponse(
            id=lr.id,
            org_id=lr.org_id,
            employee_id=lr.employee_id,
            employee_name=emp_name,
            leave_type=lr.leave_type,
            start_date=lr.start_date,
            end_date=lr.end_date,
            reason=lr.reason,
            status=lr.status,
            created_at=lr.created_at,
        )
        for lr, emp_name in rows
    ]


@router.post("", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
async def create_leave(
    request: Request,
    data: LeaveCreateRequest,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a new leave request for the current user."""
    org_id = request.state.org_id

    # Verify the employee belongs to the current org
    if current_user.org_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    leave = LeaveRequest(
        org_id=org_id,
        employee_id=current_user.id,
        leave_type=data.leave_type,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
    )
    db.add(leave)
    await db.flush()
    await db.refresh(leave)

    return LeaveResponse(
        id=leave.id,
        org_id=leave.org_id,
        employee_id=leave.employee_id,
        employee_name=current_user.name,
        leave_type=leave.leave_type,
        start_date=leave.start_date,
        end_date=leave.end_date,
        reason=leave.reason,
        status=leave.status,
        created_at=leave.created_at,
    )


@router.put("/{leave_id}", response_model=LeaveResponse)
async def update_leave(
    leave_id: int,
    request: Request,
    data: LeaveUpdateRequest,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    org_id = request.state.org_id

    result = await db.execute(
        select(LeaveRequest).where(LeaveRequest.id == leave_id, LeaveRequest.org_id == org_id)
    )
    leave = result.scalars().first()

    if not leave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")

    leave.status = data.status
    await db.flush()

    # Get employee name for response
    emp_result = await db.execute(select(Employee.name).where(Employee.id == leave.employee_id))
    emp_name = emp_result.scalar()

    return LeaveResponse(
        id=leave.id,
        org_id=leave.org_id,
        employee_id=leave.employee_id,
        employee_name=emp_name,
        leave_type=leave.leave_type,
        start_date=leave.start_date,
        end_date=leave.end_date,
        reason=leave.reason,
        status=leave.status,
        created_at=leave.created_at,
    )
