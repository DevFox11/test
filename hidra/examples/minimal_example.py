"""
Ejemplo de uso mínimo de Hidra con FastAPI

Este ejemplo demuestra cómo usar Hidra con la mínima configuración posible
"""
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

# Importar solo lo necesario para configuración mínima
from hidra import create_hidra_app

# Crear aplicación con configuración mínima
app = FastAPI()

# Configurar Hidra con configuración mínima
# Solo se necesita especificar la configuración de base de datos
app = create_hidra_app(
    app=app,
    db_config={
        "db_driver": "sqlite",
        "db_name": "example.db"  # Usar :memory: para pruebas
    },
    # La estrategia por defecto es SCHEMA_PER_TENANT
    # Los tenants se cargarán automáticamente cuando se soliciten
)

# Endpoint protegido - no es necesario definir tenants en código
@app.get("/data")
async def get_tenant_data():
    from hidra import get_current_tenant_id
    
    # El ID del tenant actual está disponible automáticamente
    tenant_id = get_current_tenant_id()
    
    return {
        "tenant_id": tenant_id,
        "message": "Datos del tenant obtenidos exitosamente",
        "note": "El tenant se validó automáticamente"
    }

# Endpoint que usa base de datos del tenant actual
@app.get("/users")
async def get_tenant_users():
    from hidra import get_current_tenant_id
    
    tenant_id = get_current_tenant_id()
    
    # Aquí iría la lógica para obtener usuarios del tenant actual
    # usando la sesión de base de datos correspondiente al tenant
    return {
        "tenant_id": tenant_id,
        "users": [],
        "message": "Lista de usuarios del tenant actual"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)