"""
Ejemplo avanzado de uso de Hidra con FastAPI

Este ejemplo demuestra cómo usar Hidra con validación automática de tenants
"""
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

# Importar componentes para configuración avanzada
from hidra import initialize_hidra_fastapi, requires_tenant, get_hidra_config

# Crear aplicación FastAPI
app = FastAPI(title="API Multitenant con Hidra", version="1.0.0")

# Configurar Hidra con validación automática de tenants
# Los tenants se pueden cargar desde una fuente externa (base de datos, API, etc.)
initialize_hidra_fastapi(
    app,
    db_config={
        "db_driver": "sqlite",
        "db_name": "advanced_example.db"
    },
    # Configurar carga automática de tenants
    enable_auto_loading=True,
    auto_loader_config={
        "source_type": "config",
        "source_config": {
            "tenants": {
                # Ejemplo de tenants preconfigurados
                # En un escenario real, esto podría venir de una base de datos
                "company1": {"plan": "premium", "features": ["analytics", "reports"]},
                "company2": {"plan": "basic", "features": []},
                "company3": {"plan": "enterprise", "features": ["analytics", "reports", "support"]}
            }
        }
    },
    # Validar que los tenants existan antes de procesar la solicitud
    auto_tenant_validation=True
)

# Endpoint que requiere tenant (cualquier tenant válido)
@app.get("/dashboard")
@requires_tenant()  # El tenant se valida automáticamente
async def get_dashboard():
    from hidra import get_current_tenant_id, get_current_tenant_config
    
    tenant_id = get_current_tenant_id()
    tenant_config = get_current_tenant_config()
    
    return {
        "tenant_id": tenant_id,
        "tenant_config": tenant_config,
        "dashboard": "Información del dashboard del tenant",
        "features_available": tenant_config.get("features", [])
    }

# Endpoint que requiere tenant específico
@app.get("/admin-panel")
@requires_tenant(["company3"])  # Solo empresa enterprise puede acceder
async def get_admin_panel():
    from hidra import get_current_tenant_id
    
    tenant_id = get_current_tenant_id()
    
    return {
        "tenant_id": tenant_id,
        "admin_panel": "Panel de administración",
        "message": "Acceso restringido a tenants enterprise"
    }

# Endpoint para verificar estado del sistema multitenant
@app.get("/health/tenant")
async def tenant_health():
    config = get_hidra_config(app)
    
    return {
        "status": "healthy",
        "strategy": config["strategy"].value,
        "tenant_validation": "enabled",
        "message": "Sistema multitenant funcionando correctamente"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)