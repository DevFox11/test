# Solución a Problemas Comunes con Hidra

## Problema 1: Creación de Tabla `tenants` en Schema Público

### Descripción
Originalmente, la biblioteca Hidra no creaba automáticamente la tabla `tenants` en el schema público, lo cual es necesario para gestionar metadatos de tenants de forma centralizada.

### Solución
La nueva clase `SchemaManager` ahora proporciona métodos para crear automáticamente la tabla `tenants` en el schema público:

```python
from hidra import SchemaManager

# Configuración de la base de datos
db_config = {
    "db_driver": "postgresql",
    "db_host": "localhost",
    "db_port": "5432",
    "db_username": "postgres",
    "db_password": "password",
    "db_name": "multitenant_db"
}

# Crear instancia de SchemaManager
schema_manager = SchemaManager(db_config)

# Configurar el entorno multitenant completo
# Esto crea la tabla 'tenants' en el schema público
schema_manager.setup_multi_tenant_environment()
```

La tabla `tenants` en el schema público contendrá:

```sql
CREATE TABLE public.tenants (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
);
```

## Problema 2: Compatibilidad con PostgreSQL y Nombres de Schemas

### Descripción
PostgreSQL no permite guiones (`-`) en los nombres de schemas. Si una aplicación usaba nombres de tenants con guiones, como `my-company`, esto causaría errores en PostgreSQL.

### Solución
La clase `SchemaManager` ahora incluye validación y limpieza de nombres de tenants:

```python
# Validar si un nombre es válido para PostgreSQL
is_valid = schema_manager.validate_tenant_name("my-company")  # False

# Limpiar el nombre para hacerlo compatible
clean_name = schema_manager.clean_tenant_name("my-company")  # "my_company"

# El método initialize_tenant maneja automáticamente esta conversión
schema_manager.initialize_tenant(
    tenant_id="my-company",
    tenant_name="My Company",
    create_tables_func=your_create_tables_function
)
```

### Configuración Automática
Cuando se inicializa un tenant, el sistema:

1. Valida el nombre del tenant
2. Si es inválido, lo limpia para crear un nombre de schema válido
3. Crea el schema usando el nombre limpio
4. Registra el tenant en la tabla pública usando el ID original
5. Crea las tablas del tenant en su schema específico

## Uso Completo

### Implementación Completa

```python
from hidra import SchemaManager, create_hidra_app, TenancyStrategy
from fastapi import FastAPI

app = FastAPI()

# Configurar Hidra con FastAPI
app = create_hidra_app(
    app=app,
    db_config=db_config,
    strategy=TenancyStrategy.SCHEMA_PER_TENANT
)

# Crear SchemaManager para manejo avanzado de schemas
schema_manager = SchemaManager(db_config)

# Configurar entorno multitenant completo
schema_manager.setup_multi_tenant_environment()

# Inicializar un tenant (con manejo automático de nombres inválidos)
schema_manager.initialize_tenant(
    tenant_id="company-1",  # Nombre con guiones
    tenant_name="Company One",
    create_tables_func=create_tenant_tables  # Función para crear tablas del tenant
)
```

## Beneficios

1. **Separación de datos clara**: La tabla `tenants` en el schema público gestiona todos los tenants
2. **Compatibilidad con PostgreSQL**: Nombres de schemas válidos automáticamente
3. **Fácil mantenimiento**: Todos los metadatos de tenants en un solo lugar
4. **Flexibilidad**: Soporte para nombres de tenants con formatos antiguos (se convierten automáticamente)