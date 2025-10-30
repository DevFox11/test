class MultitenancyError(Exception):
    """Base exception for multitenancy errors"""
    pass

class TenantNotFoundError(MultitenancyError):
    """Raised when a tenant is not found"""
    pass

class TenantContextError(MultitenancyError):
    """Raised when there's no tenant context"""
    pass