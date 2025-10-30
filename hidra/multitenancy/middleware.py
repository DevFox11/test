try:
    from fastapi import Request, HTTPException
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
                raise HTTPException(
                    status_code=400, 
                    detail=f"Tenant ID required in header '{self.header_name}' for protected routes"
                )
            
            from .core import tenant_context
            
            # Validar que el tenant existe
            if not tenant_context.tenant_manager.tenant_exists(tenant_id):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Invalid tenant '{tenant_id}'. Available tenants: {list(tenant_context.tenant_manager.tenant_configs.keys())}"
                )
            
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