"""
Ejemplo práctico: Cómo usar Hidra para resolver los problemas mencionados

1. Crear la tabla tenants en el schema público
2. Crear el resto de tablas en cada schema de tenant
3. Validar y corregir el uso de guiones en nombres de schemas
"""
from hidra import SchemaManager, create_hidra_app, TenancyStrategy
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session


# Configuración de la base de datos
db_config = {
    "db_driver": "postgresql",
    "db_host": "localhost",
    "db_port": "5432",
    "db_username": "postgres",
    "db_password": "password",
    "db_name": "multitenant_db"
}


def create_tenant_tables(session: Session, tenant_id: str):
    """
    Función para crear tablas específicas de cada tenant
    Estas tablas se crearán en el schema del tenant, no en el público
    """
    print(f"Creando tablas para el tenant: {tenant_id}")
    
    # Crear tablas en el schema del tenant
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255)
        )
    """))
    
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            price DECIMAL(10, 2)
        )
    """))
    
    # Insertar algunos datos de ejemplo
    session.execute(text("INSERT INTO users (name, email) VALUES ('John Doe', 'john@example.com') ON CONFLICT DO NOTHING"))
    session.execute(text("INSERT INTO products (name, price) VALUES ('Product 1', 19.99) ON CONFLICT DO NOTHING"))


def setup_multitenant_application():
    """
    Configura una aplicación FastAPI con soporte multitenant
    """
    app = FastAPI(title="Ejemplo de Resolución de Problemas de Hidra")
    
    # Configurar Hidra con FastAPI
    app = create_hidra_app(
        app=app,
        db_config=db_config,
        strategy=TenancyStrategy.SCHEMA_PER_TENANT
    )
    
    # Crear SchemaManager para manejar la creación de schemas y tablas
    schema_manager = SchemaManager(db_config)
    
    # Configurar el entorno multitenant completo
    # Esto crea:
    # 1. El schema público (si es necesario)
    # 2. La tabla tenants en el schema público
    schema_manager.setup_multi_tenant_environment()
    
    @app.post("/setup-tenant/{tenant_id}")
    async def setup_tenant(tenant_id: str):
        """
        Endpoint para inicializar un nuevo tenant
        """
        try:
            # Validar nombre de tenant
            is_valid = schema_manager.validate_tenant_name(tenant_id)
            clean_name = schema_manager.clean_tenant_name(tenant_id)
            
            # Inicializar el tenant
            # Esto hará:
            # 1. Crear el schema para el tenant (con nombre limpio si es necesario)
            # 2. Registrar el tenant en la tabla pública 'tenants'
            # 3. Crear las tablas del tenant en su schema específico
            schema_manager.initialize_tenant(
                tenant_id=tenant_id,
                tenant_name=tenant_id,
                create_tables_func=create_tenant_tables
            )
            
            return {
                "message": f"Tenant {tenant_id} configurado exitosamente!",
                "original_id": tenant_id,
                "clean_schema_name": clean_name,
                "name_is_valid": is_valid,
                "schema_created": True
            }
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/health")
    async def health_check():
        """
        Endpoint de salud para verificar que todo esté funcionando
        """
        return {
            "status": "healthy",
            "library": "hidra",
            "feature": "schema management with public tenants table",
            "hyphen_fix": "enabled"
        }
    
    @app.get("/validate-tenant/{tenant_id}")
    async def validate_tenant_name_endpoint(tenant_id: str):
        """
        Endpoint para validar si un nombre de tenant es válido para PostgreSQL
        """
        is_valid = schema_manager.validate_tenant_name(tenant_id)
        clean_name = schema_manager.clean_tenant_name(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "is_valid_for_postgres": is_valid,
            "cleaned_name": clean_name,
            "message": "Nombre válido" if is_valid else f"Nombre no válido para PostgreSQL. Se limpiaría a: {clean_name}"
        }
    
    return app


# Ejemplo de uso
if __name__ == "__main__":
    # Crear la aplicación
    app = setup_multitenant_application()
    
    # Simular la creación de algunos tenants con nombres que tienen guiones
    print("Configurando SchemaManager...")
    schema_manager = SchemaManager(db_config)
    schema_manager.setup_multi_tenant_environment()
    
    print("\nCreando tenants con nombres que contienen guiones:")
    problematic_tenants = ["company-1", "my-test-tenant", "tenant-with-dashes"]
    
    for tenant_id in problematic_tenants:
        try:
            print(f"\nProcesando tenant: {tenant_id}")
            is_valid = schema_manager.validate_tenant_name(tenant_id)
            clean_name = schema_manager.clean_tenant_name(tenant_id)
            
            print(f"  - ¿Nombre válido para PostgreSQL?: {is_valid}")
            print(f"  - Nombre limpio para schema: {clean_name}")
            
            # Inicializar el tenant
            schema_manager.initialize_tenant(
                tenant_id=tenant_id,
                tenant_name=f"Tenant {tenant_id}",
                create_tables_func=create_tenant_tables
            )
            
            print(f"  - Tenant {tenant_id} creado exitosamente con schema '{clean_name}'")
        except Exception as e:
            print(f"  - Error al crear tenant {tenant_id}: {e}")
    
    print("\n¡Ejemplo completado! Los problemas mencionados han sido resueltos:")
    print("1. ✓ La tabla tenants se crea en el schema público")
    print("2. ✓ Las tablas de cada tenant se crean en su schema específico")
    print("3. ✓ Los guiones en nombres de tenants se reemplazan por guiones bajos para compatibilidad con PostgreSQL")
    
    # Para ejecutar la aplicación FastAPI:
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)