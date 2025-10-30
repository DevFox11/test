from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import Column, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Importar nuestra librería actualizada
from multitenancy import TenantMiddleware, MultiTenantSession, tenant_required, specific_tenants, TenancyStrategy
from multitenancy.core import tenant_context
from multitenancy.error_handler import ErrorHandlerMiddleware

app = FastAPI(
    title="API Test Multitenant - PostgreSQL",
    description="API con PostgreSQL y Schema per Tenant",
    version="1.0.0"
)

# Middlewares
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(
    TenantMiddleware, 
    header_name="X-Tenant-ID",
    exclude_paths=["/", "/health", "/tenants", "/docs", "/openapi.json", "/favicon.ico", "/redoc", "/debug", "/schemas"]
)

# ✅ CONFIGURACIÓN POSTGRESQL CON SCHEMA PER TENANT
CURRENT_STRATEGY = TenancyStrategy.SCHEMA_PER_TENANT

# Configurar PostgreSQL
mt_session = MultiTenantSession({
    "db_driver": "postgresql",
    "db_host": "localhost",
    "db_port": "5432",
    "db_username": "postgres",
    "db_password": "makinelabdb",
    "db_name": "multitenant",
    "echo_sql": True  # ✅ Ver todas las queries
}, strategy=CURRENT_STRATEGY)

# Modelos Base
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

# Modelos Pydantic
class UserCreate(BaseModel):
    name: str
    email: str

class ProductCreate(BaseModel):
    name: str
    price: float

def get_db():
    db = mt_session.get_session()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup():
    """Configurar tenants y crear schemas en PostgreSQL"""
    
    tenants_config = {
        "acme_corp": {"plan": "premium", "features": ["advanced_analytics"]},
        "startup_tech": {"plan": "basic", "features": []},
        "enterprise_ltd": {"plan": "enterprise", "features": ["advanced_analytics", "custom_reports"]}
    }
    
    manager = tenant_context.tenant_manager
    
    for tenant_id, config in tenants_config.items():
        manager.configure_tenant(tenant_id, config)
    
    print(f"✅ Tenants configurados: {list(tenants_config.keys())}")
    print(f"🎯 Estrategia activa: {CURRENT_STRATEGY.value}")
    print(f"🗄️  Base de datos: multitenant_db")
    
    # ✅ CORREGIDO: Forzar la creación de sesiones y schemas
    for tenant_id in tenants_config.keys():
        try:
            print(f"🔧 Inicializando schema para: {tenant_id}")
            tenant_context.set_tenant(tenant_id)
            
            # Forzar la creación de la sesión (esto creará el schema)
            engine = mt_session.get_engine(tenant_id)
            
            # Crear schema explícitamente
            with engine.connect() as conn:
                schema_name = f"tenant_{tenant_id}"
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                conn.commit()
                print(f"   ✅ Schema creado: {schema_name}")
            
            # Forzar la creación de tablas
            Base.metadata.create_all(bind=engine)
            print(f"   ✅ Tablas creadas en schema: {schema_name}")
            
        except Exception as e:
            print(f"⚠️  Error inicializando {tenant_id}: {e}")
        finally:
            tenant_context.set_tenant(None)
    
    print("🎉 Inicialización completada")

# ============================================================================
# 🔓 ENDPOINTS PÚBLICOS
# ============================================================================

@app.get("/")
async def root():
    return {
        "message": "¡API Multitenant con PostgreSQL!",
        "estrategia_activa": CURRENT_STRATEGY.value,
        "base_datos": "PostgreSQL",
        "instrucciones": "Usa el header X-Tenant-ID para acceder a endpoints protegidos"
    }

@app.get("/schemas")
async def list_schemas(db: Session = Depends(get_db)):
    """Listar todos los schemas en la base de datos"""
    try:
        result = db.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%'"))
        schemas = [row[0] for row in result]
        
        return {
            "total_schemas": len(schemas),
            "schemas": schemas,
            "base_datos": "multitenant_db"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/schemas/{tenant_id}/tables")
async def get_schema_tables(tenant_id: str, db: Session = Depends(get_db)):
    """Listar tablas en un schema específico"""
    try:
        # Temporalmente establecer el schema
        schema_name = f"tenant_{tenant_id}"
        db.execute(text(f"SET search_path TO {schema_name}"))
        
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = :schema"), 
                           {"schema": schema_name})
        tables = [row[0] for row in result]
        
        return {
            "schema": schema_name,
            "total_tablas": len(tables),
            "tablas": tables
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "multitenant-api", 
        "estrategia": CURRENT_STRATEGY.value,
        "base_datos": "PostgreSQL"
    }

@app.get("/tenants")
async def list_tenants():
    manager = tenant_context.tenant_manager
    tenants_info = []
    
    for tenant_id in manager.tenant_configs.keys():
        config = manager.get_tenant_config(tenant_id)
        tenants_info.append({
            "id": tenant_id,
            "plan": config.get("plan", "basic"),
            "features": config.get("features", []),
            "schema": f"tenant_{tenant_id}"  # ✅ Ya usa guiones bajos
        })
    
    return {
        "estrategia": CURRENT_STRATEGY.value,
        "base_datos": "PostgreSQL",
        "available_tenants": tenants_info,
        "total": len(tenants_info),
        "nota": "Los nombres de tenant usan guiones bajos para compatibilidad con PostgreSQL"
    }
    
    
    
