"""
Ejemplo de configuración mínima con Hidra
"""
from hidra import quick_start

# Configuración mínima
config = quick_start(
    db_config={
        "db_driver": "sqlite",
        "db_name": "example.db"
    },
    tenants={
        "company1": {"plan": "premium"},
        "company2": {"plan": "basic"}
    }
)

print("Configuración completada:")
print(f"- Tenant manager configurado: {config['manager'] is not None}")
print(f"- Sesión creada: {config['session'] is not None}")
print(f"- Tenants configurados: {list(config['manager'].tenant_configs.keys())}")