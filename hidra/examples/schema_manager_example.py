"""
Ejemplo de uso de SchemaManager para resolver los problemas de Hidra
"""
from sqlalchemy.orm import sessionmaker
from hidra import create_hidra_app, SchemaManager, TenancyStrategy
from fastapi import FastAPI, Depends
from sqlalchemy import text


def create_sample_tables(session, tenant_id):
    """
    Función de ejemplo para crear tablas en el schema del tenant
    """
    print(f"Creando tablas para el tenant: {tenant_id}")
    
    # Crear una tabla de ejemplo para el tenant
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


def setup_multitenant_db():
    """
    Configura la base de datos multitenant con la nueva funcionalidad
    """
    # Configuración de la base de datos
    db_config = {
        "db_driver": "postgresql",
        "db_host": "localhost",
        "db_port": "5432",
        "db_username": "postgres",
        "db_password": "password",
        "db_name": "multitenant_db"
    }
    
    # Crear instancia de SchemaManager
    schema_manager = SchemaManager(db_config)
    
    # Configurar el entorno multitenant
    schema_manager.setup_multi_tenant_environment()
    
    # Ejemplo 1: Crear tenants con nombres que contienen guiones
    # El SchemaManager manejará estos nombres correctamente
    tenants_to_create = [
        {"id": "company-1", "name": "Company One"},
        {"id": "company-2", "name": "Company Two"},
        {"id": "test-tenant", "name": "Test Tenant"},
        {"id": "my_awesome_tenant", "name": "My Awesome Tenant"}
    ]
    
    # Crear cada tenant
    for tenant_data in tenants_to_create:
        print(f"\nCreando tenant: {tenant_data['id']}")
        
        # El SchemaManager manejará automáticamente los guiones en el nombre del tenant
        schema_manager.initialize_tenant(
            tenant_id=tenant_data['id'],
            tenant_name=tenant_data['name'],
            create_tables_func=create_sample_tables  # Pasamos la función para crear tablas en el schema del tenant
        )
        print(f"Tenant {tenant_data['id']} creado exitosamente!")


def example_fastapi_integration():
    """
    Ejemplo de cómo integrar con FastAPI
    """
    app = FastAPI()
    
    db_config = {
        "db_driver": "postgresql",
        "db_host": "localhost",
        "db_port": "5432",
        "db_username": "postgres",
        "db_password": "password",
        "db_name": "multitenant_db"
    }
    
    # Configurar Hidra con FastAPI
    app = create_hidra_app(
        app=app,
        db_config=db_config,
        strategy=TenancyStrategy.SCHEMA_PER_TENANT
    )
    
    # Crear SchemaManager para manejar creación de schemas y tablas
    schema_manager = SchemaManager(db_config)
    
    # Configurar el entorno multitenant
    schema_manager.setup_multi_tenant_environment()
    
    @app.get("/setup-tenant/{tenant_id}")
    async def setup_tenant(tenant_id: str):
        """
        Endpoint para crear un nuevo tenant
        """
        try:
            # Validar que el nombre de tenant sea apropiado
            if not schema_manager.validate_tenant_name(tenant_id):
                cleaned_name = schema_manager.clean_tenant_name(tenant_id)
                return {
                    "message": f"Nombre de tenant '{tenant_id}' no es válido para PostgreSQL, se usará '{cleaned_name}' para el schema",
                    "original_id": tenant_id,
                    "schema_name": cleaned_name
                }
            
            # Inicializar el tenant
            schema_manager.initialize_tenant(
                tenant_id=tenant_id,
                tenant_name=tenant_id,
                create_tables_func=create_sample_tables
            )
            
            return {"message": f"Tenant {tenant_id} creado exitosamente!", "id": tenant_id}
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/health")
    async def health():
        return {"status": "ok", "library": "hidra with schema manager"}
    
    return app


if __name__ == "__main__":
    # Ejecutar ejemplo de configuración de base de datos
    setup_multitenant_db()
    
    # Para ejecutar la aplicación FastAPI:
    # import uvicorn
    # app = example_fastapi_integration()
    # uvicorn.run(app, host="0.0.0.0", port=8000)