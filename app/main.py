"""
app/main.py — FastAPI application entry point.
Mounts static files, includes routers, adds middleware, runs seed on startup.
"""
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.limiter import limiter

from app.middleware import TenantMiddleware
from app.routes import attendance, auth, employees, leaves, orgs, stats
from app.seed import seed_data

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: seed database
    await seed_data()
    yield
    # Shutdown: nothing to clean up


# ── Rate limiter ───────────────────────────────────────────────────────────────

app = FastAPI(title="HR SaaS API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS middleware ────────────────────────────────────────────────────────────
allow_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenant middleware
app.add_middleware(TenantMiddleware)

# Static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Routers
app.include_router(orgs.router)
app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(leaves.router)
app.include_router(stats.router)


@app.get("/")
async def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "HR SaaS API is running. Visit /docs for API documentation."}
