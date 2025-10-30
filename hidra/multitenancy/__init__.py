from .core import TenantContext, tenant_context, MultiTenantManager, TenancyStrategy
from .database import MultiTenantSession
from .decorators import tenant_required, specific_tenants
from .exceptions import MultitenancyError, TenantNotFoundError, TenantContextError
from .models import TenantAwareModel  # ✅ Nuevo import

__version__ = "0.2.0"  # ✅ Nueva versión

# Import condicional para middleware
try:
    from .middleware import TenantMiddleware, FlaskTenantMiddleware
except ImportError:
    pass

__all__ = [
    "TenantContext", "tenant_context", "MultiTenantManager", "TenancyStrategy",
    "MultiTenantSession", "tenant_required", "specific_tenants", "TenantAwareModel",
    "MultitenancyError", "TenantNotFoundError", "TenantContextError",
    "TenantMiddleware", "FlaskTenantMiddleware", "__version__"
]