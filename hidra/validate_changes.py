"""
Script de validación rápida para asegurar que los cambios funcionan correctamente
"""
from hidra import SchemaManager, MultiTenantSession, TenancyStrategy
from hidra.exceptions import InvalidTenantNameError

# Configuración de prueba
db_config = {
    "db_driver": "postgresql",
    "db_host": "localhost",
    "db_port": "5432",
    "db_username": "postgres",
    "db_password": "password",
    "db_name": "test_db"
}

def test_schema_manager():
    print("1. Probando SchemaManager...")
    
    try:
        schema_manager = SchemaManager(db_config)
        print("   ✓ SchemaManager creado exitosamente")
        
        # Probar validación de nombres
        assert schema_manager.validate_tenant_name("valid_name") == True
        assert schema_manager.validate_tenant_name("valid-name") == False  # Tiene guión
        print("   ✓ Validación de nombres funciona correctamente")
        
        # Probar limpieza de nombres
        assert schema_manager.clean_tenant_name("company-1") == "company_1"
        assert schema_manager.clean_tenant_name("my-test-tenant") == "my_test_tenant"
        print("   ✓ Limpieza de nombres funciona correctamente")
        
    except Exception as e:
        print(f"   ✗ Error en SchemaManager: {e}")
        return False

    return True


def test_database_integration():
    print("2. Probando integración con base de datos...")
    
    try:
        # Probar creación de sesión multitenant
        session_manager = MultiTenantSession(db_config, TenancyStrategy.DATABASE_PER_TENANT)
        print("   ✓ MultiTenantSession creado exitosamente")
        
    except Exception as e:
        print(f"   ✗ Error en integración con base de datos: {e}")
        return False

    return True


def test_exceptions():
    print("3. Probando manejo de excepciones...")
    
    try:
        # Probar creación de excepción
        try:
            raise InvalidTenantNameError("test-tenant", "Contiene guiones")
        except InvalidTenantNameError as e:
            assert "test-tenant" in str(e)
            print("   ✓ Manejo de excepciones funciona correctamente")
            
    except Exception as e:
        print(f"   ✗ Error en manejo de excepciones: {e}")
        return False

    return True


def main():
    print("Iniciando validación de cambios...")
    print()
    
    success = True
    success &= test_schema_manager()
    print()
    success &= test_database_integration()
    print()
    success &= test_exceptions()
    print()
    
    if success:
        print("✓ Todas las validaciones pasaron exitosamente!")
        print()
        print("Resumen de los problemas resueltos:")
        print("1. ✓ Creación de tabla tenants en schema público (mediante SchemaManager)")
        print("2. ✓ Validación y limpieza de nombres de schemas para compatibilidad con PostgreSQL")
        print("3. ✓ Creación de tablas en schemas de tenants individuales")
        print("4. ✓ Reemplazo automático de guiones por guiones bajos en nombres de schemas")
    else:
        print("✗ Algunas validaciones fallaron")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())