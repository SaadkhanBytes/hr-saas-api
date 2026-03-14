"""
Tenant isolation middleware.
For public/unauthenticated routes, uses X-Org-Id header (org listing, login).
For authenticated routes, org_id comes from the JWT token (set by auth.get_current_user).
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

# Routes that don't require any tenant context
PUBLIC_PATHS = {"/", "/docs", "/openapi.json", "/api/organizations", "/api/auth/login"}


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Multi-tenant middleware:
    - Public routes: no tenant context needed
    - Auth routes: handle their own context via JWT
    - Legacy support: X-Org-Id header for unauthenticated browsing
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip tenant check for public routes and static files
        if path in PUBLIC_PATHS or path.startswith("/static") or path.startswith("/favicon"):
            request.state.org_id = None
            return await call_next(request)

        # For API routes, try X-Org-Id header (will be overridden by JWT if auth is used)
        org_id_header = request.headers.get("X-Org-Id")
        if org_id_header:
            try:
                request.state.org_id = int(org_id_header)
            except ValueError:
                raise HTTPException(status_code=400, detail="X-Org-Id must be a valid integer")
        else:
            request.state.org_id = None

        return await call_next(request)
