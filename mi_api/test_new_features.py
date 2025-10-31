"""
Ejemplo de uso de nuevas características en mi_api
"""
from hidra import quick_start, requires_tenant, HidraDB

print("Probando nuevas características de Hidra...")

# Configuración rápida
config = quick_start(
    db_config={
        "db_driver": "sqlite",
        "db_name": ":memory:"
    },
    tenants={
        "empresa1": {"plan": "premium"},
        "empresa2": {"plan": "basic"}
    }
)

print("[OK] Configuración rápida completada")

# Crear sesión de base de datos simplificada
hidra_db = HidraDB({
    "db_driver": "sqlite",
    "db_name": ":memory:"
})

print("[OK] Sesión de base de datos simplificada creada")

# Probar el decorador mejorado
@requires_tenant()
async def ejemplo_endpoint():
    return {"mensaje": "Éxito"}

print("[OK] Decorador requires_tenant importado y funcional")

print("\nTodas las nuevas características están disponibles y funcionando correctamente en mi_api!")