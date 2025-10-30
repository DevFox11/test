from functools import wraps
from typing import List
from .core import tenant_context

try:
    from fastapi import HTTPException
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

def tenant_required(func):
    """
    Decorator to ensure tenant context is set
    Works for both async and sync functions
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            tenant_context.require_tenant()
        except Exception as e:
            if FASTAPI_AVAILABLE:
                raise HTTPException(status_code=400, detail=str(e))
            else:
                raise e
        return await func(*args, **kwargs)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            tenant_context.require_tenant()
        except Exception as e:
            if FASTAPI_AVAILABLE:
                raise HTTPException(status_code=400, detail=str(e))
            else:
                raise e
        return func(*args, **kwargs)
    
    # Determinar si la función es async
    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

def specific_tenants(allowed_tenants: List[str]):
    """Decorator to restrict access to specific tenants"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tenant_id = tenant_context.require_tenant()
            if tenant_id not in allowed_tenants:
                if FASTAPI_AVAILABLE:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Tenant '{tenant_id}' not allowed. Allowed: {allowed_tenants}"
                    )
                else:
                    raise PermissionError(f"Tenant {tenant_id} not allowed")
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tenant_id = tenant_context.require_tenant()
            if tenant_id not in allowed_tenants:
                if FASTAPI_AVAILABLE:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Tenant '{tenant_id}' not allowed. Allowed: {allowed_tenants}"
                    )
                else:
                    raise PermissionError(f"Tenant {tenant_id} not allowed")
            return func(*args, **kwargs)
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator