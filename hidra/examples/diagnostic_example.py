"""
Ejemplo de diagnóstico de configuración
"""
from hidra import quick_start, diagnose_setup, print_diagnosis

# Configurar una aplicación de ejemplo
quick_start(
    db_config={
        "db_driver": "sqlite",
        "db_name": "diagnostic_example.db"
    },
    tenants={
        "tenant1": {"plan": "premium"},
        "tenant2": {"plan": "basic"}
    }
)

# Ejecutar diagnóstico
print_diagnosis()

# O también puedes obtener el diagnóstico como diccionario
diagnosis = diagnose_setup()
print(f"\nDiagnóstico detallado: {diagnosis}")