@app.get("/debug/database")
async def debug_database():
    """Diagnóstico detallado de la base de datos"""
    try:
        # Probar conexión básica
        engine = mt_session.get_engine("acme_corp")
        with engine.connect() as conn:
            # Verificar que podemos conectar
            result = conn.execute(text("SELECT version()"))
            db_version = result.scalar()
            
            # Verificar schemas existentes
            result = conn.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%'"))
            schemas = [row[0] for row in result]
            
            # Verificar tablas en un schema
            tables_in_schema = []
            if schemas:
                schema_name = schemas[0]
                result = conn.execute(text(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema_name}'"))
                tables_in_schema = [row[0] for row in result]
        
        return {
            "status": "connected",
            "database_version": db_version,
            "schemas_found": schemas,
            "tables_in_first_schema": tables_in_schema,
            "total_schemas": len(schemas),
            "strategy": CURRENT_STRATEGY.value
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "strategy": CURRENT_STRATEGY.value
        }

@app.get("/debug/tenant-test")
async def debug_tenant_test():
    """Probar funcionalidad de tenant con diferentes casos"""
    test_results = []
    
    test_cases = ["acme_corp", "startup_tech", "enterprise_ltd"]
    
    for tenant_id in test_cases:
        try:
            # Establecer tenant
            tenant_context.set_tenant(tenant_id)
            
            # Obtener sesión
            db = next(get_db())
            
            # Probar consulta simple
            result = db.execute(text("SELECT current_schema()"))
            current_schema = result.scalar()
            
            # Probar consulta a users
            try:
                users = db.query(User).all()
                user_count = len(users)
            except:
                user_count = "error"
            
            test_results.append({
                "tenant": tenant_id,
                "current_schema": current_schema,
                "expected_schema": f"tenant_{tenant_id}",
                "user_count": user_count,
                "status": "success" if current_schema == f"tenant_{tenant_id}" else "schema_mismatch"
            })
            
            db.close()
            
        except Exception as e:
            test_results.append({
                "tenant": tenant_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "status": "error"
            })
        finally:
            tenant_context.set_tenant(None)
    
    return {
        "test_results": test_results,
        "summary": {
            "total_tests": len(test_results),
            "successful": len([r for r in test_results if r.get("status") == "success"]),
            "errors": len([r for r in test_results if r.get("status") == "error"]),
            "schema_mismatches": len([r for r in test_results if r.get("status") == "schema_mismatch"])
        }
    }

# ============================================================================
# 🔐 ENDPOINTS PROTEGIDOS
# ============================================================================

@app.get("/users")
@tenant_required
async def get_users(db: Session = Depends(get_db)):
    """Obtener usuarios del tenant actual (desde su schema)"""
    try:
        users = db.query(User).all()
        return {
            "estrategia": CURRENT_STRATEGY.value,
            "base_datos": "PostgreSQL", 
            "tenant": tenant_context.get_tenant(),
            "schema": f"tenant_{tenant_context.get_tenant()}",
            "total_users": len(users),
            "users": [{"id": u.id, "name": u.name, "email": u.email} for u in users]
        }
    except Exception as e:
        return {
            "error": str(e),
            "tenant": tenant_context.get_tenant(),
            "message": "Error al obtener usuarios"
        }
        
@app.get("/products")
@tenant_required
async def get_products(db: Session = Depends(get_db)):
    """Obtener productos del tenant actual (desde su schema)"""
    try:
        products = db.query(Product).all()
        return {
            "estrategia": CURRENT_STRATEGY.value,
            "base_datos": "PostgreSQL", 
            "tenant": tenant_context.get_tenant(),
            "schema": f"tenant_{tenant_context.get_tenant()}",
            "total_products": len(products),
            "products": [{"id": p.id, "name": p.name, "price": p.price} for p in products]
        }
    except Exception as e:
        return {
            "error": str(e),
            "tenant": tenant_context.get_tenant(),
            "message": "Error al obtener productos"
        }

@app.post("/users")
@tenant_required
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Crear usuario en el schema del tenant actual"""
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    user = User(name=user_data.name, email=user_data.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Usuario creado exitosamente en PostgreSQL",
        "estrategia": CURRENT_STRATEGY.value,
        "schema": f"tenant_{tenant_context.get_tenant()}",
        "user": {"id": user.id, "name": user.name, "email": user.email}
    }
    
@app.post("/products")
@tenant_required
async def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    """Crear producto en el schema del tenant actual"""
    existing_product = db.query(Product).filter(Product.name == product_data.name).first()
    if existing_product:
        raise HTTPException(status_code=400, detail="El producto ya existe")
    product = Product(name=product_data.name, price=product_data.price)
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return {
        "message": "Producto creado exitosamente en PostgreSQL",
        "estrategia": CURRENT_STRATEGY.value,
        "schema": f"tenant_{tenant_context.get_tenant()}",
        "product": {"id": product.id, "name": product.name, "price": product.price}
    }
    

@app.get("/debug/current-schema")
@tenant_required
async def debug_current_schema(db: Session = Depends(get_db)):
    """Debug: Ver el schema actual"""
    try:
        result = db.execute(text("SELECT current_schema()"))
        current_schema = result.scalar()
        
        return {
            "schema_actual": current_schema,
            "tenant_actual": tenant_context.get_tenant(),
            "schema_esperado": f"tenant_{tenant_context.get_tenant()}"
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)