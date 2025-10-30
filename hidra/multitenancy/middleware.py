try:
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

if FASTAPI_AVAILABLE:
    class TenantMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, header_name: str = "X-Tenant-ID", exclude_paths: list = None):
            super().__init__(app)
            self.header_name = header_name
            self.exclude_paths = exclude_paths or [
                "/", 
                "/health", 
                "/tenants", 
                "/docs", 
                "/openapi.json",
                "/favicon.ico",
                "/redoc"
            ]
        
        async def dispatch(self, request: Request, call_next):
            # ✅ Verificar si la ruta está excluida (es pública)
            if self._is_public_path(request.url.path):
                # Rutas públicas - no requieren tenant, pasamos directamente
                response = await call_next(request)
                return response
            
            # 🔐 Rutas protegidas - requieren tenant
            tenant_id = request.headers.get(self.header_name)
            
            if not tenant_id:
                available_tenants = self._get_available_tenants()
                tenant_names = [t["id"] for t in available_tenants]
                
                # ✅ SOLUCIÓN DIRECTA: Devolver JSONResponse en lugar de lanzar excepción
                error_response = {
                    "error": "Tenant identification required",
                    "message": "This endpoint requires tenant identification to access tenant-specific data",
                    "solution": f"Add the '{self.header_name}' header to your request",
                    "example": {
                        "headers": {
                            self.header_name: "acme-corp",
                            "Content-Type": "application/json"
                        },
                        "curl": f'curl -H "{self.header_name}: acme-corp" {request.url}'
                    },
                    "available_tenants": available_tenants,
                    "public_endpoints": self.exclude_paths
                }
                return JSONResponse(status_code=400, content=error_response)
            
            from .core import tenant_context
            
            # Validar que el tenant existe
            if not tenant_context.tenant_manager.tenant_exists(tenant_id):
                available_tenants = self._get_available_tenants()
                
                error_response = {
                    "error": "Invalid tenant",
                    "message": f"The tenant '{tenant_id}' is not recognized or not authorized",
                    "requested_tenant": tenant_id,
                    "available_tenants": available_tenants,
                    "solution": "Use one of the available tenant IDs or contact support to register a new tenant"
                }
                return JSONResponse(status_code=403, content=error_response)
            
            # Establecer el tenant en el contexto
            tenant_context.set_tenant(tenant_id)
            
            response = await call_next(request)
            return response
        
        def _is_public_path(self, path: str) -> bool:
            """Determina si una ruta es pública (no requiere tenant)"""
            return any(
                path == exclude_path or path.startswith(exclude_path + "/")
                for exclude_path in self.exclude_paths
            )
        
        def _get_available_tenants(self):
            """Obtener lista de tenants disponibles para mensajes de error"""
            from .core import tenant_context
            manager = tenant_context.tenant_manager
            tenants_info = []
            
            for tenant_id in manager.tenant_configs.keys():
                config = manager.get_tenant_config(tenant_id)
                tenants_info.append({
                    "id": tenant_id,
                    "plan": config.get("plan", "basic"),
                    "features": config.get("features", [])
                })
            
            return tenants_info