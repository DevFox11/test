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

def initialize_hidra_fastapi(
    app: FastAPI,
    db_config: Dict[str, Any] = None,
    strategy: TenancyStrategy = None,
    **kwargs
):
    """
    Inicializa hidra en una aplicación FastAPI con mínima configuración
    
    Args:
        app: Instancia de FastAPI
        db_config: Configuración de base de datos
        strategy: Estrategia de tenencia
        **kwargs: Otros parámetros de configuración
    """
    # Configurar automáticamente la app
    create_hidra_app(
        app=app,
        db_config=db_config,
        strategy=strategy,
        **kwargs
    )
    
    # Agregar endpoints estándar si se desea
    @app.get("/health/tenant")
    async def tenant_health():
        """Endpoint para verificar estado del sistema multitenant"""
        config = get_hidra_config(app)
        return {
            "status": "healthy",
            "strategy": config["strategy"].value if config else "not_configured",
            "tenant_validation": "enabled" if config else "disabled"
        }
    
    return app