"""
Test rápido para verificar que las nuevas funcionalidades funcionan
"""
def test_new_features():
    # Probar importaciones
    from hidra import (
        quick_start,
        requires_tenant,
        HidraDB,
        create_db_session,
        diagnose_setup,
        print_diagnosis,
        get_current_tenant_id,
        tenant_exists,
        get_current_tenant_config,
        setup_fastapi_app
    )
    
    print("[OK] Todas las nuevas funciones se pueden importar correctamente")
    
    # Probar quick_start con configuración mínima
    config = quick_start(
        db_config={
            "db_driver": "sqlite",
            "db_name": ":memory:"
        },
        tenants={
            "test_tenant": {"plan": "basic"}
        }
    )
    
    assert config["manager"] is not None
    assert config["session"] is not None
    assert "test_tenant" in config["manager"].tenant_configs
    print("[OK] quick_start funciona correctamente")
    
    # Probar diagnóstico
    diagnosis = diagnose_setup()
    assert diagnosis["status"] in ["healthy", "needs_attention"]
    print("[OK] Funciones de diagnóstico funcionan correctamente")
    
    print("\n[SUCCESS] Todas las nuevas funcionalidades están trabajando correctamente!")

if __name__ == "__main__":
    test_new_features()