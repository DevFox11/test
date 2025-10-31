try:
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from typing import Callable, Optional, List, Awaitable, Dict, Any

def default_tenant_resolver(request: Request) -> Optional[str]:
    """Default resolver that gets the tenant ID from the X-Tenant-ID header."""
    return request.headers.get("X-Tenant-ID")

if FASTAPI_AVAILABLE:

    class TenantMiddleware(BaseHTTPMiddleware):
        def __init__(
            self,
            app,
            resolver: Callable[[Request], Optional[str]] = None,  # Parámetro original
            exclude_paths: list = None,
            validate_existence: bool = True,
            manager=None,
            header_name: str = "X-Tenant-ID",  # Nuevo parámetro con valor por defecto
        ):
            super().__init__(app)
            
            # Si se proporciona un resolver personalizado, usarlo; sino, usar el basado en header_name
            if resolver:
                self.resolver = resolver
                # Extraer header_name si el resolver es el default_tenant_resolver
                if resolver == default_tenant_resolver:
                    self.header_name = "X-Tenant-ID"
                else:
                    # Para resolver personalizados, usar un valor genérico o intentar determinarlo
                    self.header_name = header_name
            else:
                # Nuevo resolver basado en header_name
                def custom_resolver(request: Request) -> Optional[str]:
                    return request.headers.get(header_name)
                
                self.resolver = custom_resolver
                self.header_name = header_name  # Guardar para uso en mensajes de error
            
            self.exclude_paths = exclude_paths or [
                "/",
                "/health", 
                "/tenants",
                "/docs",
                "/openapi.json",
                "/favicon.ico",
                "/redoc",
            ]
            # Snapshot de tenants permitidos al momento de configurar el middleware
            try:
                from .core import tenant_context as _ctx
                self.manager_ref = manager or _ctx.tenant_manager
                self.allowed_tenants_snapshot = set(self.manager_ref.tenant_configs.keys())
            except Exception:
                self.manager_ref = manager
                self.allowed_tenants_snapshot = set(getattr(self.manager_ref, "tenant_configs", {}).keys() if self.manager_ref else [])
            self.validate_existence = validate_existence

        async def dispatch(self, request: Request, call_next):
            if self._is_public_path(request.url.path):
                response = await call_next(request)
                return response

            tenant_id = self.resolver(request)

            if not tenant_id:
                error_response = {
                    "error": "Tenant identification required",
                    "message": "This endpoint requires tenant identification to access tenant-specific data",
                    "solution": "Ensure your request provides a valid tenant identifier.",
                }
                return JSONResponse(status_code=400, content=error_response)

            from .core import tenant_context

            # Establecer el tenant en el contexto antes de validar
            tenant_context.set_tenant(tenant_id)

            if self.validate_existence:
                # Validación combinada: snapshot, referencia y consulta al manager actual
                exists = False
                if self.allowed_tenants_snapshot:
                    exists = tenant_id in self.allowed_tenants_snapshot
                if not exists and self.manager_ref is not None:
                    exists = tenant_id in self.manager_ref.tenant_configs
                if not exists:
                    # Último recurso: manager global actual
                    global_manager = tenant_context.tenant_manager
                    exists = tenant_id in global_manager.tenant_configs
                if not exists:
                    # Intento final: llamar a loader (en referencia si existe)
                    ref_manager = self.manager_ref or tenant_context.tenant_manager
                    exists = await ref_manager.tenant_exists(tenant_id)
                if not exists:
                    available_tenants = await self._get_available_tenants()

                    error_response = {
                        "error": "Invalid tenant",
                        "message": f"The tenant '{tenant_id}' is not recognized or not authorized",
                        "requested_tenant": tenant_id,
                        "available_tenants": available_tenants,
                        "solution": "Use one of the available tenant IDs or contact support to register a new tenant",
                    }
                    return JSONResponse(status_code=403, content=error_response)

            response = await call_next(request)
            return response

        def _is_public_path(self, path: str) -> bool:
            """Determina si una ruta es pública (no requiere tenant)"""
            return any(
                path == exclude_path or path.startswith(exclude_path + "/")
                for exclude_path in self.exclude_paths
            )

        async def _get_available_tenants(self) -> List[Dict[str, Any]]:
            """Obtener lista de tenants disponibles para mensajes de error"""
            from .core import tenant_context

            manager = tenant_context.tenant_manager
            tenants_info = []

            all_tenant_ids = await manager.get_all_tenant_ids()

            for tenant_id in all_tenant_ids:
                config = await manager.get_tenant_config(tenant_id)
                tenants_info.append(
                    {
                        "id": tenant_id,
                        "plan": config.get("plan", "basic"),
                        "features": config.get("features", []),
                    }
                )

            return tenants_info
