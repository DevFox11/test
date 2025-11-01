"""
Sistema de configuración automática para FastAPI
"""
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request
from .core import tenant_context, MultiTenantManager, TenancyStrategy
from .database import MultiTenantSession
from .middleware import TenantMiddleware
from .auto_tenant_loader import AutoTenantLoader

def create_hidra_app(
    app: FastAPI = None,
    db_config: Dict[str, Any] = None,
    strategy: TenancyStrategy = None,
    auto_tenant_validation: bool = True,
    default_tenant_config: Dict[str, Any] = None,
    enable_auto_loading: bool = True,
    auto_loader_config: Dict[str, Any] = None,
    middleware_config: Dict[str, Any] = None
) -> FastAPI:
    """
    Crea o configura una aplicación FastAPI con soporte multitenant
    
    Args:
        app: Instancia de FastAPI (si es None, se crea una nueva)
        db_config: Configuración de base de datos
        strategy: Estrategia de tenencia (por defecto SCHEMA_PER_TENANT)
        auto_tenant_validation: Validar automáticamente la existencia de tenants
        default_tenant_config: Configuración predeterminada para nuevos tenants
        enable_auto_loading: Habilitar carga automática de tenants
        auto_loader_config: Configuración para el loader automático
        middleware_config: Configuración para el middleware
    
    Returns:
        FastAPI app configurada con soporte multitenant
    """
    if app is None:
        app = FastAPI()
    
    # Configuración por defecto
    if strategy is None:
        strategy = TenancyStrategy.SCHEMA_PER_TENANT
    
    if default_tenant_config is None:
        default_tenant_config = {}
    
    if auto_loader_config is None:
        auto_loader_config = {
            "source_type": "config",
            "source_config": {"tenants": {}}
        }
    
    if middleware_config is None:
        middleware_config = {
            "header_name": os.getenv("TENANT_HEADER_NAME", "X-Tenant-ID"),
            "exclude_paths": [
                "/", "/health", "/docs", "/openapi.json", 
                "/redoc", "/favicon.ico"
            ]
        }
    
    # Configurar el manager
    manager = MultiTenantManager()
    manager.set_default_strategy(strategy)
    
    # Si se habilita la carga automática, configurar el loader
    if enable_auto_loading:
        loader = AutoTenantLoader(
            source_type=auto_loader_config.get("source_type", "config"),
            source_config=auto_loader_config.get("source_config", {})
        )
        manager.tenant_loader = loader.load_tenant
        manager.get_all_tenants_loader = loader.get_all_tenants
    
    # Establecer el manager en el contexto
    tenant_context.tenant_manager = manager
    
    # Agregar middleware con configuración
    app.add_middleware(
        TenantMiddleware,
        header_name=middleware_config.get("header_name", "X-Tenant-ID"),
        exclude_paths=middleware_config.get("exclude_paths", [
            "/", "/health", "/docs", "/openapi.json", 
            "/redoc", "/favicon.ico"
        ]),
        validate_existence=auto_tenant_validation
    )
    
    # Almacenar componentes en la app para acceso posterior
    app.state.hidra_config = {
        "manager": manager,
        "strategy": strategy,
        "db_config": db_config,
        "session_manager": MultiTenantSession(db_config, strategy) if db_config else None,
        "auto_loader": loader if enable_auto_loading else None
    }
    
    return app

def get_hidra_config(app: FastAPI):
    """
    Obtiene la configuración de hidra de la aplicación FastAPI
    """
    return getattr(app.state, 'hidra_config', None)

def get_current_tenant_db(request: Request):
    """
    Obtiene la sesión de base de datos para el tenant actual
    """
    app = request.app
    config = get_hidra_config(app)
    if config and config.get("session_manager"):
        return config["session_manager"].get_session()
    else:
        raise RuntimeError("Hidra not properly configured in this application")

async def default_tenant_registration(session, tenant_data: dict):
    """
    Función por defecto para registrar un tenant en la tabla pública.
    Esta función puede ser reemplazada por el desarrollador con su propia lógica.
    """
    from sqlalchemy import text
    
    # Esta es una implementación básica, el desarrollador debería proporcionar
    # su propia lógica acorde a la estructura de su tabla tenants
    query = text("""
        INSERT INTO public.tenants (id, name, status) 
        VALUES (:id, :name, :status)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            updated_at = CURRENT_TIMESTAMP,
            status = EXCLUDED.status
    """)
    session.execute(query, {
        "id": tenant_data["id"],
        "name": tenant_data["name"],
        "status": tenant_data.get("status", "active")
    })
    session.commit()


def initialize_hidra_fastapi(
    app: FastAPI,
    db_config: Dict[str, Any] = None,
    strategy: TenancyStrategy = None,
    include_default_endpoints: bool = True,
    include_tenant_registration: bool = True,
    tenant_registration_func=None,
    **kwargs
):
    """
    Inicializa hidra en una aplicación FastAPI con mínima configuración
    
    Args:
        app: Instancia de FastAPI
        db_config: Configuración de base de datos
        strategy: Estrategia de tenencia
        include_default_endpoints: Incluir endpoints de salud
        include_tenant_registration: Incluir endpoint de registro de tenant
        tenant_registration_func: Función personalizada para registrar tenants
        **kwargs: Otros parámetros de configuración
    """
    from .schema_manager import SchemaManager
    
    # Configurar automáticamente la app
    app = create_hidra_app(
        app=app,
        db_config=db_config,
        strategy=strategy,
        **kwargs
    )
    
    # Agregar schema manager al estado de la app
    schema_manager = SchemaManager(db_config)
    app.state.schema_manager = schema_manager
    
    # Configurar el entorno multitenant
    schema_manager.setup_multi_tenant_environment()
    
    if include_default_endpoints:
        @app.get("/health/tenant")
        async def tenant_health():
            """Endpoint para verificar estado del sistema multitenant"""
            config = get_hidra_config(app)
            return {
                "status": "healthy",
                "strategy": config["strategy"].value if config else "not_configured",
                "tenant_validation": "enabled" if config else "disabled"
            }
    
    if include_tenant_registration:
        @app.post("/register-tenant")
        async def register_tenant(tenant_info: dict):
            """Endpoint para registrar un nuevo tenant"""
            from .database import MultiTenantSession
            from .db_simple import HidraDB
            
            tenant_id = tenant_info.get("id")
            if not tenant_id:
                raise ValueError("Tenant ID is required")
            
            tenant_name = tenant_info.get("name", tenant_id)
            
            # Usar schema manager para crear el schema del tenant
            schema_manager.initialize_tenant(
                tenant_id=tenant_id,
                tenant_name=tenant_name,
                register_tenant=True  # Registrará en la tabla por defecto
            )
            
            # Opcionalmente crear tablas en el schema del tenant
            create_tables_func = tenant_info.get("create_tables_func")
            if create_tables_func:
                schema_manager.create_tables_in_tenant_schema(
                    tenant_id=tenant_id,
                    create_tables_func=create_tables_func
                )
            
            return {
                "message": f"Tenant {tenant_id} registered successfully",
                "tenant_id": tenant_id,
                "tenant_name": tenant_name
            }
    
    return app