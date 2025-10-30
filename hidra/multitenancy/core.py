from contextvars import ContextVar
from typing import Optional, Dict, Any

class TenantContext:
    def __init__(self):
        self.current_tenant = ContextVar('current_tenant', default=None)
        self.tenant_manager = MultiTenantManager()  # ✅ Un solo manager compartido
    
    def set_tenant(self, tenant_id: str) -> None:
        self.current_tenant.set(tenant_id)
    
    def get_tenant(self) -> Optional[str]:
        return self.current_tenant.get()
    
    def require_tenant(self) -> str:
        tenant = self.get_tenant()
        if not tenant:
            raise Exception("No tenant context set")
        return tenant

class MultiTenantManager:
    def __init__(self):
        self.tenant_configs = {}
    
    def configure_tenant(self, tenant_id: str, config: Dict[str, Any]) -> None:
        self.tenant_configs[tenant_id] = config
    
    def get_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        return self.tenant_configs.get(tenant_id, {})
    
    def tenant_exists(self, tenant_id: str) -> bool:
        return tenant_id in self.tenant_configs

# ✅ Instancia global compartida
tenant_context = TenantContext()