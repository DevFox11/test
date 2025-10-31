import pytest
import time
import asyncio
from hidra.core import TenantContext, MultiTenantManager, TenancyStrategy
from hidra.exceptions import TenantContextError

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
    @pytest.mark.asyncio
    async def test_configure_and_get_tenant(self):
        manager = MultiTenantManager()
        config = {"db_name": "tenant_db"}
        manager.configure_tenant("test-tenant", config)
        assert await manager.get_tenant_config("test-tenant") == config

    @pytest.mark.asyncio
    async def test_tenant_exists(self):
        manager = MultiTenantManager()
        manager.configure_tenant("test-tenant", {})
        assert await manager.tenant_exists("test-tenant") is True
        assert await manager.tenant_exists("non-existent") is False

    @pytest.mark.asyncio
    async def test_get_non_existent_tenant_config(self):
        manager = MultiTenantManager()
        assert await manager.get_tenant_config("non-existent-tenant") == {}

    @pytest.mark.asyncio
    async def test_default_strategy(self):
        manager = MultiTenantManager()
        manager.set_default_strategy(TenancyStrategy.SCHEMA_PER_TENANT)
        assert manager.default_strategy == TenancyStrategy.SCHEMA_PER_TENANT

class TestTenantContextTenantSwitching:
    def test_as_tenant_context_manager(self):
        """Test the as_tenant context manager for temporary tenant switching."""
        context = TenantContext()
        context.set_tenant("original-tenant")
        
        # Verify initial tenant
        assert context.get_tenant() == "original-tenant"
        
        # Switch to another tenant temporarily
        with context.as_tenant("temp-tenant"):
            assert context.get_tenant() == "temp-tenant"
        
        # Should return to original tenant after context
        assert context.get_tenant() == "original-tenant"

    def test_as_tenant_nested_context(self):
        """Test nested as_tenant context managers."""
        context = TenantContext()
        context.set_tenant("original-tenant")
        
        assert context.get_tenant() == "original-tenant"
        
        with context.as_tenant("first-tenant"):
            assert context.get_tenant() == "first-tenant"
            
            with context.as_tenant("second-tenant"):
                assert context.get_tenant() == "second-tenant"
            
            # Should return to first-tenant after inner context
            assert context.get_tenant() == "first-tenant"
        
        # Should return to original-tenant after outer context
        assert context.get_tenant() == "original-tenant"

    @pytest.mark.asyncio
    async def test_async_as_tenant_context_manager(self):
        """Test the async_as_tenant context manager for temporary tenant switching."""
        context = TenantContext()
        context.set_tenant("original-tenant")
        
        # Verify initial tenant
        assert context.get_tenant() == "original-tenant"
        
        # Switch to another tenant temporarily with async context
        async with context.async_as_tenant("temp-tenant"):
            assert context.get_tenant() == "temp-tenant"
        
        # Should return to original tenant after context
        assert context.get_tenant() == "original-tenant"

    @pytest.mark.asyncio
    async def test_async_as_tenant_nested_context(self):
        """Test nested async_as_tenant context managers."""
        context = TenantContext()
        context.set_tenant("original-tenant")
        
        assert context.get_tenant() == "original-tenant"
        
        async with context.async_as_tenant("first-tenant"):
            assert context.get_tenant() == "first-tenant"
            
            async with context.async_as_tenant("second-tenant"):
                assert context.get_tenant() == "second-tenant"
            
            # Should return to first-tenant after inner context
            assert context.get_tenant() == "first-tenant"
        
        # Should return to original-tenant after outer context
        assert context.get_tenant() == "original-tenant"

    @pytest.mark.asyncio
    async def test_sync_async_context_mix(self):
        """Test mixing sync and async context managers."""
        context = TenantContext()
        context.set_tenant("original-tenant")
        
        assert context.get_tenant() == "original-tenant"
        
        async with context.async_as_tenant("async-tenant"):
            assert context.get_tenant() == "async-tenant"
            
            with context.as_tenant("sync-tenant"):
                assert context.get_tenant() == "sync-tenant"
            
            assert context.get_tenant() == "async-tenant"
        
        assert context.get_tenant() == "original-tenant"

    @pytest.mark.asyncio
    async def test_tenant_switching_with_require_tenant(self):
        """Test tenant switching with require_tenant functionality."""
        context = TenantContext()
        context.set_tenant("original-tenant")
        
        # Verify original tenant can be required
        original_tenant = context.require_tenant()
        assert original_tenant == "original-tenant"
        
        # Switch and verify new tenant can be required
        with context.as_tenant("new-tenant"):
            new_tenant = context.require_tenant()
            assert new_tenant == "new-tenant"
        
        # Verify back to original after context
        original_tenant_after = context.require_tenant()
        assert original_tenant_after == "original-tenant"


class TestMultiTenantManagerWithLoader:
    @pytest.mark.asyncio
    async def test_load_tenant_dynamically(self):
        async def mock_loader(tenant_id):
            if tenant_id == "dynamic-tenant":
                return {"db": "dynamic_db"}
            return None

        manager = MultiTenantManager(tenant_loader=mock_loader)
        
        assert await manager.tenant_exists("dynamic-tenant") is True
        assert await manager.get_tenant_config("dynamic-tenant") == {"db": "dynamic_db"}

    @pytest.mark.asyncio
    async def test_load_non_existent_tenant(self):
        async def mock_loader(tenant_id):
            return None

        manager = MultiTenantManager(tenant_loader=mock_loader)
        assert await manager.tenant_exists("non-existent") is False
        assert await manager.get_tenant_config("non-existent") == {}

    @pytest.mark.asyncio
    async def test_caching_mechanism(self):
        call_count = 0

        async def mock_loader_with_counter(tenant_id):
            nonlocal call_count
            call_count += 1
            if tenant_id == "cached-tenant":
                return {"db": "cached_db"}
            return None

        manager = MultiTenantManager(tenant_loader=mock_loader_with_counter, cache_ttl=1)

        assert await manager.tenant_exists("cached-tenant") is True
        assert call_count == 1

        assert await manager.tenant_exists("cached-tenant") is True
        assert call_count == 1

        await asyncio.sleep(1.1)

        assert await manager.tenant_exists("cached-tenant") is True
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_negative_caching(self):
        call_count = 0

        async def mock_loader_with_counter(tenant_id):
            nonlocal call_count
            call_count += 1
            return None

        manager = MultiTenantManager(tenant_loader=mock_loader_with_counter, cache_ttl=1)

        assert await manager.tenant_exists("non-existent") is False
        assert call_count == 1

        assert await manager.tenant_exists("non-existent") is False
        assert call_count == 1
