"""
Ejemplo de integración completa con FastAPI
"""
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from hidra import setup_fastapi_app, requires_tenant, get_current_tenant_id

# Crear aplicación FastAPI
app = FastAPI()

# Configurar Hidra con FastAPI
hidra = setup_fastapi_app(
    app,
    db_config={
        "db_driver": "sqlite",
        "db_name": "fastapi_example.db" 
    },
    tenants={
        "company1": {"plan": "premium", "features": ["advanced"]},
        "company2": {"plan": "basic", "features": []}
    }
)

# Endpoint protegido con el nuevo decorador
@app.get("/users")
@requires_tenant()  # Requiere tenant
async def get_users(db: Session = Depends(hidra["session_getter"])):
    # Obtener el tenant actual
    tenant_id = get_current_tenant_id()
    
    return {
        "tenant_id": tenant_id,
        "message": "Datos del tenant obtenidos exitosamente",
        "db_session_available": db is not None
    }

# Endpoint con acceso restringido a ciertos tenants
@app.get("/premium-feature")
@requires_tenant(["company1"])  # Solo company1 puede acceder
async def premium_feature(db: Session = Depends(hidra["session_getter"])):
    tenant_id = get_current_tenant_id()
    
    return {
        "tenant_id": tenant_id,
        "feature": "premium_feature",
        "access_granted": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)