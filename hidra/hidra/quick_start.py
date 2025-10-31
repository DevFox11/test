"""
Módulo para configuración rápida de la biblioteca Hidra
"""
from typing import Dict, Any
from .core import tenant_context, MultiTenantManager, TenancyStrategy
from .database import MultiTenantSession

def quick_start(
    db_url: str = None,
    strategy: TenancyStrategy = TenancyStrategy.SCHEMA_PER_TENANT,
    tenants: Dict[str, Dict] = None,
    db_config: Dict[str, Any] = None
):
    """
    Configuración rápida de la biblioteca multitenant
    
    Args:
        db_url: URL de la base de datos (opcional, usar db_config en su lugar)
        strategy: Estrategia de tenencia a usar
        tenants: Diccionario de tenants a configurar
        db_config: Configuración detallada de la base de datos
    
    Returns:
        Dict con los componentes configurados
    """
    if db_config is None and db_url is None:
        raise ValueError("Se debe proporcionar db_config o db_url")
    
    # Inicializa el manager con configuración por defecto
    manager = MultiTenantManager()
    manager.set_default_strategy(strategy)
    
    if tenants:
        for tenant_id, config in tenants.items():
            manager.configure_tenant(tenant_id, config)
    
    tenant_context.tenant_manager = manager
    
    # Configurar sesión de base de datos
    if db_config:
        session = MultiTenantSession(db_config, strategy)
    else:
        # Extraer componentes de db_url si se proporciona
        import re
        match = re.match(r'(\w+)://(\w+):(\w+)@([\w\.]+):(\d+)/(\w+)', db_url)
        if match:
            driver, username, password, host, port, database = match.groups()
            db_config = {
                "db_driver": driver,
                "db_host": host,
                "db_port": port,
                "db_username": username,
                "db_password": password,
                "db_name": database
            }
            session = MultiTenantSession(db_config, strategy)
        else:
            raise ValueError("Formato de db_url no válido")
    
    return {
        "session": session,
        "manager": manager,
        "strategy": strategy,
        "tenant_context": tenant_context
    }