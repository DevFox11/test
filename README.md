# Proyecto Hidra - Biblioteca Multitenant para Python

## Descripción General

Este proyecto contiene dos componentes principales:

1. **hidra**: Una biblioteca ligera y agnóstica a frameworks para implementar aplicaciones multitenant en Python.
2. **mi_api**: Una aplicación FastAPI que sirve como demostración y banco de pruebas para la biblioteca `hidra`.

## Características de la Biblioteca `hidra`

- **Framework-Agnóstico**: Funciona con cualquier framework web de Python (FastAPI, Flask, etc.)
- **Múltiples Estrategias de Tenencia**:
  - DATABASE_PER_TENANT: Cada tenant tiene una base de datos separada
  - SCHEMA_PER_TENANT: Cada tenant tiene un esquema separado en la misma base de datos
  - ROW_LEVEL: Todos los tenants comparten la misma base de datos con aislamiento a nivel de fila
- **Contexto Seguro**: Utiliza `contextvars` para manejo seguro de contexto entre hilos/corutinas
- **Middleware Integrado**: Middleware para FastAPI que identifica tenants automáticamente
- **Decoradores Potentes**: `@tenant_required`, `@requires_tenant`, `@specific_tenants`
- **Sesiones de Base de Datos Inteligentes**: Gestión automática de conexiones por tenant
- **Modelos Especializados**: `TenantAwareModel` para estrategia ROW_LEVEL

## Estructura del Proyecto

```
test/
├── hidra/                 # Biblioteca principal
│   ├── hidra/            # Código fuente
│   ├── tests/            # Tests unitarios
│   ├── examples/         # Ejemplos de uso
│   ├── pyproject.toml
│   └── README.md
├── mi_api/               # Aplicación de ejemplo
│   ├── main.py          # API FastAPI para pruebas
│   └── main_test.py
├── README.md             # Documentación principal
└── .gitignore           # Archivos a ignorar
```

## Prerrequisitos

1. **Python 3.8+**
2. **PostgreSQL** (para pruebas completas) o SQLite (para pruebas básicas)
3. **Paquetes necesarios**:
   - SQLAlchemy >= 1.4.0
   - FastAPI (opcional)
   - Pydantic (opcional)

## Instalación y Configuración

### Instalar la biblioteca `hidra`

```bash
# Desde el directorio C:\Users\WINDOWS 11\test\hidra
pip install -e .

# O para instalar con dependencias de desarrollo
pip install -e ".[dev]"
```

### Dependencias para `mi_api`

```bash
# Desde el directorio C:\Users\WINDOWS 11\test\mi_api
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic
```

## Uso Básico

### Configuración Rápida

```python
from hidra import quick_start

# Configuración mínima
config = quick_start(
    db_config={
        "db_driver": "sqlite",
        "db_name": "example.db"
    },
    tenants={
        "empresa1": {"plan": "premium"},
        "empresa2": {"plan": "basic"}
    }
)
```

### Integración con FastAPI

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from hidra import setup_fastapi_app, requires_tenant

app = FastAPI()
hidra = setup_fastapi_app(
    app,
    db_config={
        "db_driver": "postgresql",
        "db_host": "localhost",
        "db_port": "5432",
        "db_username": "postgres",
        "db_password": "password",
        "db_name": "multitenant"
    },
    tenants={
        "tenant1": {"plan": "premium"},
        "tenant2": {"plan": "basic"}
    }
)

@app.get("/users")
@requires_tenant()  # Requiere tenant
async def get_users(db: Session = Depends(hidra["session_getter"])):
    # tenant_context.get_tenant() contiene el tenant actual
    pass
```

## Pruebas de Funcionalidades

### 1. Prueba Básica de Configuración

**Endpoint:** `GET http://localhost:8000/`

### 2. Verificación de Tenants Configurados

**Endpoint:** `GET http://localhost:8000/tenants`

### 3. Prueba del Decorador `@requires_tenant`

**Endpoint:** `GET http://localhost:8000/users`

**Sin header (debe fallar):**
- Realiza una petición GET a `http://localhost:8000/users`
- Deberías recibir un error 400 con mensaje de error de tenant

