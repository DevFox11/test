import pytest
import os
from typing import List
from sqlalchemy import text, create_engine

from hidra import (
    tenant_context,
    MultiTenantManager,
    create_tenant_aware_session,
    TenancyStrategy,
    run_migrations_for_all_tenants,
)

class TestMigrationHelper:
    def setup_method(self):
        self.tenant_ids = ["tenant1", "tenant2", "tenant3"]
        self.db_files = [f"tenant_{tid}.db" for tid in self.tenant_ids]

        # Clean up any old db files before starting
        for db_file in self.db_files:
            if os.path.exists(db_file): os.remove(db_file)

        # Configure a manager with a loader for all tenants
        def get_all_tenants_loader() -> List[str]:
            return self.tenant_ids

        self.manager = MultiTenantManager(get_all_tenants_loader=get_all_tenants_loader)
        tenant_context.tenant_manager = self.manager

        # Create the tenant-aware session factory
        self.db_config = {"db_driver": "sqlite"}
        self.Session = create_tenant_aware_session(
            base_config=self.db_config, strategy=TenancyStrategy.DATABASE_PER_TENANT
        )

    def teardown_method(self):
        # Close all connections to release file locks
        self.Session.close_all()

        # Clean up db files after tests
        for db_file in self.db_files:
            if os.path.exists(db_file): os.remove(db_file)
        
        # Clear context
        tenant_context.set_tenant(None)

    def test_run_migrations_for_all_tenants(self):
        """Verify that the migration helper runs for all tenants and applies changes."""
        migrated_tenants = []

        def mock_migration_func(session, tenant_id):
            migrated_tenants.append(tenant_id)
            # Assert that the context is correctly set for this migration
            assert tenant_context.get_tenant() == tenant_id

            # Create a simple table and insert data
            session.execute(text("CREATE TABLE IF NOT EXISTS migrations (version INT, tenant_id TEXT)"))
            session.execute(text(f"INSERT INTO migrations VALUES (1, '{tenant_id}')"))
            session.commit()

        # Run the migrations
        run_migrations_for_all_tenants(self.Session, mock_migration_func)

        # Assert that the migration function was called for all tenants
        assert sorted(migrated_tenants) == sorted(self.tenant_ids)

        # Verify that the changes were applied to each tenant's database
        for tenant_id in self.tenant_ids:
            # Connect directly to the tenant's database to verify independently
            engine = create_engine(f"sqlite:///tenant_{tenant_id}.db")
            with engine.connect() as connection:
                result = connection.execute(text("SELECT tenant_id FROM migrations WHERE version = 1")).scalar()
                assert result == tenant_id
            engine.dispose()
