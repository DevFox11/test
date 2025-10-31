# Ejemplos de Hidra

Esta carpeta contiene ejemplos que demuestran las diferentes funcionalidades de la biblioteca Hidra.

## Ejemplos Disponibles

### 1. Configuración Mínima
- **Archivo:** `simple_example.py`
- **Descripción:** Muestra la configuración más básica de Hidra
- **Uso:** `python simple_example.py`

### 2. Integración con FastAPI
- **Archivo:** `fastapi_example.py`
- **Descripción:** Ejemplo completo de integración con FastAPI usando los nuevos decoradores y funciones simplificadas
- **Uso:** `python fastapi_example.py` y visita `http://localhost:8000/docs`

### 3. Diagnóstico de Configuración
- **Archivo:** `diagnostic_example.py`
- **Descripción:** Muestra cómo usar las herramientas de diagnóstico de Hidra
- **Uso:** `python diagnostic_example.py`

## Características Mejoradas

Los ejemplos demuestran las siguientes mejoras:

1. **Configuración rápida** con `quick_start()`
2. **Decoradores simplificados** con `requires_tenant()`
3. **Manejo simplificado de base de datos** con `HidraDB`
4. **Herramientas de diagnóstico** con `diagnose_setup()` y `print_diagnosis()`
5. **Integración simplificada** con frameworks como FastAPI
6. **Mensajes de error mejorados** con sugerencias útiles
7. **Funciones de ayuda** como `get_current_tenant_id()`

## Requisitos

Asegúrate de tener instaladas las dependencias necesarias:

```bash
pip install fastapi uvicorn sqlalchemy
```

Para ejecutar los ejemplos, entra en el directorio de cada ejemplo y ejecuta el archivo correspondiente.