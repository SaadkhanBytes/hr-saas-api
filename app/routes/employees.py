"""
app/routes/employees.py — Employee CRUD, org-scoped, admin-gated for write operations.
GET    /api/employees       — auth, paginated, filterable by department/role/status
POST   /api/employees       — auth + admin only
PUT    /api/employees/{id}  — auth + admin only
DELETE /api/employees/{id}  — auth + admin only
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, hash_password
from app.database import get_db
from app.models import ADMIN_ROLES, Employee
from app.schemas import EmployeeCreateRequest, EmployeeResponse, EmployeeUpdateRequest

router = APIRouter(prefix="/api/employees", tags=["Employees"])


@router.get("", response_model=list[EmployeeResponse])
async def list_employees(
    request: Request,
    department: str | None = Query(None),
    role: str | None = Query(None),
    emp_status: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = request.state.org_id
    query = select(Employee).where(Employee.org_id == org_id)

    if department:
        query = query.where(Employee.department == department)
    if role:
        query = query.where(Employee.role == role)
    if emp_status:
        query = query.where(Employee.status == emp_status)
    if search:
        query = query.where(Employee.name.ilike(f"%{search}%"))

    query = query.order_by(Employee.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    employees = result.scalars().all()

    # Hide salary from non-admin users
    if current_user.role not in ADMIN_ROLES:
        responses = []
        for emp in employees:
            emp_response = EmployeeResponse.model_validate(emp)
            emp_response.salary = None
            responses.append(emp_response)
        return responses

    return employees


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    request: Request,
    data: EmployeeCreateRequest,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new employee (admin only)."""
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    org_id = request.state.org_id
    employee = Employee(
        org_id=org_id,
        name=data.name,
        email=data.email.lower().strip(),
        password_hash=hash_password(data.password),
        phone=data.phone,
        department=data.department,
        role=data.role,
        position=data.position,
        salary=data.salary,
        status=data.status,
        join_date=data.join_date,
    )
    db.add(employee)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists in this organization")

    await db.refresh(employee)
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    request: Request,
    data: EmployeeUpdateRequest,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing employee (admin only). Supports password change."""
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    org_id = request.state.org_id
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id, Employee.org_id == org_id)
    )
    employee = result.scalars().first()

    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    update_data = data.model_dump(exclude_unset=True)

    # Handle password change: hash it and set password_hash instead
    if "password" in update_data:
        raw_password = update_data.pop("password")
        update_data["password_hash"] = hash_password(raw_password)

    for field, value in update_data.items():
        setattr(employee, field, value)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists in this organization")

    await db.refresh(employee)
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: int,
    request: Request,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    org_id = request.state.org_id
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id, Employee.org_id == org_id)
    )
    employee = result.scalars().first()

    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    await db.delete(employee)
