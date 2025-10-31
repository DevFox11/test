from .core import TenantContext, tenant_context, MultiTenantManager, TenancyStrategy
from .database import MultiTenantSession, create_tenant_aware_session
from .decorators import tenant_required, specific_tenants, requires_tenant
from .exceptions import MultitenancyError, TenantNotFoundError, TenantContextError, HidraError
from .models import TenantAwareModel
from .migrations import run_migrations_for_all_tenants
from .quick_start import quick_start
from .helpers import get_current_tenant_id, tenant_exists, get_current_tenant_config
from .db_simple import HidraDB, create_db_session
from .diagnostic import diagnose_setup, print_diagnosis
from .integrations import setup_fastapi_app

__version__ = "0.2.0"

from .middleware import TenantMiddleware

__all__ = [
    "TenantContext",
    "tenant_context",
    "MultiTenantManager",
    "TenancyStrategy",
    "MultiTenantSession",
    "create_tenant_aware_session",
    "tenant_required",
    "specific_tenants",
    "requires_tenant",
    "TenantAwareModel",
    "MultitenancyError",
    "TenantNotFoundError",
    "TenantContextError",
    "HidraError",
    "TenantMiddleware",
    "run_migrations_for_all_tenants",
    "quick_start",
    "get_current_tenant_id",
    "tenant_exists",
    "get_current_tenant_config",
    "HidraDB",
    "create_db_session",
    "diagnose_setup",
    "print_diagnosis",
    "setup_fastapi_app",
    "__version__",
]