from functools import wraps
from typing import List
from .core import tenant_context

try:
    from fastapi import HTTPException
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

def tenant_required(func):
    """Decorator que devuelve JSONResponse directamente"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        tenant_id = tenant_context.get_tenant()
        if not tenant_id:
            # ✅ Devolver JSONResponse directamente
            error_response = {
                "error": "Tenant context missing",
                "message": "This endpoint requires tenant identification but no tenant context was found",
                "solution": "Ensure your request includes the X-Tenant-ID header and passes through the TenantMiddleware"
            }
            return JSONResponse(status_code=400, content=error_response)
        return await func(*args, **kwargs)
    
    return async_wrapper

def specific_tenants(allowed_tenants: List[str]):
    """Decorator para tenants específicos que devuelve JSONResponse"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tenant_id = tenant_context.get_tenant()
            if tenant_id not in allowed_tenants:
                # ✅ Devolver JSONResponse directamente
                error_response = {
                    "error": "Tenant not authorized",
                    "message": f"Your tenant '{tenant_id}' does not have access to this feature",
                    "requested_tenant": tenant_id,
                    "allowed_tenants": allowed_tenants,
                    "solution": "Upgrade your plan or contact support for access to premium features"
                }
                return JSONResponse(status_code=403, content=error_response)
            return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator