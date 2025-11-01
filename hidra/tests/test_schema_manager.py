"""
Prueba para validar la implementación de SchemaManager
"""
import pytest
from unittest.mock import MagicMock
from hidra import SchemaManager
from hidra.exceptions import InvalidTenantNameError


def test_clean_tenant_name():
    """Prueba que la limpieza de nombres de tenant funcione correctamente"""
    db_config = {
        "db_driver": "postgresql",
        "db_host": "localhost",
        "db_port": "5432",
        "db_username": "postgres", 
        "db_password": "password",
        "db_name": "test_db"
    }
    
    schema_manager = SchemaManager(db_config)
    
    # Prueba con nombre que contiene guiones
    assert schema_manager.clean_tenant_name("company-1") == "company_1"
    assert schema_manager.clean_tenant_name("my-company-name") == "my_company_name"
    
    # Prueba con nombre que ya es válido
    assert schema_manager.clean_tenant_name("company1") == "company1"
    assert schema_manager.clean_tenant_name("my_company") == "my_company"
    
    # Prueba con nombre que comienza con número (debería añadir prefijo)
    assert schema_manager.clean_tenant_name("123company") == "tenant_123company"


def test_validate_tenant_name():
    """Prueba que la validación de nombres de tenant funcione correctamente"""
    db_config = {
        "db_driver": "postgresql",
        "db_host": "localhost",
        "db_port": "5432",
        "db_username": "postgres",
        "db_password": "password", 
        "db_name": "test_db"
    }
    
    schema_manager = SchemaManager(db_config)
    
    # Nombres válidos
    assert schema_manager.validate_tenant_name("company1") == True
    assert schema_manager.validate_tenant_name("my_company") == True
    assert schema_manager.validate_tenant_name("tenant_name_123") == True
    assert schema_manager.validate_tenant_name("_underscore_start") == True
    
    # Nombres inválidos
    assert schema_manager.validate_tenant_name("company-1") == False  # contiene guión
    assert schema_manager.validate_tenant_name("company.1") == False  # contiene punto
    assert schema_manager.validate_tenant_name("company 1") == False  # contiene espacio
    assert schema_manager.validate_tenant_name("company@tenant") == False  # carácter especial
    assert schema_manager.validate_tenant_name("-startdash") == False  # empieza con guión
    assert schema_manager.validate_tenant_name("") == False  # vacío
    
    # Nombre muy largo (>63 caracteres)
    long_name = "a" * 64
    assert schema_manager.validate_tenant_name(long_name) == False


def test_invalid_tenant_name_error():
    """Prueba que se lance la excepción correcta para nombres inválidos"""
    with pytest.raises(InvalidTenantNameError) as exc_info:
        raise InvalidTenantNameError("invalid-tenant", "Contiene guiones que no son válidos para PostgreSQL")
    
    assert "invalid-tenant" in str(exc_info.value)
    assert "no es válido para usar como nombre de schema en PostgreSQL" in str(exc_info.value)


if __name__ == "__main__":
    test_clean_tenant_name()
    test_validate_tenant_name()
    test_invalid_tenant_name_error()
    print("Todas las pruebas pasaron exitosamente!")