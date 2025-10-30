# multitenancy/__init__.py
from .core import TenantContext, tenant_context, MultiTenantManager
from .database import MultiTenantSession
from .decorators import tenant_required, specific_tenants  # ✅ Asegurar que está aquí
from .exceptions import MultitenancyError, TenantNotFoundError, TenantContextError

__version__ = "0.1.0"

# Import condicional para middleware
try:
    from .middleware import TenantMiddleware, FlaskTenantMiddleware
except ImportError:
    pass

__all__ = [
    "TenantContext", "tenant_context", "MultiTenantManager",
    "MultiTenantSession", "tenant_required", "specific_tenants",  # ✅ Incluir aquí
    "MultitenancyError", "TenantNotFoundError", "TenantContextError",
    "TenantMiddleware", "FlaskTenantMiddleware", "__version__"
]