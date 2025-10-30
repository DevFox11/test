import pytest
from multitenancy.core import TenantContext, MultiTenantManager
from multitenancy.exceptions import TenantContextError

class TestTenantContext:
    def test_set_and_get_tenant(self):
        context = TenantContext()
        context.set_tenant("test-tenant")
        assert context.get_tenant() == "test-tenant"
    
    def test_require_tenant_success(self):
        context = TenantContext()
        context.set_tenant("test-tenant")
        assert context.require_tenant() == "test-tenant"
    
    def test_require_tenant_failure(self):
        context = TenantContext()
        with pytest.raises(TenantContextError):
            context.require_tenant()

class TestMultiTenantManager:
    def test_configure_and_get_tenant(self):
        manager = MultiTenantManager()
        config = {"db_name": "tenant_db"}
        manager.configure_tenant("test-tenant", config)
        assert manager.get_tenant_config("test-tenant") == config
    
    def test_tenant_exists(self):
        manager = MultiTenantManager()
        manager.configure_tenant("test-tenant", {})
        assert manager.tenant_exists("test-tenant") is True
        assert manager.tenant_exists("non-existent") is False