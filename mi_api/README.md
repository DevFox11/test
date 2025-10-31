# mi_api - Aplicación de Prueba para Hidra

Esta es una aplicación FastAPI que sirve como banco de pruebas y demostración para la biblioteca `hidra`. La aplicación demuestra todas las funcionalidades de la biblioteca multitenant.

## Descripción

`mi_api` es una API REST que implementa patrones multitenant completos usando la biblioteca `hidra`. Incluye endpoints para probar cada característica de la biblioteca, desde la configuración básica hasta funcionalidades avanzadas.

## Características

- **Implementación completa de multitenancy** con la biblioteca `hidra`
- **Tres estrategias de tenencia** disponibles: DATABASE_PER_TENANT, SCHEMA_PER_TENANT, ROW_LEVEL
- **Protección de endpoints** con decoradores como `@requires_tenant`
- **Operaciones CRUD** por tenant con datos completamente aislados
- **Endpoints de diagnóstico** para verificar el estado del sistema
- **Soporte para PostgreSQL** con esquemas por tenant
- **Modelos de datos extendidos** con `TenantAwareModel`

## Configuración

### Prerrequisitos

- Python 3.8+
- PostgreSQL (si se usa la estrategia de esquemas)

### Instalación

1. Instalar la biblioteca `hidra`:
   ```bash
   cd ../hidra
   pip install -e .
   ```

2. Instalar dependencias de la API:
   ```bash
   pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic
   ```

### Variables de Configuración

La aplicación está configurada para usar PostgreSQL con la estrategia de esquemas por tenant. Puedes modificar estos valores en el archivo `main.py`:

- `CURRENT_STRATEGY`: Estrategia de tenencia actual
- Configuración de base de datos: host, puerto, usuario, contraseña, nombre de base de datos

## Ejecución

```bash
uvicorn main:app --reload --port 8000
```

Luego visita `http://localhost:8000/docs` para ver la documentación interactiva de la API.

## Endpoints Disponibles

### Públicos (no requieren tenant)

- `GET /` - Información básica de la API
- `GET /health` - Estado de salud del servicio
- `GET /tenants` - Lista de tenants configurados
- `GET /schemas` - Lista de esquemas en la base de datos
- `GET /strategies` - Información sobre estrategias de tenencia
- `GET /debug/database` - Diagnóstico de base de datos
- `GET /debug/tenant-test` - Prueba de funcionalidad de tenant

### Protegidos (requieren header X-Tenant-ID)

- `GET /users` - Obtener usuarios del tenant
- `POST /users` - Crear usuario en el tenant
- `GET /products` - Obtener productos del tenant
- `POST /products` - Crear producto en el tenant
- `GET /tenant-aware-orders` - Obtener órdenes usando TenantAwareModel
- `POST /tenant-aware-orders` - Crear orden usando TenantAwareModel
- `GET /premium-feature` - Feature solo para tenants premium
- `GET /admin-access` - Feature solo para tenant enterprise
- `GET /tenant-context` - Información del contexto de tenant
- `GET /debug/current-schema` - Verificar esquema actual

### Administrativos

- `GET /temp-tenant` - Probar contexto temporal de tenant
- `GET /async-temp-tenant` - Probar contexto temporal asincrónico
- `GET /test-errors` - Probar manejo de errores
- `POST /run-all-migrations` - Ejecutar migraciones para todos los tenants
- `POST /configure-tenant` - Configurar nuevo tenant dinámicamente
- `GET /all-tenants-info` - Obtener información de todos los tenants

## Uso de Headers

Para acceder a los endpoints protegidos, debes incluir el header `X-Tenant-ID` con el ID de un tenant válido:

```
X-Tenant-ID: acme_corp
```

## Estrategias de Tenencia

La aplicación está configurada con `SCHEMA_PER_TENANT` por defecto, lo que significa que cada tenant tiene su propio esquema en la base de datos PostgreSQL.

## Desarrollo

La aplicación incluye múltiples endpoints para probar cada característica de la biblioteca `hidra`:

1. **Aislamiento de datos**: Cada tenant tiene acceso solo a sus propios datos
2. **Gestión de contexto**: El contexto de tenant se mantiene durante la solicitud
3. **Manejo de errores**: Respuestas claras para diferentes tipos de errores
4. **Migraciones**: Sistema para ejecutar migraciones en todos los tenants
5. **Modelos especializados**: Uso de TenantAwareModel para estrategia ROW_LEVEL

## Pruebas

Para probar completamente la aplicación:

1. Inicia el servidor: `uvicorn main:app --reload --port 8000`
2. Visita `http://localhost:8000/docs` para ver los endpoints
3. Usa herramientas como Postman o curl para probar los endpoints
4. Recuerda incluir el header `X-Tenant-ID` para endpoints protegidos

## Integración con Hidra

Esta aplicación demuestra cómo integrar `hidra` en un proyecto real:

- Configuración inicial con `MultiTenantSession`
- Uso de middleware para identificación automática de tenant
- Decoradores para protección de endpoints
- Modelos de datos adaptados para multitenancy
- Manejo de errores personalizados