"""
Integraciones con frameworks populares
"""
from typing import Dict, Any
from .quick_start import quick_start
from .middleware import TenantMiddleware
from .db_simple import HidraDB

def setup_fastapi_app(
    app,
    db_config: Dict[str, Any],
    tenants: Dict[str, Dict] = None,
    strategy=None
):
    """
    Configura una aplicación FastAPI completa con multitenancy
    
    Args:
        app: Instancia de FastAPI
        db_config: Configuración de base de datos
        tenants: Diccionario de tenants a configurar
        strategy: Estrategia de tenencia (opcional)
    
    Returns:
        Dict con componentes configurados
    """
    from .core import TenancyStrategy
    if strategy is None:
        strategy = TenancyStrategy.SCHEMA_PER_TENANT
    
    # Configuración rápida
    setup_result = quick_start(
        db_config=db_config,
        strategy=strategy,
        tenants=tenants
    )
    
    # Agrega middleware
    app.add_middleware(TenantMiddleware)
    
    # Devuelve componentes listos para usar
    hidra_db = HidraDB(db_config, strategy)
    
    return {
        "app": app,
        "db": hidra_db,
        "session_getter": hidra_db.get_tenant_db(),
        "manager": setup_result["manager"],
        "setup_result": setup_result
    }