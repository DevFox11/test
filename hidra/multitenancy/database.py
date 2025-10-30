from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .core import tenant_context

class MultiTenantSession:
    def __init__(self, base_config: dict):
        self.base_config = base_config
        self.engines = {}
        self.session_makers = {}
    
    def get_engine(self, tenant_id: str):
        """Get or create SQLAlchemy engine for a tenant"""
        if tenant_id not in self.engines:
            db_url = self._build_connection_string(tenant_id)
            self.engines[tenant_id] = create_engine(
                db_url, 
                pool_pre_ping=True,
                echo=self.base_config.get('echo_sql', False)
            )
        return self.engines[tenant_id]
    
    def get_session(self) -> Session:
        """Create a database session for the current tenant"""
        tenant_id = tenant_context.require_tenant()
        
        if tenant_id not in self.session_makers:
            engine = self.get_engine(tenant_id)
            self.session_makers[tenant_id] = sessionmaker(bind=engine)
        
        return self.session_makers[tenant_id]()
    
    def _build_connection_string(self, tenant_id: str) -> str:
        """Build database connection string based on strategy"""
        driver = self.base_config.get('db_driver', 'sqlite')
        
        if driver == 'sqlite':
            # ✅ CORREGIDO: SQLite usa formato simple
            return f"sqlite:///tenant_{tenant_id}.db"
        else:
            # Para PostgreSQL/MySQL
            host = self.base_config.get('db_host', 'localhost')
            port = self.base_config.get('db_port', '5432')
            username = self.base_config.get('db_username', 'postgres')
            password = self.base_config.get('db_password', 'password')
            database = f"{self.base_config.get('db_prefix', '')}{tenant_id}"
            
            return f"{driver}://{username}:{password}@{host}:{port}/{database}"
    
    def close_all_connections(self):
        """Close all database connections"""
        for engine in self.engines.values():
            engine.dispose()
        self.engines.clear()
        self.session_makers.clear()