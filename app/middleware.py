"""
app/middleware.py — TenantMiddleware sets request.state.org_id for every request.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


PUBLIC_PATHS = {
    "/",
    "/docs",
    "/openapi.json",
    "/api/organizations/register",
    "/api/auth/login",
    "/api/auth/forgot-password",
    "/api/auth/reset-password",
}


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Static files and favicon — pass through
        if path.startswith("/static") or path.startswith("/favicon"):
            request.state.org_id = None
            response = await call_next(request)
            return response

        # Public paths — no org_id required
        if path in PUBLIC_PATHS:
            request.state.org_id = None
            response = await call_next(request)
            return response

        # All other paths — read X-Org-Id header if present
        org_id_header = request.headers.get("X-Org-Id")
        if org_id_header:
            try:
                request.state.org_id = int(org_id_header)
            except ValueError:
                request.state.org_id = None
        else:
            request.state.org_id = None

        response = await call_next(request)
        return response
