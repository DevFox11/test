from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import Column, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Importar nuestra librería completa
from hidra import TenantMiddleware, MultiTenantSession, tenant_required, specific_tenants, TenancyStrategy, TenantAwareModel, run_migrations_for_all_tenants
from hidra.core import tenant_context
from hidra.exceptions import MultitenancyError, TenantNotFoundError, TenantContextError

app = FastAPI(
    title="API Test Multitenant - Pruebas Completas de Hidra",
    description="API para probar todas las funcionalidades de la biblioteca Hidra",
    version="1.0.0"
)

# Middlewares
app.add_middleware(
    TenantMiddleware, 
    header_name="X-Tenant-ID",
    exclude_paths=["/", "/health", "/tenants", "/docs", "/openapi.json", "/favicon.ico", "/redoc", "/debug", "/schemas", "/strategies", "/temp-tenant"]
)

# ✅ CONFIGURACIÓN POSTGRESQL CON STRATEGY CONFIGURABLE
CURRENT_STRATEGY = TenancyStrategy.SCHEMA_PER_TENANT

# Extender la clase MultiTenantSession para incluir get_engine
class ExtendedMultiTenantSession(MultiTenantSession):
    def get_engine(self, tenant_id: str):
        """Obtiene el motor de base de datos para un tenant específico"""
        if self.strategy == TenancyStrategy.DATABASE_PER_TENANT:
            if tenant_id not in self.engines:
                db_url = self._build_database_connection_string(tenant_id)
                engine = create_engine(
                    db_url, pool_pre_ping=True, echo=self.base_config.get("echo_sql", False)
                )
                self.engines[tenant_id] = engine
            return self.engines[tenant_id]
        elif self.strategy == TenancyStrategy.SCHEMA_PER_TENANT:
            if tenant_id not in self.engines:
                db_url = self._build_schema_connection_string(tenant_id)
                engine = create_engine(
                    db_url, pool_pre_ping=True, echo=self.base_config.get("echo_sql", False)
                )
                self.engines[tenant_id] = engine
            return self.engines[tenant_id]
        elif self.strategy == TenancyStrategy.ROW_LEVEL:
            if tenant_id not in self.engines:
                db_url = self._build_row_level_connection_string()
                engine = create_engine(
                    db_url, pool_pre_ping=True, echo=self.base_config.get("echo_sql", False)
                )
                self.engines[tenant_id] = engine
            return self.engines[tenant_id]
        else:
            raise ValueError(f"Estrategia no soportada: {self.strategy}")

