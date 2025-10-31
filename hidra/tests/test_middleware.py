import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from typing import Optional

from hidra.middleware import TenantMiddleware
from hidra.decorators import tenant_required
from hidra import tenant_context, MultiTenantManager

# Define a resolver for testing
def header_resolver(request: Request) -> Optional[str]:
    return request.headers.get("X-Custom-Tenant-ID")

class TestTenantMiddleware:
    def setup_method(self):
        # Create a fresh app and manager for each test to ensure isolation
        self.app = FastAPI()
        self.manager = MultiTenantManager()
        self.manager.configure_tenant("tenant-a", {"plan": "basic"})
        
        # The global context is used by the middleware, so we set our fresh manager on it
        tenant_context.tenant_manager = self.manager

        # Add the middleware with the custom resolver
        self.app.add_middleware(TenantMiddleware, resolver=header_resolver)
        
        @self.app.get("/protected")
        @tenant_required
        async def protected_route():
            current_tenant = await tenant_context.require_tenant()
            return {"message": f"Welcome, {current_tenant}"}
        
        self.client = TestClient(self.app)

    def test_access_with_valid_tenant(self):
        response = self.client.get("/protected", headers={"X-Custom-Tenant-ID": "tenant-a"})
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome, tenant-a"}

    def test_access_without_identifier(self):
        response = self.client.get("/protected")
        assert response.status_code == 400
        json_response = response.json()
        assert json_response["error"] == "Tenant identification required"

    def test_access_with_invalid_tenant(self):
        response = self.client.get("/protected", headers={"X-Custom-Tenant-ID": "invalid-tenant"})
        assert response.status_code == 403
        json_response = response.json()
        assert json_response["error"] == "Invalid tenant"


# --- Test with a different, JWT-style resolver ---

async def mock_jwt_middleware(request: Request, call_next):
    if "X-Auth-Simulate" in request.headers:
        request.state.user = {"tenant_id": request.headers["X-Auth-Simulate"]}
    response = await call_next(request)
    return response

def jwt_style_resolver(request: Request) -> Optional[str]:
    if hasattr(request.state, "user"):
        return request.state.user.get("tenant_id")
    return None

class TestTenantMiddlewareWithJWT:
    def setup_method(self):
        # Create a fresh app and manager for each test to ensure isolation
        self.app = FastAPI()
        self.manager = MultiTenantManager()
        self.manager.configure_tenant("tenant-a", {"plan": "premium"})
        
        # The global context is used by the middleware, so we set our fresh manager on it
        tenant_context.tenant_manager = self.manager

        # Add middlewares to the fresh app. NOTE: Starlette processes middleware
        # in reverse order of addition. The one added LAST runs FIRST.
        self.app.add_middleware(TenantMiddleware, resolver=jwt_style_resolver)
        self.app.middleware("http")(mock_jwt_middleware)
        
        @self.app.get("/protected")
        @tenant_required
        async def protected_route():
            current_tenant = await tenant_context.require_tenant()
            return {"message": f"Welcome, {current_tenant}"}
        
        self.client = TestClient(self.app)

    def test_access_with_jwt_style_resolver(self):
        response = self.client.get("/protected", headers={"X-Auth-Simulate": "tenant-a"})
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome, tenant-a"}

    def test_access_with_jwt_style_no_user(self):
        response = self.client.get("/protected")
        assert response.status_code == 400
        assert response.json()["error"] == "Tenant identification required"


