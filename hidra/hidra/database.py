from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from .core import tenant_context, TenancyStrategy
from typing import Dict, Any, Optional

class MultiTenantSession:
    """
    Gestiona sesiones de base de datos para múltiples estrategias de multitenancy
    """

    def __init__(self, base_config: Dict[str, Any], strategy: TenancyStrategy = None):
        self.base_config = base_config
        self.strategy = strategy or tenant_context.tenant_manager.default_strategy
        self.engines = {}
        self.session_makers = {}

    def get_session(self) -> Session:
        """Obtiene una sesión de base de datos según la estrategia configurada"""
        tenant_id = tenant_context.require_tenant()

        if self.strategy == TenancyStrategy.DATABASE_PER_TENANT:
            return self._get_database_session(tenant_id)
        elif self.strategy == TenancyStrategy.SCHEMA_PER_TENANT:
            return self._get_schema_session(tenant_id)
        elif self.strategy == TenancyStrategy.ROW_LEVEL:
            return self._get_row_level_session(tenant_id)
        else:
            raise ValueError(f"Estrategia no soportada: {self.strategy}")

    def _get_database_session(self, tenant_id: str) -> Session:
        if tenant_id not in self.session_makers:
            db_url = self._build_database_connection_string(tenant_id)
            engine = create_engine(
                db_url, pool_pre_ping=True, echo=self.base_config.get("echo_sql", False)
            )
            self.engines[tenant_id] = engine
            self.session_makers[tenant_id] = sessionmaker(bind=engine)
        return self.session_makers[tenant_id]()

    def _get_schema_session(self, tenant_id: str) -> Session:
        if tenant_id not in self.session_makers:
            db_url = self._build_schema_connection_string(tenant_id)
            engine = create_engine(
                db_url, pool_pre_ping=True, echo=self.base_config.get("echo_sql", False)
            )
            # Configurar búsqueda de esquema para el tenant
            with engine.connect() as conn:
                conn.execute(text(f"SET search_path TO tenant_{tenant_id}, public"))
                conn.commit()
            self.engines[tenant_id] = engine
            self.session_makers[tenant_id] = sessionmaker(bind=engine)
        return self.session_makers[tenant_id]()

    def _get_row_level_session(self, tenant_id: str) -> Session:
        if tenant_id not in self.session_makers:
            db_url = self._build_row_level_connection_string()
            engine = create_engine(
                db_url, pool_pre_ping=True, echo=self.base_config.get("echo_sql", False)
            )
            self.engines[tenant_id] = engine
            # Crear session maker personalizado que inyecta tenant_id en las consultas
            def tenant_aware_sessionmaker(**kwargs):
                session = sessionmaker(bind=engine)(**kwargs)
                # Establecer el tenant_id en el contexto de la sesión para RLS
                session.current_tenant = tenant_id
                return session
            self.session_makers[tenant_id] = tenant_aware_sessionmaker
        return self.session_makers[tenant_id]()

    def _build_database_connection_string(self, tenant_id: str) -> str:
        driver = self.base_config.get("db_driver", "sqlite")
        if driver == "sqlite":
            return f"sqlite:///tenant_{tenant_id}.db"
        else:
            host = self.base_config.get("db_host", "localhost")
            port = self.base_config.get("db_port", "5432")
            username = self.base_config.get("db_username", "postgres")
            password = self.base_config.get("db_password", "password")
            database = f"tenant_{tenant_id}"
            return f"{driver}://{username}:{password}@{host}:{port}/{database}"

    def _build_schema_connection_string(self, tenant_id: str) -> str:
        driver = self.base_config.get("db_driver", "postgresql")  # Normalmente PostgreSQL para schemas
        host = self.base_config.get("db_host", "localhost")
        port = self.base_config.get("db_port", "5432")
        username = self.base_config.get("db_username", "postgres")
        password = self.base_config.get("db_password", "password")
        database = self.base_config.get("db_name", "multitenant_db")
        return f"{driver}://{username}:{password}@{host}:{port}/{database}"

    def _build_row_level_connection_string(self) -> str:
        driver = self.base_config.get("db_driver", "postgresql")  # Normalmente PostgreSQL para RLS
        host = self.base_config.get("db_host", "localhost")
        port = self.base_config.get("db_port", "5432")
        username = self.base_config.get("db_username", "postgres")
        password = self.base_config.get("db_password", "password")
        database = self.base_config.get("db_name", "multitenant_db")
        return f"{driver}://{username}:{password}@{host}:{port}/{database}"

    def close_all_connections(self):
        """Cierra todas las conexiones de base de datos"""
        for engine in self.engines.values():
            engine.dispose()
        self.engines.clear()
        self.session_makers.clear()

def create_tenant_aware_session(base_config: Dict[str, Any], strategy: TenancyStrategy = None) -> scoped_session:
    """
    Creates and returns a tenant-aware SQLAlchemy scoped_session.
    """
    multi_tenant_session_manager = MultiTenantSession(base_config, strategy)

    def scopefunc() -> Optional[str]:
        return tenant_context.get_tenant()

    TenantAwareSession = scoped_session(
        multi_tenant_session_manager.get_session,
        scopefunc=scopefunc
    )
    
    # Attach the close method to the session factory for easy access
    TenantAwareSession.close_all = multi_tenant_session_manager.close_all_connections

    return TenantAwareSession