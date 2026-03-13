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
from app.routes import orgs
from app.routes import users as employees_routes
from app.routes import projects as attendance_routes
from app.routes import tasks as leaves_routes
from app.routes import stats


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
app.include_router(employees_routes.router)
app.include_router(attendance_routes.router)
app.include_router(leaves_routes.router)
app.include_router(stats.router)

# ── Static Files ───────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the HR dashboard SPA."""
    return FileResponse("static/index.html")
