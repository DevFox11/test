import pytest
import os
from sqlalchemy import text, create_engine
from sqlalchemy.orm import declarative_base

from hidra import (
    tenant_context,
    MultiTenantManager,
    create_tenant_aware_session,
    TenancyStrategy,
)

# Setup for the tests
Base = declarative_base()

class TestTenantAwareSession:
    def setup_method(self):
        # Clean up any old db files before starting
        if os.path.exists("tenant_alpha.db"): os.remove("tenant_alpha.db")
        if os.path.exists("tenant_beta.db"): os.remove("tenant_beta.db")

        # Configure a manager and tenants
        self.manager = MultiTenantManager()
        self.manager.configure_tenant("alpha", {})
        self.manager.configure_tenant("beta", {})
        tenant_context.tenant_manager = self.manager

        # Create the session factory for the tests
        db_config = {"db_driver": "sqlite"}
        self.Session = create_tenant_aware_session(
            base_config=db_config, strategy=TenancyStrategy.DATABASE_PER_TENANT
        )

    def teardown_method(self):
        # IMPORTANT: Close all connections to release file locks
        self.Session.close_all()

        # Clean up db files after tests
        if os.path.exists("tenant_alpha.db"): os.remove("tenant_alpha.db")
        if os.path.exists("tenant_beta.db"): os.remove("tenant_beta.db")
        
        # Clear context
        tenant_context.set_tenant(None)

    def test_session_switches_database_per_tenant(self):
        """Verify the session connects to the correct DB for each tenant."""
        
        # 1. Work with Tenant Alpha
        tenant_context.set_tenant("alpha")
        session_alpha = self.Session()
        
        # Assert the engine is connected to the correct database file
        db_file_alpha = str(session_alpha.get_bind().url.database)
        assert db_file_alpha == "tenant_alpha.db"

        # Create a simple table and add data
        session_alpha.execute(text("CREATE TABLE IF NOT EXISTS data (id INT, value TEXT)"))
        session_alpha.execute(text("INSERT INTO data VALUES (1, 'alpha_data')"))
        session_alpha.commit()

        # Verify data
        result_alpha = session_alpha.execute(text("SELECT value FROM data WHERE id = 1")).scalar()
        assert result_alpha == "alpha_data"
        self.Session.remove() # Close session

        # 2. Switch to Tenant Beta
        tenant_context.set_tenant("beta")
        session_beta = self.Session()

        # Assert the engine is connected to a DIFFERENT database file
        db_file_beta = str(session_beta.get_bind().url.database)
        assert db_file_beta == "tenant_beta.db"

        # The table from alpha should not exist here yet
        with pytest.raises(Exception):
            session_beta.execute(text("SELECT value FROM data WHERE id = 1")).scalar()
        session_beta.rollback() # Rollback the failed query

        # Create the table and add beta's data
        session_beta.execute(text("CREATE TABLE IF NOT EXISTS data (id INT, value TEXT)"))
        session_beta.execute(text("INSERT INTO data VALUES (1, 'beta_data')"))
        session_beta.commit()

        # Verify beta's data
        result_beta = session_beta.execute(text("SELECT value FROM data WHERE id = 1")).scalar()
        assert result_beta == "beta_data"
        self.Session.remove() # Close session
