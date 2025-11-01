# Guía de Uso Estándar de Hidra

## Introducción

Hidra es una biblioteca ligera para implementar multitenancia en aplicaciones Python/FastAPI. Esta guía documenta la única forma estándar que utilizaremos para garantizar consistencia y mantenibilidad en todos los proyectos.

## Forma Estándar de Uso

### 1. Configuración Inicial

La forma estándar de inicializar Hidra es usar la función `initialize_hidra_fastapi()`:

```python
from hidra import initialize_hidra_fastapi

app = initialize_hidra_fastapi()
```

### 2. Administración del Esquema

Usaremos el `SchemaManager` para todas las operaciones de administración de esquemas:

```python
from hidra.schema_manager import SchemaManager

schema_manager = SchemaManager()
```

El `SchemaManager` incluye funcionalidades para:
- Validar nombres de inquilinos
- Limpiar nombres de inquilinos (convertir guiones a guiones bajos para compatibilidad con PostgreSQL)
- Crear esquemas para inquilinos

### 3. Modelo de Inquilinos

**El desarrollador es responsable de crear la tabla `tenants` en el esquema público.** La tabla debe definirse en `app/models/tenant_model.py` con la estructura personalizada que necesite el proyecto.

```python
# app/models/tenant_model.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    schema_name = Column(String, unique=True, nullable=False)
    # Añade otros campos según sea necesario
```

**Importante**: Hidra no creará automáticamente la tabla `tenants`, solo interactuará con una tabla que ya exista.

### 4. Separación de Modelos

Los modelos de inquilinos deben mantenerse separados de otros modelos de negocio:

- `app/models/tenant_model.py` - Define la estructura de la tabla `tenants`
- `app/models/__init__.py` o `app/models/business_models.py` - Define modelos para datos de negocio

### 5. Aislamiento de Datos

Cada inquilino obtiene su propio esquema PostgreSQL con datos completamente aislados de otros inquilinos.

### 6. Autenticación y Autorización

Implementa autenticación JWT con permisos basados en roles como parte del sistema de seguridad:

- Puntos de entrada para gestión de usuarios y roles
- Middleware para autenticación automática
- Control de acceso basado en roles

## Ejemplo Completo

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from hidra import initialize_hidra_fastapi
from hidra.schema_manager import SchemaManager
from app.models.tenant_model import Tenant
from app.database import get_db

# Inicializar la aplicación FastAPI con Hidra
app = initialize_hidra_fastapi()

# Crear instancia del SchemaManager
schema_manager = SchemaManager()

@app.post("/tenants/")
def create_tenant(tenant_data: TenantCreate, db: Session = Depends(get_db)):
    # Validar y limpiar el nombre del inquilino
    clean_schema_name = schema_manager.validate_and_clean_tenant_name(tenant_data.name)
    
    # Crear el inquilino en la base de datos
    tenant = Tenant(name=tenant_data.name, schema_name=clean_schema_name)
    db.add(tenant)
    db.commit()
    
    # Crear el esquema para el inquilino
    schema_manager.create_tenant_schema(clean_schema_name)
    
    return tenant
```

## Convenciones Importantes

1. **Nombres de Esquemas**: Los nombres de esquemas no pueden contener guiones (-), solo guiones bajos (_)
2. **Responsabilidad del Desarrollador**: El desarrollador debe definir y crear la tabla `tenants` en el esquema público
3. **Un Solo Modelo de Inquilino**: Usamos un modelo personalizado en lugar de modelos predeterminados de Hidra
4. **Middlewares Automáticos**: El middleware de inquilino se configura automáticamente con `initialize_hidra_fastapi()`

## Seguridad

- Todos los endpoints deben incluir autenticación JWT
- El aislamiento de datos entre inquilinos se mantiene en el nivel de base de datos
- Las operaciones CRUD se realizan dentro del contexto del inquilino actual