"""
Funciones de ayuda para facilitar el uso de la biblioteca
"""
import asyncio
from typing import Union, List, Optional
from .core import tenant_context
from .exceptions import TenantContextError

def get_current_tenant_id() -> str:
    """
    Obtiene el ID del tenant actual o lanza una excepción amigable
    """
    tenant_id = tenant_context.get_tenant()
    if not tenant_id:
        raise TenantContextError("No se encontró tenant en el contexto actual. ¿Olvidaste agregar el middleware?")
    return tenant_id

def tenant_exists(tenant_id: str) -> bool:
    """
    Verifica si un tenant existe (función síncrona)
    """
    try:
        # Intentar obtener el loop actual
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No hay loop, ejecutar en un nuevo loop
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                lambda: asyncio.run(tenant_context.tenant_manager.tenant_exists(tenant_id))
            )
            return future.result()
    else:
        # Hay un loop en ejecución
        return asyncio.run(tenant_context.tenant_manager.tenant_exists(tenant_id))

def get_current_tenant_config() -> dict:
    """
    Obtiene la configuración del tenant actual
    """
    tenant_id = get_current_tenant_id()
    try:
        # Intentar obtener el loop actual
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No hay loop, ejecutar en un nuevo loop
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                lambda: asyncio.run(tenant_context.tenant_manager.get_tenant_config(tenant_id))
            )
            return future.result()
    else:
        # Hay un loop en ejecución
        return asyncio.run(tenant_context.tenant_manager.get_tenant_config(tenant_id))