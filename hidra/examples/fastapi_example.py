"""
Ejemplo de integración completa con FastAPI
"""
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from hidra import create_hidra_app, requires_tenant, get_current_tenant_id

# Crear aplicación FastAPI con configuración mínima
app = create_hidra_app(
    db_config={
        "db_driver": "sqlite",
        "db_name": "fastapi_example.db" 
    },
    # Los tenants se cargarán automáticamente cuando se necesiten
    enable_auto_loading=True,
    auto_tenant_validation=True  # Validar que los tenants existan
)

# Endpoint protegido con el nuevo decorador
@app.get("/users")
@requires_tenant()  # Requiere tenant (se valida automáticamente)
async def get_users():
    # Obtener el tenant actual
    tenant_id = get_current_tenant_id()
    
    return {
        "tenant_id": tenant_id,
        "message": "Datos del tenant obtenidos exitosamente",
        "note": "La validación del tenant se realizó automáticamente"
    }

# Endpoint con acceso restringido a ciertos tenants
@app.get("/premium-feature")
@requires_tenant(["company1", "enterprise"])  # Solo tenants específicos pueden acceder
async def premium_feature():
    tenant_id = get_current_tenant_id()
    
    return {
        "tenant_id": tenant_id,
        "feature": "premium_feature",
        "access_granted": True
    }

# Endpoint para salud del sistema multitenant
@app.get("/health/tenant")
async def tenant_health():
    return {
        "status": "healthy",
        "message": "Sistema multitenant operativo",
        "validation": "enabled"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)