"""
Tenant isolation middleware.
Extracts X-Org-Id header and scopes every request to that organization.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

# Routes that don't require tenant context
PUBLIC_PATHS = {"/", "/docs", "/openapi.json", "/api/organizations"}


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Core multi-tenant pattern:
    1. Extract org_id from X-Org-Id header
    2. Attach to request.state.org_id
    3. All downstream route handlers use this to scope queries
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip tenant check for public routes and static files
        if path in PUBLIC_PATHS or path.startswith("/static") or path.startswith("/favicon"):
            request.state.org_id = None
            return await call_next(request)

        # Extract org_id from header
        org_id_header = request.headers.get("X-Org-Id")

        if not org_id_header:
            # For API routes, require the header
            if path.startswith("/api/"):
                raise HTTPException(
                    status_code=400,
                    detail="X-Org-Id header is required for tenant-scoped requests"
                )
            request.state.org_id = None
            return await call_next(request)

        try:
            request.state.org_id = int(org_id_header)
        except ValueError:
            raise HTTPException(status_code=400, detail="X-Org-Id must be a valid integer")

        return await call_next(request)