# Configurar PostgreSQL con la clase extendida
mt_session = ExtendedMultiTenantSession({
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

# Modelo que usa TenantAwareModel para aislamiento a nivel de fila
class TenantAwareOrder(TenantAwareModel, Base):
    __tablename__ = "tenant_aware_orders"
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String)
    quantity = Column(Integer)
    # Hereda tenant_id de TenantAwareModel

# Modelos Pydantic
class UserCreate(BaseModel):
    name: str
    email: str

class ProductCreate(BaseModel):
    name: str
    price: float

class TenantConfig(BaseModel):
    db_connection: str
    plan: str = "basic"
    features: list = []

class TenantAwareOrderCreate(BaseModel):
    product_name: str
    quantity: int

def get_db():
    db = mt_session.get_session()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup():
    """Configurar tenants y crear schemas en PostgreSQL"""
    
    # Configuramos tenants para diferentes estrategias
    tenants_config = {
        "acme_corp": {"plan": "premium", "features": ["advanced_analytics"], "db_connection": "postgresql://user:pass@host/db1"},
        "startup_tech": {"plan": "basic", "features": [], "db_connection": "postgresql://user:pass@host/db2"},
        "enterprise_ltd": {"plan": "enterprise", "features": ["advanced_analytics", "custom_reports"], "db_connection": "postgresql://user:pass@host/db3"}
    }
    
    manager = tenant_context.tenant_manager
    manager.set_default_strategy(CURRENT_STRATEGY)
    
    for tenant_id, config in tenants_config.items():
        manager.configure_tenant(tenant_id, config)
    
    print(f"✅ Tenants configurados: {list(tenants_config.keys())}")
    print(f"🎯 Estrategia activa: {CURRENT_STRATEGY.value}")
    print(f"🗄️  Base de datos: multitenant_db")
    
    # Inicializar schemas para esquema-per-tenant
    if CURRENT_STRATEGY == TenancyStrategy.SCHEMA_PER_TENANT:
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
# 🔐 ENDPOINTS PROTEGIDOS CON DECORADORES
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

# ============================================================================
# 🛡️ ENDPOINTS CON DECORADOR ESPECÍFICO DE TENANT
# ============================================================================

@app.get("/premium-feature")
@specific_tenants(["acme_corp", "enterprise_ltd"])
async def premium_feature(db: Session = Depends(get_db)):
    """Feature solo disponible para tenants premium"""
    return {
        "message": "Feature premium accesible",
        "tenant": tenant_context.get_tenant(),
        "feature": "advanced_analytics",
        "status": "success"
    }

@app.get("/admin-access")
@specific_tenants(["enterprise_ltd"])
async def admin_access(db: Session = Depends(get_db)):
    """Feature solo disponible para tenant enterprise"""
    return {
        "message": "Acceso administrativo concedido",
        "tenant": tenant_context.get_tenant(),
        "feature": "custom_reports",
        "status": "admin_access_granted"
    }

# ============================================================================
# 🔄 ENDPOINTS DE MANEJO DE ESTRATEGIAS DE TENENCIA
# ============================================================================

@app.get("/strategies")
async def list_strategies():
    """Listar todas las estrategias de tenencia disponibles"""
    strategies = {
        "DATABASE_PER_TENANT": "Cada tenant tiene una base de datos separada",
        "SCHEMA_PER_TENANT": "Cada tenant tiene un esquema separado dentro de la misma base de datos", 
        "ROW_LEVEL": "Todos los tenants comparten la misma base de datos y tablas, con aislamiento mediante una columna identificadora"
    }
    return {
        "estrategias_disponibles": list(TenancyStrategy.__members__.keys()),
        "descripciones": strategies,
        "estrategia_actual": CURRENT_STRATEGY.value
    }

# ============================================================================
# 🧪 ENDPOINTS DE PRUEBA AVANZADOS
# ============================================================================

@app.get("/tenant-context")
@tenant_required
async def get_tenant_context_info():
    """Información completa del contexto de tenant"""
    return {
        "tenant_actual": tenant_context.get_tenant(),
        "tenant_manager_config_count": len(tenant_context.tenant_manager.tenant_configs),
        "default_strategy": tenant_context.tenant_manager.default_strategy.value,
        "context_var_info": "ContextVar usado para mantener el tenant actual de forma segura entre hilos/corutinas"
    }

@app.get("/temp-tenant")
async def test_temp_tenant_context():
    """Probar contexto temporal de tenant"""
    original_tenant = tenant_context.get_tenant()
    result = {"original_tenant": original_tenant, "tested_tenants": []}
    
    # Probar con contexto temporal
    test_tenants = ["acme_corp", "startup_tech"]
    for test_tenant in test_tenants:
        with tenant_context.as_tenant(test_tenant):
            current = tenant_context.get_tenant()
            result["tested_tenants"].append({
                "attempted": test_tenant,
                "set_result": current,
                "is_correct": current == test_tenant
            })
    
    # Verificar que el tenant original se restauró
    final_tenant = tenant_context.get_tenant()
    result["final_tenant"] = final_tenant
    result["context_restored"] = final_tenant == original_tenant
    
    return result

@app.get("/async-temp-tenant")
async def test_async_temp_tenant_context():
    """Probar contexto temporal de tenant asincrónico"""
    original_tenant = tenant_context.get_tenant()
    result = {"original_tenant": original_tenant, "tested_tenants": []}
    
    # Probar con contexto temporal asincrónico
    test_tenants = ["enterprise_ltd"]
    for test_tenant in test_tenants:
        async with tenant_context.async_as_tenant(test_tenant):
            current = await tenant_context.require_tenant()
            result["tested_tenants"].append({
                "attempted": test_tenant,
                "set_result": current,
                "is_correct": current == test_tenant
            })
    
    # Verificar que el tenant original se restauró
    final_tenant = tenant_context.get_tenant()
    result["final_tenant"] = final_tenant
    result["context_restored"] = final_tenant == original_tenant
    
    return result

# ============================================================================
# 🏗️ ENDPOINTS DE MANEJO DE ERRORES
# ============================================================================

@app.get("/test-errors")
async def test_error_handling(tenant_id: str = Query(None, description="ID del tenant a probar")):
    """Probar diferentes tipos de errores de la biblioteca"""
    errors_tested = []
    
    # Probar TenantNotFoundError
    try:
        if tenant_id:
            exists = await tenant_context.tenant_manager.tenant_exists(tenant_id)
            errors_tested.append({
                "type": "tenant_exists_check",
                "tenant_id": tenant_id,
                "exists": exists
            })
        else:
            errors_tested.append({
                "type": "tenant_exists_check",
                "message": "No tenant_id provided for existence check"
            })
    except TenantNotFoundError as e:
        errors_tested.append({
            "type": "TenantNotFoundError",
            "error": str(e),
            "tested_tenant": tenant_id
        })
    except Exception as e:
        errors_tested.append({
            "type": "OtherError",
            "error": str(e),
            "tested_tenant": tenant_id
        })
    
    # Probar TenantContextError
    try:
        # Forzar error de contexto sin tenant
        current_tenant = tenant_context.get_tenant()
        if not current_tenant:
            errors_tested.append({
                "type": "no_tenant_context",
                "message": "No hay tenant actual en el contexto"
            })
        else:
            errors_tested.append({
                "type": "current_tenant_found",
                "tenant": current_tenant
            })
    except TenantContextError as e:
        errors_tested.append({
            "type": "TenantContextError",
            "error": str(e)
        })
    
    return {
        "errors_tested": errors_tested,
        "total_tests": len(errors_tested)
    }

# ============================================================================
# 🗃️ ENDPOINTS DE MIGRACIONES
# ============================================================================

@app.post("/run-all-migrations")
async def run_all_migrations():
    """Ejecutar migraciones para todos los tenants"""
    def create_session_for_migration():
        # Crear una sesión para la migración
        return mt_session.get_session()
    
    def dummy_migration_logic(session, tenant_id):
        # Lógica de migración de ejemplo - en un caso real, aquí irían las operaciones de migración
        print(f"Ejecutando migración para tenant: {tenant_id}")
        # Por ejemplo, crear tablas, modificar estructuras, etc.
        return None  # Síncrono
    
    try:
        # Ejecutar migraciones para todos los tenants
        run_migrations_for_all_tenants(create_session_for_migration, dummy_migration_logic)
        return {
            "message": "Migraciones para todos los tenants iniciadas",
            "status": "success"
        }
    except Exception as e:
        return {
            "message": "Error ejecutando migraciones",
            "error": str(e),
            "status": "error"
        }

# ============================================================================
# 🔧 ENDPOINTS DE CONFIGURACIÓN DINÁMICA
# ============================================================================

@app.post("/configure-tenant")
async def configure_new_tenant(tenant_data: TenantConfig, tenant_id: str = Query(..., description="ID del nuevo tenant")):
    """Configurar un nuevo tenant dinámicamente"""
    try:
        tenant_context.tenant_manager.configure_tenant(tenant_id, tenant_data.dict())
        return {
            "message": f"Tenant {tenant_id} configurado exitosamente",
            "tenant_id": tenant_id,
            "config": tenant_data.dict()
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Error configurando nuevo tenant"
        }

@app.get("/all-tenants-info")
async def get_all_tenants_info():
    """Obtener información de todos los tenants disponibles"""
    try:
        all_tenants = await tenant_context.tenant_manager.get_all_tenant_ids()
        tenants_info = []
        for tenant_id in all_tenants:
            config = await tenant_context.tenant_manager.get_tenant_config(tenant_id)
            tenants_info.append({
                "id": tenant_id,
                "config": config
            })
        return {
            "tenants_count": len(tenants_info),
            "tenants": tenants_info
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Error obteniendo información de tenants"
        }

# ============================================================================
# 🏷️ ENDPOINTS PARA PRUEBA DE TenantAwareModel (ROW LEVEL STRATEGY)
# ============================================================================

@app.get("/tenant-aware-orders")
@tenant_required
async def get_tenant_aware_orders(db: Session = Depends(get_db)):
    """Obtener órdenes usando TenantAwareModel (prueba para Row Level Strategy)"""
    try:
        orders = db.query(TenantAwareOrder).all()
        return {
            "estrategia": CURRENT_STRATEGY.value,
            "base_datos": "PostgreSQL", 
            "tenant": tenant_context.get_tenant(),
            "total_orders": len(orders),
            "orders": [{
                "id": o.id, 
                "product_name": o.product_name, 
                "quantity": o.quantity,
                "tenant_id": o.tenant_id
            } for o in orders]
        }
    except Exception as e:
        return {
            "error": str(e),
            "tenant": tenant_context.get_tenant(),
            "message": "Error al obtener órdenes con TenantAwareModel"
        }

@app.post("/tenant-aware-orders")
@tenant_required
async def create_tenant_aware_order(order_data: TenantAwareOrderCreate, db: Session = Depends(get_db)):
    """Crear orden usando TenantAwareModel (prueba para Row Level Strategy)"""
    order = TenantAwareOrder(
        product_name=order_data.product_name,
        quantity=order_data.quantity
    )
    # En la estrategia ROW_LEVEL, el tenant_id debería ser establecido automáticamente
    # o establecido explícitamente en el contexto
    order.tenant_id = tenant_context.get_tenant()
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return {
        "message": "Orden creada con TenantAwareModel",
        "estrategia": CURRENT_STRATEGY.value,
        "order": {
            "id": order.id,
            "product_name": order.product_name,
            "quantity": order.quantity,
            "tenant_id": order.tenant_id
        }
    }

@app.get("/test-row-level-strategy")
async def test_row_level_strategy_info():
    """Información sobre cómo usar la estrategia de aislamiento a nivel de fila"""
    return {
        "descripcion": "La estrategia ROW_LEVEL permite a todos los tenants compartir la misma base de datos y tablas",
        "caracteristicas": [
            "Todos los tenants comparten las mismas tablas",
            "El aislamiento se logra mediante una columna tenant_id",
            "El modelo TenantAwareModel incluye automáticamente el campo tenant_id",
            "Para usarlo efectivamente, se recomienda implementar políticas de fila (Row Level Security) en la base de datos"
        ],
        "modelo_usado": "TenantAwareOrder",
        "estrategia_actual": CURRENT_STRATEGY.value,
        "recomendacion": "Cambiar CURRENT_STRATEGY a TenancyStrategy.ROW_LEVEL para pruebas completas" if CURRENT_STRATEGY != TenancyStrategy.ROW_LEVEL else "Actualmente configurado para ROW_LEVEL"
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