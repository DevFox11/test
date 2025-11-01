"""
Módulo para la gestión de schemas y tablas en la estrategia SCHEMA_PER_TENANT
"""
from typing import Dict, Any, Optional
import re
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker
from .core import tenant_context, TenancyStrategy
from .database import MultiTenantSession
from .exceptions import InvalidTenantNameError


class SchemaManager:
    """
    Gestiona la creación y mantenimiento de schemas y tablas para tenants
    """
    
    def __init__(self, base_config: Dict[str, Any]):
        self.base_config = base_config
        # Conexión al schema público
        self.engine = self._create_public_engine()
        self.sessionmaker = sessionmaker(bind=self.engine)

    def _create_public_engine(self):
        """Crea un engine para conexión al schema público"""
        driver = self.base_config.get("db_driver", "postgresql")
        host = self.base_config.get("db_host", "localhost")
        port = self.base_config.get("db_port", "5432")
        username = self.base_config.get("db_username", "postgres")
        password = self.base_config.get("db_password", "password")
        database = self.base_config.get("db_name", "multitenant_db")
        
        connection_string = f"{driver}://{username}:{password}@{host}:{port}/{database}"
        return create_engine(connection_string)

    def create_public_schema_if_not_exists(self):
        """Crea el schema público si no existe (para bases de datos que lo requieran)"""
        with self.engine.connect() as conn:
            # En PostgreSQL, el schema 'public' existe por defecto, pero aseguramos que esté disponible
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
            conn.commit()

    def create_tenants_table(self, custom_sql: str = None):
        """
        Crea la tabla tenants en el schema público
        NOTA: Esta función está aquí para conveniencia, pero se RECOMIENDA
        que el desarrollador cree su propia tabla tenants con la estructura
        que mejor se adapte a sus necesidades de negocio. Esta función
        solo proporciona una estructura base mínima si se necesita para
        casos de uso muy simples.
        """
        with self.engine.connect() as conn:
            if custom_sql:
                # Si se proporciona SQL personalizado, usarlo
                conn.execute(text(custom_sql))
            else:
                # Mostrar advertencia si se usa la estructura por defecto
                print("Advertencia: Se está usando la estructura por defecto para la tabla tenants.")
                print("Se recomienda definir una tabla personalizada acorde a las necesidades del negocio.")
                
                # Usar SQL por defecto si no se proporciona personalizado
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS public.tenants (
                        id VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status VARCHAR(50) DEFAULT 'active'
                    )
                """))
            conn.commit()

    def validate_tenant_name(self, tenant_id: str) -> bool:
        """Valida que el nombre del tenant sea válido para usar como nombre de schema en PostgreSQL"""
        # PostgreSQL solo permite letras, números y guiones bajos en nombres de schema
        # No permite guiones (-), puntos (.), espacios u otros caracteres especiales
        # El nombre debe comenzar con una letra o guion bajo
        
        # Comprobar si contiene caracteres inválidos
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', tenant_id):
            return False
            
        # Comprobar longitud (máximo 63 caracteres en PostgreSQL)
        if len(tenant_id) > 63:
            return False
            
        return True

    def clean_tenant_name(self, tenant_id: str) -> str:
        """Limpia el nombre del tenant reemplazando caracteres no válidos para schemas"""
        # PostgreSQL no permite guiones (-) en nombres de schema
        # Reemplazamos guiones por guiones bajos
        cleaned_name = tenant_id.replace("-", "_")
        
        # Asegurar que comience con una letra o guion bajo
        if cleaned_name and not re.match(r'^[a-zA-Z_]', cleaned_name):
            cleaned_name = f"tenant_{cleaned_name}"
            
        return cleaned_name

    def create_tenant_schema(self, tenant_id: str, strict_validation: bool = False):
        """Crea un schema para un tenant específico"""
        # Validar el nombre del tenant
        if not self.validate_tenant_name(tenant_id):
            if strict_validation:
                raise InvalidTenantNameError(tenant_id, "El nombre contiene caracteres inválidos para un schema de PostgreSQL.")
            
            # Limpiar el nombre del tenant para que sea válido como nombre de schema
            clean_tenant_name = self.clean_tenant_name(tenant_id)
        else:
            clean_tenant_name = tenant_id
        
        with self.engine.connect() as conn:
            # Usamos comillas dobles para permitir nombres que pueden haber sido limpiados
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{clean_tenant_name}"'))
            conn.commit()

    def create_tables_in_tenant_schema(self, tenant_id: str, create_tables_func, strict_validation: bool = False):
        """Ejecuta la creación de tablas en el schema del tenant"""
        # Validar y limpiar el nombre del tenant
        if not self.validate_tenant_name(tenant_id):
            if strict_validation:
                raise InvalidTenantNameError(tenant_id, "El nombre contiene caracteres inválidos para un schema de PostgreSQL.")
            
            clean_tenant_name = self.clean_tenant_name(tenant_id)
        else:
            clean_tenant_name = tenant_id
        
        # Obtener una sesión específica para este tenant
        db_config = self.base_config.copy()
        multi_tenant_session = MultiTenantSession(db_config, TenancyStrategy.SCHEMA_PER_TENANT)
        
        # Establecer el contexto del tenant
        original_tenant = tenant_context.get_tenant()
        try:
            tenant_context.set_tenant(tenant_id)
            
            # Obtener sesión ya configurada para este tenant (con search_path)
            session = multi_tenant_session.get_session()
            
            # Ejecutar la función de creación de tablas
            if create_tables_func:
                create_tables_func(session, tenant_id)
            
            session.commit()
        finally:
            # Restaurar el tenant original
            tenant_context.set_tenant(original_tenant)

    def initialize_tenant(self, tenant_id: str, tenant_name: str = None, create_tables_func=None, strict_validation: bool = False, register_tenant=True):
        """Inicializa un nuevo tenant creando su schema y opcionalmente registrándolo"""
        if tenant_name is None:
            tenant_name = tenant_id
            
        # Validar el nombre de tenant antes de crear el schema
        if not self.validate_tenant_name(tenant_id):
            if strict_validation:
                raise InvalidTenantNameError(tenant_id, "El nombre contiene caracteres inválidos para un schema de PostgreSQL.")
            
            # Si el nombre no es válido, usar la versión limpiada para el schema
            cleaned_schema_name = self.clean_tenant_name(tenant_id)
            print(f"Advertencia: El nombre de tenant '{tenant_id}' no es válido para PostgreSQL. "
                  f"Se usará '{cleaned_schema_name}' para el schema, pero se registrará con el nombre original.")
        
        # Crear el schema para el tenant
        self.create_tenant_schema(tenant_id, strict_validation=strict_validation)
        
        # Registrar el tenant en la tabla pública con el ID original (opcional)
        if register_tenant:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO public.tenants (id, name, status) 
                    VALUES (:id, :name, :status)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        updated_at = CURRENT_TIMESTAMP,
                        status = EXCLUDED.status
                """), {"id": tenant_id, "name": tenant_name, "status": "active"})
                conn.commit()
        
        # Crear tablas en el schema del tenant si se proporciona la función
        if create_tables_func:
            self.create_tables_in_tenant_schema(tenant_id, create_tables_func, strict_validation=strict_validation)

    def setup_multi_tenant_environment(self, create_tables_func=None, create_tenants_table: bool = True, tenants_table_sql: str = None):
        """Configura el entorno multitenant completo"""
        # Asegurar que exista el schema público
        self.create_public_schema_if_not_exists()
        
        # Crear la tabla tenants en el schema público si se solicita
        if create_tenants_table:
            self.create_tenants_table(custom_sql=tenants_table_sql)
        
        # Si se proporciona una función para crear tablas, se puede usar más tarde
        # para inicializar tenants específicos
        pass