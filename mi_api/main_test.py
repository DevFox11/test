from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

# Importar nuestra librería
from hidra import TenantMiddleware, MultiTenantSession
from hidra.core import tenant_context

app = FastAPI(
    title="API Test Multitenant - DEBUG",
    description="Versión de debug para probar el middleware",
    version="1.0.0"
)

# Configurar middleware con logging
app.add_middleware(
    TenantMiddleware,
    exclude_paths=[
        "/",
        "/health",
        "/tenants",
        "/docs",
        "/openapi.json",
        "/favicon.ico",
        "/redoc",
        "/debug",
    ],
)

# Configurar SQLite para desarrollo
mt_session = MultiTenantSession({
    "db_driver": "sqlite",
    "echo_sql": False
})

# Modelos
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)

def get_db():
    db = mt_session.get_session()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup():
    """Configurar tenants disponibles al iniciar la aplicación"""
    
    tenants_config = {
        "acme-corp": {"plan": "premium"},
        "startup-tech": {"plan": "basic"}, 
        "enterprise-ltd": {"plan": "enterprise"}
    }
    
    manager = tenant_context.tenant_manager
    
    for tenant_id, config in tenants_config.items():
        manager.configure_tenant(tenant_id, config)
    
    print("✅ Tenants configurados:", list(tenants_config.keys()))

# ============================================================================
# 🔓 ENDPOINTS PÚBLICOS
# ============================================================================

@app.get("/")
async def root():
    return {"message": "¡API Multitenant funcionando!", "status": "debug"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/tenants")
async def list_tenants():
    manager = tenant_context.tenant_manager
    return {
        "tenants": list(manager.tenant_configs.keys()),
        "total": len(manager.tenant_configs)
    }

@app.get("/debug")
async def debug_info(request: Request):
    """Endpoint de debug para ver headers y contexto"""
    headers = dict(request.headers)
    tenant_id = tenant_context.get_tenant()
    
    return {
        "headers": headers,
        "current_tenant": tenant_id,
        "available_tenants": list(tenant_context.tenant_manager.tenant_configs.keys()),
        "message": "Debug information"
    }

# ============================================================================
# 🔐 ENDPOINTS PROTEGIDOS - SIN DECORADORES (verificación manual)
# ============================================================================

@app.get("/users")
async def get_users(db: Session = Depends(get_db)):
    """Obtener usuarios - con verificación manual de tenant"""
    tenant_id = tenant_context.get_tenant()
    
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Tenant identification required",
                "message": "This endpoint requires the X-Tenant-ID header",
                "solution": "Add X-Tenant-ID: your-tenant-id to your request headers",
                "example": "curl -H 'X-Tenant-ID: acme-corp' http://localhost:8000/users"
            }
        )
    
    try:
        users = db.query(User).all()
        return {
            "tenant": tenant_id,
            "total_users": len(users),
            "users": [{"id": u.id, "name": u.name, "email": u.email} for u in users]
        }
    except Exception as e:
        # Crear tablas si no existen
        engine = db.get_bind()
        Base.metadata.create_all(bind=engine)
        return {
            "tenant": tenant_id,
            "total_users": 0,
            "users": [],
            "message": "Tablas creadas, no hay usuarios aún"
        }

@app.post("/users")
async def create_user(name: str, email: str, db: Session = Depends(get_db)):
    """Crear usuario - con verificación manual de tenant"""
    tenant_id = tenant_context.get_tenant()
    
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Tenant identification required",
                "message": "This endpoint requires the X-Tenant-ID header",
                "solution": "Add X-Tenant-ID: your-tenant-id to your request headers"
            }
        )
    
    user = User(name=name, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Usuario creado exitosamente",
        "user": {"id": user.id, "name": user.name, "email": user.email}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)