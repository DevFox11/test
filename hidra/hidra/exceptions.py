class HidraError(Exception):
    """Excepción base con mensajes amigables"""
    
    def __init__(self, message: str, suggestion: str = None, context: dict = None):
        super().__init__(message)
        self.suggestion = suggestion
        self.context = context or {}
    
    def __str__(self):
        result = super().__str__()
        if self.suggestion:
            result += f"\nSugerencia: {self.suggestion}"
        return result


class MultitenancyError(HidraError):
    """Base exception for multitenancy errors"""

    pass


class TenantNotFoundError(MultitenancyError):
    """Raised when a tenant is not found"""

    def __init__(self, tenant_id: str):
        super().__init__(
            f"Tenant '{tenant_id}' no encontrado",
            suggestion=f"Asegúrate de configurar el tenant '{tenant_id}' antes de usarlo",
            context={"tenant_id": tenant_id}
        )


class TenantContextError(MultitenancyError):
    """Raised when there's no tenant context"""

    def __init__(self, message: str = "No se encontró contexto de tenant"):
        super().__init__(
            message,
            suggestion="Asegúrate de que el middleware de tenant esté configurado y el header X-Tenant-ID esté presente en la solicitud"
        )
