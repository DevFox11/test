import time
from contextvars import ContextVar
from contextlib import contextmanager, asynccontextmanager
from enum import Enum
from typing import Optional, Dict, Any, Callable, List, Awaitable
import inspect

from hidra.exceptions import TenantContextError

class TenancyStrategy(Enum):
    DATABASE_PER_TENANT = "database_per_tenant"
    SCHEMA_PER_TENANT = "schema_per_tenant"
    ROW_LEVEL = "row_level"

class TenantContext:
    def __init__(self):
        self.current_tenant = ContextVar("current_tenant", default=None)
        self.tenant_manager = MultiTenantManager()

    def set_tenant(self, tenant_id: str) -> None:
        self.current_tenant.set(tenant_id)

    def get_tenant(self) -> Optional[str]:
        return self.current_tenant.get()

    class _AwaitableStr(str):
        def __await__(self):
            async def _coro():
                return str(self)
            return _coro().__await__()

    def require_tenant(self) -> str:
        tenant = self.get_tenant()
        if not tenant:
            raise TenantContextError("No tenant context set")
        return TenantContext._AwaitableStr(tenant)

    @contextmanager
    def as_tenant(self, tenant_id: str):
        """Context manager to temporarily switch to another tenant.
        
        This is particularly useful for administrative tasks or support operations
        where administrators need to view data or execute actions as if they were
        another tenant, without making a new request.
        
        Args:
            tenant_id (str): The ID of the tenant to switch to temporarily
            
        Example:
            # Current tenant is "tenant-1"
            with tenant_context.as_tenant("tenant-2"):
                # Code here executes with "tenant-2" as the current tenant
                current = tenant_context.get_tenant()  # Returns "tenant-2"
            # Now back to original tenant "tenant-1"
        """
        token = self.current_tenant.set(tenant_id)
        try:
            yield
        finally:
            self.current_tenant.reset(token)

    @asynccontextmanager
    async def async_as_tenant(self, tenant_id: str):
        """Async context manager to temporarily switch to another tenant.
        
        This is the async version of as_tenant for use in async contexts.
        
        Args:
            tenant_id (str): The ID of the tenant to switch to temporarily
            
        Example:
            # Current tenant is "tenant-1"
            async with tenant_context.async_as_tenant("tenant-2"):
                # Code here executes with "tenant-2" as the current tenant
                current = await tenant_context.require_tenant()  # Returns "tenant-2"
            # Now back to original tenant "tenant-1"
        """
        token = self.current_tenant.set(tenant_id)
        try:
            yield
        finally:
            self.current_tenant.reset(token)

class MultiTenantManager:
    def __init__(
        self,
        tenant_loader: Optional[Callable[[str], Awaitable[Optional[Dict[str, Any]]]]] = None,
        get_all_tenants_loader: Optional[Callable[[], Awaitable[List[str]]]] = None,
        cache_ttl: int = 300,
    ):
        self.tenant_loader = tenant_loader
        self.get_all_tenants_loader = get_all_tenants_loader
        self.cache_ttl = cache_ttl
        self.tenant_configs: Dict[str, Dict[str, Any]] = {}
        self.tenant_cache: Dict[str, bool] = {}
        self.cache_timestamps: Dict[str, float] = {}
        self.default_strategy = TenancyStrategy.DATABASE_PER_TENANT

    def configure_tenant(self, tenant_id: str, config: Dict[str, Any]) -> None:
        self.tenant_configs[tenant_id] = config
        self.tenant_cache[tenant_id] = True
        self.cache_timestamps[tenant_id] = time.time()

    async def tenant_exists(self, tenant_id: str) -> bool:
        if tenant_id in self.tenant_cache:
            if time.time() - self.cache_timestamps.get(tenant_id, 0) < self.cache_ttl:
                return self.tenant_cache[tenant_id]

        if self.tenant_loader:
            loader_result = self.tenant_loader(tenant_id)
            if inspect.isawaitable(loader_result):
                config = await loader_result
            else:
                config = loader_result

            if config is not None:
                self.configure_tenant(tenant_id, config)
                return True
            else:
                self.tenant_cache[tenant_id] = False
                self.cache_timestamps[tenant_id] = time.time()
                return False

        return tenant_id in self.tenant_configs

    async def get_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        if tenant_id not in self.tenant_configs:
            await self.tenant_exists(tenant_id)
        return self.tenant_configs.get(tenant_id, {})

    async def get_all_tenant_ids(self) -> List[str]:
        if self.get_all_tenants_loader:
            loader_result = self.get_all_tenants_loader()
            if inspect.isawaitable(loader_result):
                return await loader_result
            else:
                return loader_result
        return list(self.tenant_configs.keys())

    def set_default_strategy(self, strategy: TenancyStrategy):
        self.default_strategy = strategy

tenant_context = TenantContext()
