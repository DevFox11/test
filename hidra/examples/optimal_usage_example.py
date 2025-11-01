"""
Ejemplo de uso óptimo de Hidra: Balance entre facilidad y flexibilidad
"""
from fastapi import FastAPI
from hidra import initialize_hidra_fastapi, SchemaManager

# Ejemplo 1: Uso simple con valores por defecto (mínima configuración)
def create_simple_app():
    """Creación de aplicación con configuración mínima"""
    app = FastAPI(title="Mi App Multitenant - Simple")
    
    db_config = {
        "db_driver": "postgresql",
        "db_host": "localhost", 
        "db_port": "5432",
        "db_username": "postgres",
        "db_password": "password",
        "db_name": "my_multitenant_db"
    }
    
    # Con esta sola llamada, se configura todo el sistema multitenant
    app = initialize_hidra_fastapi(
        app=app,
        db_config=db_config
    )
    
    @app.get("/data")
    async def get_data():
        from hidra import get_current_tenant_id
        tenant_id = get_current_tenant_id()
        return {"tenant_id": tenant_id, "message": "Datos del tenant actual"}
    
    return app


# Ejemplo 2: Uso con personalización controlada (estructura de tenants personalizada)
def create_custom_app():
    """Creación de aplicación con control total sobre la estructura de tenants"""
    app = FastAPI(title="Mi App Multitenant - Personalizada")
    
    db_config = {
        "db_driver": "postgresql",
        "db_host": "localhost",
        "db_port": "5432", 
        "db_username": "postgres",
        "db_password": "password",
        "db_name": "my_multitenant_db"
    }
    
    # Inicializar Hidra con configuración mínima
    app = initialize_hidra_fastapi(
        app=app,
        db_config=db_config,
        include_tenant_registration=False  # No incluir el endpoint por defecto
    )
    
    # Ahora el desarrollador puede definir su propia tabla tenants y lógica
    # usando directamente SchemaManager para operaciones específicas
    schema_manager = app.state.schema_manager
    
    @app.post("/register-business-tenant")
    async def register_business_tenant(tenant_data: dict):
        """Endpoint personalizado para registro de tenant con lógica de negocio"""
        from sqlalchemy import create_engine, text
        
        # El desarrollador controla completamente el proceso
        tenant_id = tenant_data["subdomain"]
        business_name = tenant_data["business_name"]
        
        # Usar schema manager para crear el schema, pero no registrar en tenants
        schema_manager.initialize_tenant(
            tenant_id=tenant_id,
            tenant_name=business_name,
            register_tenant=False  # El desarrollador manejará el registro personalizado
        )
        
        # Lógica personalizada de registro en tabla personalizada
        # (esto sería implementado por el desarrollador según su estructura)
        engine = create_engine(f"postgresql://postgres:password@localhost:5432/my_multitenant_db")
        with engine.connect() as conn:
            # Aquí el desarrollador usaría su propia tabla con su estructura personalizada
            pass
        
        return {"message": f"Tenant {tenant_id} registrado con éxito", "id": tenant_id}
    
    @app.get("/data")
    async def get_data():
        from hidra import get_current_tenant_id
        tenant_id = get_current_tenant_id()
        return {"tenant_id": tenant_id, "message": "Datos del tenant actual"}
    
    return app


# Ejemplo 3: Uso híbrido - conveniencia con flexibilidad
def create_hybrid_app():
    """Creación de aplicación que usa conveniencia de Hidra pero permite personalización"""
    app = FastAPI(title="Mi App Multitenant - Híbrida")
    
    db_config = {
        "db_driver": "postgresql",
        "db_host": "localhost",
        "db_port": "5432",
        "db_username": "postgres", 
        "db_password": "password",
        "db_name": "my_multitenant_db"
    }
    
    # Inicializar con la funcionalidad de conveniencia
    app = initialize_hidra_fastapi(
        app=app,
        db_config=db_config,
        include_tenant_registration=True  # Incluir endpoint de registro
    )
    
    # Puedes acceder al schema manager para operaciones avanzadas
    schema_manager = app.state.schema_manager
    
    @app.get("/advanced-operation")
    async def advanced_operation():
        # Ejemplo de operación avanzada usando SchemaManager directamente
        is_valid = schema_manager.validate_tenant_name("my-company")
        clean_name = schema_manager.clean_tenant_name("my-company")
        
        return {
            "original_name": "my-company",
            "is_valid_for_postgres": is_valid,
            "clean_name_for_schema": clean_name
        }
    
    @app.get("/data")
    async def get_data():
        from hidra import get_current_tenant_id
        tenant_id = get_current_tenant_id()
        return {"tenant_id": tenant_id, "message": "Datos del tenant actual"}
    
    return app


if __name__ == "__main__":
    print("Ejemplos de uso de Hidra con balance entre facilidad y flexibilidad:")
    print()
    print("1. Uso simple: initialize_hidra_fastapi() - Mínima configuración")
    print("2. Uso personalizado: Control total sobre la estructura de tenants")
    print("3. Uso híbrido: Conveniencia + Flexibilidad")
    print()
    print("La librería permite:")
    print("- Estructura de tenants definida por el desarrollador")
    print("- Validación automática de nombres de schemas")
    print("- Creación automática de schemas por tenant")
    print("- Funciones de conveniencia para casos simples")
    print("- Control total para casos complejos")