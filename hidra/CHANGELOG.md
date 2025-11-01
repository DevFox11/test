# CHANGELOG

## [0.2.2] - 2025-10-31

### Added
- Nuevo módulo `schema_manager.py` para gestión avanzada de schemas
- Funcionalidad para crear la tabla `tenants` en el schema público
- Validación y limpieza de nombres de tenants para compatibilidad con PostgreSQL
- Soporte para reemplazo automático de guiones (-) por guiones bajos (_) en nombres de schemas
- Clase `SchemaManager` para manejo completo de entornos multitenant
- Nueva excepción `InvalidTenantNameError` para manejo de nombres inválidos
- Tests para la nueva funcionalidad de schema management

### Changed
- Actualizado el middleware para usar nombres de schemas limpios en la configuración de search_path
- Mejorada la validación de nombres de tenants para cumplir con las restricciones de PostgreSQL
- Actualizado README con documentación de las nuevas características
- Actualizado ejemplo de uso para demostrar la nueva funcionalidad

## [0.2.1] - 2025-10-31

### Added
- Sistema de carga automática de tenants con `AutoTenantLoader`
- Función `create_hidra_app()` para configuración mínima en FastAPI
- Función `initialize_hidra_fastapi()` para integración automática
- Configuración sin código previo de tenants (carga dinámica)
- Validación automática de tenants sin definirlos en código
- Soporte para carga de tenants desde múltiples fuentes (config, db, api)
- Ejemplos de uso con mínima configuración

### Changed
- Ahora se puede usar la biblioteca sin definir tenants en el código
- La configuración mínima para FastAPI se reduce a 3 líneas
- Mejorada la documentación con ejemplos de configuración mínima

## [0.2.0] - 2025-10-31

### Added
- Función `quick_start()` para configuración rápida de la biblioteca
- Decorador mejorado `requires_tenant()` con parámetros más flexibles
- Clase `HidraDB` para acceso simplificado a base de datos
- Función `create_db_session()` para creación simplificada de sesiones
- Herramientas de diagnóstico: `diagnose_setup()` y `print_diagnosis()`
- Funciones de ayuda: `get_current_tenant_id()`, `tenant_exists()`, `get_current_tenant_config()`
- Función `setup_fastapi_app()` para integración simplificada con FastAPI
- Excepciones mejoradas con mensajes amigables y sugerencias
- Soporte para ambas interfaces del middleware (anterior y nueva)
- Ejemplos de uso en directorio `examples/`

### Changed
- Mejorada la compatibilidad hacia atrás del middleware
- Actualizados los mensajes de error para ser más descriptivos
- Simplificada la configuración inicial de la biblioteca
- Actualizados los READMEs con información sobre nuevas características

### Fixed
- Problemas de importación circular en el módulo de diagnóstico
- Compatibilidad con versiones antiguas de middleware en tests
- Codificación de caracteres en archivos de ejemplo

## [0.1.0] - Fecha inicial

### Added
- Biblioteca base para multitenancy en Python
- Soporte para múltiples estrategias de tenencia
- Middleware para FastAPI
- Decoradores para protección de endpoints
- Soporte para contextvars
- Tests unitarios básicos