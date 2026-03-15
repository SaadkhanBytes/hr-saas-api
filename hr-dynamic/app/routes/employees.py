"""
Employees route — tenant-scoped, role-gated, paginated.
"""

from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Employee, ADMIN_ROLES
from app.schemas import EmployeeCreate, EmployeeUpdate
from app.auth import get_current_user, hash_password

router = APIRouter(prefix="/api/employees", tags=["employees"])


def _serialize(e: Employee) -> dict:
    return {
        "id": e.id,
        "org_id": e.org_id,
        "name": e.name,
        "email": e.email,
        "phone": e.phone,
        "department": e.department.value,
        "role": e.role.value,
        "position": e.position,
        "salary": e.salary,
        "status": e.status.value,
        "join_date": e.join_date.isoformat(),
        "created_at": e.created_at.isoformat(),
    }


@router.get("")
async def list_employees(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _user: Employee = Depends(get_current_user),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    department: str = Query(default=None),
    status: str = Query(default=None),
):
    """List employees — paginated, filterable by department and status."""
    org_id = request.state.org_id
    try:
        q = select(Employee).where(Employee.org_id == org_id)
        if department:
            q = q.where(Employee.department == department)
        if status:
            q = q.where(Employee.status == status)
        q = q.order_by(Employee.name).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(q)
        employees = result.scalars().all()
        return [_serialize(e) for e in employees]
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch employees") from exc


@router.post("", status_code=201)
async def create_employee(
    body: EmployeeCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Employee = Depends(get_current_user),
):
    """Create employee — admin roles only."""
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Only managers and above can create employees")

    org_id = request.state.org_id
    try:
        emp = Employee(
            org_id=org_id,
            name=body.name,
            email=body.email,
            phone=body.phone,
            department=body.department,
            role=body.role,
            position=body.position,
            salary=body.salary,
            password_hash=hash_password(body.password) if body.password else None,
        )
        db.add(emp)
        await db.flush()
        return _serialize(emp)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="An employee with this email already exists in your organization")
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to create employee") from exc


@router.put("/{emp_id}")
async def update_employee(
    emp_id: int,
    body: EmployeeUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Employee = Depends(get_current_user),
):
    """Update employee fields — admin roles only."""
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Only managers and above can edit employees")

    org_id = request.state.org_id
    try:
        result = await db.execute(
            select(Employee).where(Employee.id == emp_id, Employee.org_id == org_id)
        )
        emp = result.scalar()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found in this organization")

        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(emp, field, value)

        await db.flush()
        return _serialize(emp)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to update employee") from exc


@router.delete("/{emp_id}")
async def delete_employee(
    emp_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Employee = Depends(get_current_user),
):
    """Delete employee — admin roles only."""
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Only managers and above can delete employees")

    org_id = request.state.org_id
    try:
        result = await db.execute(
            select(Employee).where(Employee.id == emp_id, Employee.org_id == org_id)
        )
        emp = result.scalar()
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found in this organization")
        await db.delete(emp)
        return {"message": "Employee deleted", "id": emp_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to delete employee") from exc
