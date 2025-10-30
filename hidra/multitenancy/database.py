from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session  # ✅ Añadir Session aquí
from .core import tenant_context, TenancyStrategy
from typing import Dict, Any

class MultiTenantSession:
    """
    Gestiona sesiones de base de datos para múltiples estrategias de multitenancy
    """
    
    def __init__(self, base_config: Dict[str, Any], strategy: TenancyStrategy = None):
        self.base_config = base_config
        self.strategy = strategy or tenant_context.tenant_manager.default_strategy
        self.engines = {}
        self.session_makers = {}
        
        print(f"🔧 MultiTenantSession configurado con estrategia: {self.strategy.value}")
    
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
        """Estrategia: Base de datos separada por tenant"""
        if tenant_id not in self.session_makers:
            db_url = self._build_database_connection_string(tenant_id)
            engine = create_engine(
                db_url, 
                pool_pre_ping=True,
                echo=self.base_config.get('echo_sql', False)
            )
            self.engines[tenant_id] = engine
            self.session_makers[tenant_id] = sessionmaker(bind=engine)
        
        return self.session_makers[tenant_id]()
    
    def _get_schema_session(self, tenant_id: str) -> Session:
        """Estrategia: Misma base de datos, schema diferente por tenant"""
        driver = self.base_config.get('db_driver', 'sqlite')
        
        if driver == 'sqlite':
            # Para SQLite: usar tablas con prefijo (fallback)
            return self._get_sqlite_schema_session(tenant_id)
        else:
            # Para PostgreSQL: usar schemas reales
            return self._get_postgres_schema_session(tenant_id)
    
    def _get_postgres_schema_session(self, tenant_id: str) -> Session:
        """PostgreSQL: Schemas reales por tenant"""
        # ✅ CORREGIDO: Usar una clave única por tenant para session_makers
        session_key = f"schema_{tenant_id}"
        
        if session_key not in self.session_makers:
            # Crear engine base para estrategia de schema si no existe
            if 'postgres_schema_engine' not in self.engines:
                db_url = self._build_schema_connection_string()
                self.engines['postgres_schema_engine'] = create_engine(
                    db_url,
                    pool_pre_ping=True,
                    echo=self.base_config.get('echo_sql', True)
                )
            
            # Crear session maker para este tenant específico
            self.session_makers[session_key] = sessionmaker(bind=self.engines['postgres_schema_engine'])
        
        session = self.session_makers[session_key]()
        
        # Establecer el schema para esta sesión
        schema_name = f"tenant_{tenant_id}"
        try:
            session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            session.execute(text(f"SET search_path TO {schema_name}"))
            session.commit()
        except Exception as e:
            session.rollback()
            # Si hay error al establecer schema, recrear la sesión
            session.close()
            del self.session_makers[session_key]
            raise e
        
        return session
    
    def _get_sqlite_schema_session(self, tenant_id: str) -> Session:
        """SQLite: Fallback para desarrollo"""
        if 'sqlite_schema_engine' not in self.engines:
            db_url = "sqlite:///multitenant_schema.db"
            self.engines['sqlite_schema_engine'] = create_engine(
                db_url,
                pool_pre_ping=True,
                echo=self.base_config.get('echo_sql', True)
            )
            self.session_makers['sqlite_schema'] = sessionmaker(bind=self.engines['sqlite_schema_engine'])
        
        return self.session_makers['sqlite_schema']()
    
    def _get_row_level_session(self, tenant_id: str) -> Session:
        """Estrategia: Misma tabla, filtrado por tenant_id"""
        if 'row_level_engine' not in self.engines:
            db_url = self._build_row_level_connection_string()
            self.engines['row_level_engine'] = create_engine(
                db_url,
                pool_pre_ping=True,
                echo=self.base_config.get('echo_sql', False)
            )
            self.session_makers['row_level'] = sessionmaker(bind=self.engines['row_level_engine'])
        
        return self.session_makers['row_level']()
    
    def _build_database_connection_string(self, tenant_id: str) -> str:
        """Construye connection string para estrategia de base de datos por tenant"""
        driver = self.base_config.get('db_driver', 'sqlite')
        
        if driver == 'sqlite':
            return f"sqlite:///tenant_{tenant_id}.db"
        else:
            host = self.base_config.get('db_host', 'localhost')
            port = self.base_config.get('db_port', '5432')
            username = self.base_config.get('db_username', 'postgres')
            password = self.base_config.get('db_password', 'password')
            database = f"tenant_{tenant_id}"
            
            return f"{driver}://{username}:{password}@{host}:{port}/{database}"
    
    def _build_schema_connection_string(self) -> str:
        """Construye connection string para estrategia de schema por tenant"""
        driver = self.base_config.get('db_driver', 'sqlite')
        
        if driver == 'sqlite':
            # SQLite no soporta schemas, usamos archivo único
            return "sqlite:///multitenant_schema.db"
        else:
            host = self.base_config.get('db_host', 'localhost')
            port = self.base_config.get('db_port', '5432')
            username = self.base_config.get('db_username', 'postgres')
            password = self.base_config.get('db_password', 'password')
            database = self.base_config.get('db_name', 'multitenant_db')
            
            return f"{driver}://{username}:{password}@{host}:{port}/{database}"
    
    def _build_row_level_connection_string(self) -> str:
        """Construye connection string para estrategia row level"""
        driver = self.base_config.get('db_driver', 'sqlite')
        
        if driver == 'sqlite':
            return "sqlite:///multitenant_row_level.db"
        else:
            host = self.base_config.get('db_host', 'localhost')
            port = self.base_config.get('db_port', '5432')
            username = self.base_config.get('db_username', 'postgres')
            password = self.base_config.get('db_password', 'password')
            database = self.base_config.get('db_name', 'multitenant_db')
            
            return f"{driver}://{username}:{password}@{host}:{port}/{database}"
    
    def get_engine(self, tenant_id: str):
        """Obtiene el engine específico para un tenant (útil para migraciones)"""
        if self.strategy == TenancyStrategy.DATABASE_PER_TENANT:
            if tenant_id not in self.engines:
                db_url = self._build_database_connection_string(tenant_id)
                self.engines[tenant_id] = create_engine(db_url)
            return self.engines[tenant_id]
        elif self.strategy == TenancyStrategy.SCHEMA_PER_TENANT:
            if 'postgres_schema_engine' not in self.engines:
                db_url = self._build_schema_connection_string()
                self.engines['postgres_schema_engine'] = create_engine(db_url)
            return self.engines['postgres_schema_engine']
        else:  # ROW_LEVEL
            if 'row_level_engine' not in self.engines:
                db_url = self._build_row_level_connection_string()
                self.engines['row_level_engine'] = create_engine(db_url)
            return self.engines['row_level_engine']
    
    def close_all_connections(self):
        """Cierra todas las conexiones de base de datos"""
        for engine in self.engines.values():
            engine.dispose()
        self.engines.clear()
        self.session_makers.clear()