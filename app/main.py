"""
FastAPI application entry point.
Wires up middleware, routes, static files, and seeds data on startup.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.middleware import TenantMiddleware
from app.seed import seed_database
from app.routes import orgs, auth, employees, attendance, leaves, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed database on startup."""
    await seed_database()
    yield


app = FastAPI(
    title="HR SaaS — Multi-Tenant",
    description="Multi-tenant HR management with row-level organization isolation",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────
app.add_middleware(TenantMiddleware)

# ── Routes ─────────────────────────────────────────────
app.include_router(orgs.router)
app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(leaves.router)
app.include_router(stats.router)

# ── Static Files ───────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the HR dashboard SPA."""
    return FileResponse("static/index.html")
