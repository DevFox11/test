from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Importar nuestra librería CON decoradores corregidos
from multitenancy import TenantMiddleware, MultiTenantSession, tenant_required, specific_tenants
from multitenancy.core import tenant_context

app = FastAPI(
    title="API Test Multitenant",
    description="API con endpoints públicos y protegidos por tenant",
    version="1.0.0"
)

# Configurar middleware
app.add_middleware(
    TenantMiddleware, 
    header_name="X-Tenant-ID",
    exclude_paths=[
        "/", 
        "/health", 
        "/tenants", 
        "/docs", 
        "/openapi.json",
        "/favicon.ico",
        "/redoc"
    ]
)

# Configurar SQLite para desarrollo
mt_session = MultiTenantSession({
    "db_driver": "sqlite",
    "echo_sql": True
})

# Modelos
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Integer)

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
        "acme-corp": {
            "plan": "premium",
            "features": ["advanced_analytics", "api-access"],
            "max_users": 1000
        },
        "startup-tech": {
            "plan": "basic", 
            "features": ["api-access"],
            "max_users": 100
        },
        "enterprise-ltd": {
            "plan": "enterprise",
            "features": ["advanced_analytics", "custom_reports", "priority-support"],
            "max_users": 10000
        }
    }
    
    manager = tenant_context.tenant_manager
    
    for tenant_id, config in tenants_config.items():
        manager.configure_tenant(tenant_id, config)
    
    print("✅ Tenants configurados:", list(tenants_config.keys()))
    
    # Crear tablas iniciales
    for tenant_id in tenants_config.keys():
        try:
            tenant_context.set_tenant(tenant_id)
            engine = mt_session.get_engine(tenant_id)
            Base.metadata.create_all(bind=engine)
            print(f"✅ Tablas creadas para: {tenant_id}")
        except Exception as e:
            print(f"⚠️  Error con {tenant_id}: {e}")
        finally:
            tenant_context.set_tenant(None)

# ============================================================================
# 🔓 ENDPOINTS PÚBLICOS
# ============================================================================

@app.get("/")
async def root():
    return {
        "message": "¡Bienvenido a la API Multitenant!",
        "instrucciones": "Usa el header X-Tenant-ID para acceder a endpoints protegidos",
        "tenants_disponibles": ["acme-corp", "startup-tech", "enterprise-ltd"]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "multitenant-api"}

@app.get("/tenants")
async def list_tenants():
    manager = tenant_context.tenant_manager
    tenants_info = []
    
    for tenant_id in manager.tenant_configs.keys():
        config = manager.get_tenant_config(tenant_id)
        tenants_info.append({
            "id": tenant_id,
            "plan": config.get("plan", "basic"),
            "features": config.get("features", [])
        })
    
    return {
        "available_tenants": tenants_info,
        "total": len(tenants_info)
    }

# ============================================================================
# 🔐 ENDPOINTS PROTEGIDOS - CON DECORADORES
# ============================================================================

@app.get("/users")
@tenant_required  # ✅ Decorador funcionando
async def get_users(db: Session = Depends(get_db)):
    """Obtener usuarios del tenant actual"""
    try:
        users = db.query(User).all()
        return {
            "tenant": tenant_context.get_tenant(),
            "total_users": len(users),
            "users": [{"id": u.id, "name": u.name, "email": u.email} for u in users]
        }
    except Exception as e:
        # Crear tablas si no existen
        engine = mt_session.get_engine(tenant_context.get_tenant())
        Base.metadata.create_all(bind=engine)
        return {
            "tenant": tenant_context.get_tenant(),
            "total_users": 0,
            "users": [],
            "message": "Tablas creadas, no hay usuarios aún"
        }

@app.post("/users")
@tenant_required  # ✅ Decorador funcionando
async def create_user(name: str, email: str, db: Session = Depends(get_db)):
    """Crear usuario para el tenant actual"""
    # Verificar si el usuario ya existe
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    user = User(name=name, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Usuario creado exitosamente",
        "user": {"id": user.id, "name": user.name, "email": user.email}
    }

@app.get("/products")
@tenant_required  # ✅ Decorador funcionando
async def get_products(db: Session = Depends(get_db)):
    """Obtener productos del tenant actual"""
    try:
        products = db.query(Product).all()
        return {
            "tenant": tenant_context.get_tenant(),
            "total_products": len(products),
            "products": [{"id": p.id, "name": p.name, "price": p.price} for p in products]
        }
    except Exception as e:
        engine = mt_session.get_engine(tenant_context.get_tenant())
        Base.metadata.create_all(bind=engine)
        return {
            "tenant": tenant_context.get_tenant(),
            "total_products": 0,
            "products": [],
            "message": "Tablas creadas, no hay productos aún"
        }

@app.post("/products")
@tenant_required  # ✅ Decorador funcionando
async def create_product(name: str, price: float, db: Session = Depends(get_db)):
    """Crear producto para el tenant actual"""
    product = Product(name=name, price=int(price * 100))  # Precio en centavos
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return {
        "message": "Producto creado exitosamente",
        "product": {"id": product.id, "name": product.name, "price": price}
    }

@app.get("/tenant/info")
@tenant_required  # ✅ Decorador funcionando
async def get_tenant_info():
    """Obtener información del tenant actual"""
    tenant_id = tenant_context.get_tenant()
    manager = tenant_context.tenant_manager
    config = manager.get_tenant_config(tenant_id)
    
    return {
        "tenant_id": tenant_id,
        "plan": config.get("plan", "basic"),
        "features": config.get("features", []),
        "limits": {"max_users": config.get("max_users", 100)}
    }

# ============================================================================
# 🚀 ENDPOINTS EXCLUSIVOS - CON DECORADORES ANIDADOS
# ============================================================================

@app.get("/analytics")
@tenant_required
@specific_tenants(["acme-corp", "enterprise-ltd"])  # ✅ Decorador funcionando
async def get_analytics(db: Session = Depends(get_db)):
    """Analíticas avanzadas - solo para tenants premium"""
    total_users = db.query(User).count()
    total_products = db.query(Product).count()
    
    return {
        "tenant": tenant_context.get_tenant(),
        "analytics": {
            "total_users": total_users,
            "total_products": total_products,
            "user_engagement": "high" if total_users > 50 else "low",
            "message": "Datos analíticos avanzados - función premium"
        }
    }

@app.get("/premium-features")
@tenant_required
@specific_tenants(["acme-corp", "enterprise-ltd"])
async def get_premium_features():
    """Características premium - solo para tenants específicos"""
    tenant_id = tenant_context.get_tenant()
    manager = tenant_context.tenant_manager
    config = manager.get_tenant_config(tenant_id)
    
    return {
        "tenant": tenant_id,
        "premium_features": config.get("features", []),
        "message": "Acceso a características premium concedido"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)