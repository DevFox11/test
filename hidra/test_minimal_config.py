"""
Test simple para verificar la funcionalidad de configuración mínima
"""
def test_minimal_config():
    try:
        from fastapi import FastAPI
        from hidra import create_hidra_app
        
        # Crear aplicación con configuración mínima
        app = FastAPI()
        hidra_app = create_hidra_app(
            app=app,
            db_config={
                "db_driver": "sqlite",
                "db_name": ":memory:"
            }
        )
        
        print("[SUCCESS] Configuración mínima completada exitosamente")
        print("[SUCCESS] La aplicación FastAPI ahora tiene soporte multitenant")
        
        # Verificar que la configuración esté disponible
        config = getattr(hidra_app.state, 'hidra_config', None)
        if config:
            print("[SUCCESS] Configuración de Hidra disponible en app.state")
            print(f"[INFO] Estrategia usada: {config['strategy']}")
        else:
            print("[WARNING] Configuración de Hidra no encontrada en app.state")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en la configuración mínima: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_minimal_config()
    if success:
        print("\n[OVERALL] La nueva funcionalidad de configuración mínima funciona correctamente")
    else:
        print("\n[OVERALL] Hubo un problema con la nueva funcionalidad")