**Con header (debe funcionar):**
- Realiza una petición GET a `http://localhost:8000/users` con header:
  - `X-Tenant-ID: acme_corp`
- Deberías recibir la lista de usuarios para ese tenant

### 4. Prueba de Operaciones CRUD

**Crear un usuario:**
- Endpoint: `POST http://localhost:8000/users`
- Headers: `X-Tenant-ID: acme_corp`
- Body (JSON):
```json
{
  "name": "John Doe",
  "email": "john@example.com"
}
```

### 5. Prueba de Estrategias de Tenencia

**Endpoint:** `GET http://localhost:8000/strategies`

### 6. Prueba de Contexto Temporal de Tenant

**Endpoints:**
- `GET http://localhost:8000/temp-tenant`
- `GET http://localhost:8000/async-temp-tenant`

### 7. Pruebas de Diagnóstico

**Funciones útiles:**
```python
from hidra import diagnose_setup, print_diagnosis

# Obtener diagnóstico detallado
diagnosis = diagnose_setup()

# Imprimir diagnóstico formateado
print_diagnosis()
```

## Características Avanzadas

### Nuevo Decorador `@requires_tenant`

Más flexible que `@tenant_required`:

```python
# Cualquier tenant con acceso
@requires_tenant()

# Solo tenant específico
@requires_tenant("premium_tenant")

# Lista de tenants permitidos
@requires_tenant(["tenant1", "tenant2"])
```

### Acceso Simplificado a Base de Datos

```python
from hidra import HidraDB

# Crear acceso simplificado a base de datos
hidra_db = HidraDB({
    "db_driver": "postgresql",
    "db_host": "localhost",
    "db_port": "5432", 
    "db_username": "postgres",
    "db_password": "password",
    "db_name": "multitenant"
})

# Usar con FastAPI Depends
@app.get("/users")
async def get_users(db: Session = Depends(hidra_db.get_tenant_db())):
    pass
```

### Funciones de Ayuda

```python
from hidra import get_current_tenant_id, tenant_exists

# Obtener ID del tenant actual
tenant_id = get_current_tenant_id()

# Verificar si un tenant existe
exists = tenant_exists("some_tenant_id")
```

## Ejecutar la Aplicación de Prueba

```bash
cd C:\Users\WINDOWS 11\test\mi_api
uvicorn main:app --reload --port 8000
```

Luego visita `http://localhost:8000/docs` para ver la documentación de la API interactiva.

## Ejecutar Tests

```bash
cd C:\Users\WINDOWS 11\test\hidra
python -m pytest tests/ -v
```

## Consideraciones Importantes

1. **Headers de Tenant**: Todos los endpoints protegidos requieren el header `X-Tenant-ID` con un valor de tenant válido.

2. **Estrategia Actual**: Por defecto, la aplicación usa `SCHEMA_PER_TENANT`. Para probar otras estrategias, cambia la constante `CURRENT_STRATEGY` en el archivo `main.py`.

3. **Base de Datos**: Asegúrate de que PostgreSQL esté corriendo y el nombre de la base de datos coincida con la configuración.

4. **Logs**: Observa la consola durante el inicio de la aplicación para ver mensajes de inicialización de tenants y esquemas.

## Solución de Problemas

**Error 400 - Tenant identification required:**
- Verifica que estás enviando el header `X-Tenant-ID`
- Verifica que el valor del tenant está en la lista de tenants configurados

**Error al crear esquemas:**
- Verifica la conexión a PostgreSQL y permisos
- Asegúrate de que la base de datos existe

**Datos compartidos entre tenants:**
- Verifica que estás usando los headers correctos en cada petición
- Confirma que la estrategia está configurada correctamente

## Recursos Adicionales

- **Ejemplos**: Revisa el directorio `hidra/examples/` para ver diferentes casos de uso
- **Tests**: Los tests en `hidra/tests/` también sirven como ejemplos de uso
- **Documentación de la API**: La documentación interactiva está disponible en `/docs` cuando se ejecuta la aplicación