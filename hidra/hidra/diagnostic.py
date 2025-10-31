"""
Herramientas de diagnóstico para la biblioteca Hidra
"""
import sys
from .core import tenant_context

# Importar la versión de manera segura para evitar conflictos de importación circular
def _get_version():
    try:
        from . import __version__
        return __version__
    except ImportError:
        # En caso de problemas de importación circular, usar un valor predeterminado
        return "unknown"

hidra_version = _get_version()

def diagnose_setup():
    """
    Diagnóstico de configuración
    """
    diagnosis = {
        "python_version": sys.version,
        "hidra_version": hidra_version,
        "tenant_context_set": tenant_context.get_tenant() is not None,
        "manager_configured": len(tenant_context.tenant_manager.tenant_configs) > 0,
        "default_strategy": tenant_context.tenant_manager.default_strategy.value,
        "configured_tenants": list(tenant_context.tenant_manager.tenant_configs.keys()),
        "database_connection": "unknown"  # Se podría mejorar para probar conexión
    }
    
    # Validaciones
    issues = []
    if not diagnosis["manager_configured"]:
        issues.append("No se han configurado tenants")
    
    if not diagnosis["tenant_context_set"]:
        issues.append("Contexto de tenant no establecido")
    
    diagnosis["issues"] = issues
    diagnosis["status"] = "healthy" if not issues else "needs_attention"
    
    return diagnosis

def print_diagnosis():
    """
    Imprime diagnóstico formateado
    """
    diagnosis = diagnose_setup()
    
    print("🔍 Diagnóstico de Hidra")
    print("=" * 30)
    print(f"Versión: {diagnosis['hidra_version']}")
    print(f"Estado: {diagnosis['status']}")
    print(f"Strategia: {diagnosis['default_strategy']}")
    print(f"Tenants: {len(diagnosis['configured_tenants'])}")
    
    if diagnosis['issues']:
        print("\n⚠️  Problemas detectados:")
        for issue in diagnosis['issues']:
            print(f"  - {issue}")
    else:
        print("\n✅ Todo está correctamente configurado")
    
    if diagnosis['configured_tenants']:
        print(f"\nTenants configurados: {', '.join(diagnosis['configured_tenants'])}")
    
    return diagnosis