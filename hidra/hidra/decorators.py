from functools import wraps
from typing import Union, List, Optional
from .core import tenant_context

try:
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
            error_response = {
                "error": "Tenant context missing",
                "message": "This endpoint requires tenant identification but no tenant context was found",
                "solution": "Ensure your request includes the X-Tenant-ID header and passes through the TenantMiddleware",
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
                error_response = {
                    "error": "Tenant not authorized",
                    "message": f"Your tenant '{tenant_id}' does not have access to this feature",
                    "requested_tenant": tenant_id,
                    "allowed_tenants": allowed_tenants,
                    "solution": "Upgrade your plan or contact support for access to premium features",
                }
                return JSONResponse(status_code=403, content=error_response)
            return await func(*args, **kwargs)

        return async_wrapper

    return decorator

def requires_tenant(
    tenants: Optional[Union[str, List[str]]] = None,
    auto_error: bool = True
):
    """
    Decorador mejorado para requerir tenant
    
    Args:
        tenants: Tenant(s) permitidos. Si es None, cualquier tenant está permitido
        auto_error: Si True, lanza error automáticamente. Si False, permite manejo personalizado
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_tenant = tenant_context.get_tenant()
            
            if not current_tenant:
                if auto_error:
                    error_response = {
                        "error": "Tenant required",
                        "message": "This endpoint requires tenant identification"
                    }
                    return JSONResponse(status_code=400, content=error_response)
                else:
                    from .exceptions import TenantContextError
                    raise TenantContextError("Tenant not found in current context")
            
            # Verificar si el tenant está permitido
            if tenants:
                allowed = tenants if isinstance(tenants, list) else [tenants]
                if current_tenant not in allowed:
                    if auto_error:
                        error_response = {
                            "error": "Tenant not authorized",
                            "message": f"Tenant '{current_tenant}' does not have access to this resource"
                        }
                        return JSONResponse(status_code=403, content=error_response)
                    else:
                        from .exceptions import TenantContextError
                        raise TenantContextError(f"Tenant '{current_tenant}' not authorized")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator