"""
Seed data: 3 companies with distinct employees, attendance, and leave requests.
Safe to re-run — skips seeding if data already exists.
Only runs in non-production environments (checks ENV variable).
"""

import os
from datetime import date, timedelta
from sqlalchemy import select, text
from app.models import (
    Base, Organization, Employee, Attendance, LeaveRequest,
    PlanType, Department, EmployeeRole, EmployeeStatus,
    AttendanceStatus, LeaveType, LeaveStatus,
)
from app.database import engine, async_session
from app.auth import hash_password

DEFAULT_PWD = hash_password("password123")


async def seed_database():
    """Create tables and seed demo data if not already seeded.
    Skips entirely when ENV=production.
    """
    if os.getenv("ENV", "development").lower() == "production":
        # In production: only create tables, never seed
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return

    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(select(Organization).limit(1))
        if result.scalar():
            return  # Already seeded

        today = date.today()

        # ── Org 1: TechVista Solutions ──────────────────
        org1 = Organization(name="TechVista Solutions", slug="techvista", plan=PlanType.PRO, industry="Technology")
        session.add(org1)
        await session.flush()

        tv_employees = [
            Employee(org_id=org1.id, name="Sarah Chen", email="sarah@techvista.io", password_hash=DEFAULT_PWD,
                     department=Department.ENGINEERING, role=EmployeeRole.CXO, position="CTO", salary=180000),
            Employee(org_id=org1.id, name="Marcus Rivera", email="marcus@techvista.io", password_hash=DEFAULT_PWD,
                     department=Department.ENGINEERING, role=EmployeeRole.LEAD, position="Lead Engineer", salary=130000),
            Employee(org_id=org1.id, name="Priya Patel", email="priya@techvista.io", password_hash=DEFAULT_PWD,
                     department=Department.DESIGN, role=EmployeeRole.SENIOR, position="UX Designer", salary=110000),
            Employee(org_id=org1.id, name="Jake Thompson", email="jake@techvista.io", password_hash=DEFAULT_PWD,
                     department=Department.MARKETING, role=EmployeeRole.MID, position="Growth Marketer", salary=85000),
            Employee(org_id=org1.id, name="Aisha Okonkwo", email="aisha@techvista.io", password_hash=DEFAULT_PWD,
                     department=Department.HR, role=EmployeeRole.MANAGER, position="HR Manager", salary=95000),
            Employee(org_id=org1.id, name="Leo Zhang", email="leo@techvista.io", password_hash=DEFAULT_PWD,
                     department=Department.ENGINEERING, role=EmployeeRole.JUNIOR, position="Frontend Dev", salary=72000),
            Employee(org_id=org1.id, name="Nina Kowalski", email="nina@techvista.io", password_hash=DEFAULT_PWD,
                     department=Department.FINANCE, role=EmployeeRole.SENIOR, position="Finance Lead", salary=105000),
            Employee(org_id=org1.id, name="Omar Siddiqui", email="omar@techvista.io", password_hash=DEFAULT_PWD,
                     department=Department.ENGINEERING, role=EmployeeRole.MID, position="Backend Dev", salary=95000),
        ]
        for e in tv_employees:
            session.add(e)
        await session.flush()

        # ── Org 2: Bloom Health Clinic ──────────────────
        org2 = Organization(name="Bloom Health Clinic", slug="bloomhealth", plan=PlanType.STARTER, industry="Healthcare")
        session.add(org2)
        await session.flush()

        bh_employees = [
            Employee(org_id=org2.id, name="Dr. Luna Wright", email="luna@bloomhealth.com", password_hash=DEFAULT_PWD,
                     department=Department.OPERATIONS, role=EmployeeRole.DIRECTOR, position="Medical Director", salary=220000),
            Employee(org_id=org2.id, name="Dr. Raj Kumar", email="raj@bloomhealth.com", password_hash=DEFAULT_PWD,
                     department=Department.OPERATIONS, role=EmployeeRole.SENIOR, position="Physician", salary=190000),
            Employee(org_id=org2.id, name="Maria Santos", email="maria@bloomhealth.com", password_hash=DEFAULT_PWD,
                     department=Department.SUPPORT, role=EmployeeRole.MID, position="Nurse", salary=78000),
            Employee(org_id=org2.id, name="Tom Bradley", email="tom@bloomhealth.com", password_hash=DEFAULT_PWD,
                     department=Department.FINANCE, role=EmployeeRole.MANAGER, position="Finance Manager", salary=98000),
            Employee(org_id=org2.id, name="Chen Wei", email="chen@bloomhealth.com", password_hash=DEFAULT_PWD,
                     department=Department.HR, role=EmployeeRole.MID, position="HR Coordinator", salary=68000),
        ]
        for e in bh_employees:
            session.add(e)
        await session.flush()

        # ── Org 3: NovaTech Manufacturing ──────────────
        org3 = Organization(name="NovaTech Manufacturing", slug="novatech", plan=PlanType.ENTERPRISE, industry="Manufacturing")
        session.add(org3)
        await session.flush()

        nt_employees = [
            Employee(org_id=org3.id, name="Dr. Alex Morgan", email="alex@novatech.com", password_hash=DEFAULT_PWD,
                     department=Department.OPERATIONS, role=EmployeeRole.VP, position="VP Operations", salary=210000),
            Employee(org_id=org3.id, name="Sandra Lee", email="sandra@novatech.com", password_hash=DEFAULT_PWD,
                     department=Department.ENGINEERING, role=EmployeeRole.MANAGER, position="Engineering Manager", salary=145000),
            Employee(org_id=org3.id, name="Ben Okafor", email="ben@novatech.com", password_hash=DEFAULT_PWD,
                     department=Department.SALES, role=EmployeeRole.SENIOR, position="Sales Director", salary=125000),
            Employee(org_id=org3.id, name="Fatima Al-Rashid", email="fatima@novatech.com", password_hash=DEFAULT_PWD,
                     department=Department.FINANCE, role=EmployeeRole.SENIOR, position="Senior Accountant", salary=100000),
            Employee(org_id=org3.id, name="Ivan Petrov", email="ivan@novatech.com", password_hash=DEFAULT_PWD,
                     department=Department.ENGINEERING, role=EmployeeRole.MID, position="Process Engineer", salary=88000),
            Employee(org_id=org3.id, name="Grace Kim", email="grace@novatech.com", password_hash=DEFAULT_PWD,
                     department=Department.HR, role=EmployeeRole.MANAGER, position="HR Manager", salary=92000),
        ]
        for e in nt_employees:
            session.add(e)
        await session.flush()

        # ── Attendance records (last 7 days) ────────────
        all_emp_groups = [tv_employees, bh_employees, nt_employees]
        statuses = [
            AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT,
            AttendanceStatus.WORK_FROM_HOME, AttendanceStatus.LATE, AttendanceStatus.ABSENT,
        ]
        for emp_list in all_emp_groups:
            for emp in emp_list:
                for days_ago in range(7):
                    d = today - timedelta(days=days_ago)
                    if d.weekday() >= 5:
                        continue
                    s = statuses[(emp.id + days_ago) % len(statuses)]
                    att = Attendance(
                        org_id=emp.org_id,
                        employee_id=emp.id,
                        date=d,
                        status=s,
                        check_in="09:00" if s != AttendanceStatus.ABSENT else "",
                        check_out="18:00" if s not in (AttendanceStatus.ABSENT, AttendanceStatus.HALF_DAY) else "13:00",
                    )
                    session.add(att)

        # ── Leave requests ──────────────────────────────
        leave_data = [
            (tv_employees[1], LeaveType.ANNUAL, today + timedelta(days=5), today + timedelta(days=10), LeaveStatus.PENDING),
            (tv_employees[2], LeaveType.SICK, today - timedelta(days=2), today - timedelta(days=1), LeaveStatus.APPROVED),
            (tv_employees[5], LeaveType.CASUAL, today + timedelta(days=3), today + timedelta(days=4), LeaveStatus.PENDING),
            (bh_employees[2], LeaveType.SICK, today - timedelta(days=1), today, LeaveStatus.APPROVED),
            (bh_employees[3], LeaveType.ANNUAL, today + timedelta(days=14), today + timedelta(days=21), LeaveStatus.PENDING),
            (nt_employees[1], LeaveType.MATERNITY, today + timedelta(days=30), today + timedelta(days=120), LeaveStatus.APPROVED),
            (nt_employees[4], LeaveType.CASUAL, today + timedelta(days=1), today + timedelta(days=2), LeaveStatus.REJECTED),
        ]
        for emp, ltype, start, end, lstatus in leave_data:
            session.add(LeaveRequest(
                org_id=emp.org_id,
                employee_id=emp.id,
                leave_type=ltype,
                start_date=start,
                end_date=end,
                status=lstatus,
                reason="Seeded demo request",
            ))

        await session.commit()
