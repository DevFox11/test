# Hidra Multitenancy: Lightweight Multi-Tenancy for Python

Hidra is a lightweight, framework-agnostic library for building multi-tenant applications in Python. It provides a simple and flexible way to manage tenants, allowing you to isolate tenant data using different strategies.

[![PyPI version](https://badge.fury.io/py/hidra-multitenancy.svg)](https://badge.fury.io/py/hidra-multitenancy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Key Features

- **Framework-Agnostic:** Designed to work with any Python web framework.
- **Multiple Tenancy Strategies:**
    - `DATABASE_PER_TENANT`: Each tenant has a separate database.
    - `SCHEMA_PER_TENANT`: Each tenant has a separate schema within the same database.
    - `ROW_LEVEL`: All tenants share the same database and tables, with data isolated by a tenant identifier column.
- **Context-Aware:** Uses `contextvars` to safely manage the current tenant's context, making it suitable for asynchronous applications.
- **Extensible:** Easily extendable to support custom tenancy strategies and tenant identification methods.
- **Optional Framework Integrations:** Provides optional, ready-to-use middlewares and decorators for FastAPI and Flask.
- **Easy Setup:** Simple configuration with `quick_start()` function
- **Enhanced Decorators:** Improved `requires_tenant()` decorator with more flexible options
- **Simplified Database Access:** `HidraDB` class for easier database session management
- **Diagnostic Tools:** Built-in functions to diagnose configuration issues
- **Helpful Error Messages:** Clear error messages with suggestions for resolution

## Installation

Install the library using `pip`:

```bash
# Core library
pip install hidra-multitenancy

# To include optional dependencies for FastAPI
pip install hidra-multitenancy[fastapi]

# To include optional dependencies for Flask
pip install hidra-multitenancy[flask]

# For development (includes testing and linting tools)
pip install hidra-multitenancy[dev]
```

## Enhanced Usage Examples

### Quick Start Configuration (With Predefined Tenants)

```python
from hidra import quick_start

# Simple configuration with predefined tenants
config = quick_start(
    db_config={
        "db_driver": "postgresql",
        "db_host": "localhost",
        "db_port": "5432",
        "db_username": "postgres",
        "db_password": "password",
        "db_name": "multitenant"
    },
    tenants={
        "company1": {"plan": "premium"},
        "company2": {"plan": "basic"}
    }
)
```

### Minimal Configuration for FastAPI (No Predefined Tenants Required)

```python
from fastapi import FastAPI
from hidra import create_hidra_app

# Create FastAPI app with minimal configuration
app = create_hidra_app(
    db_config={
        "db_driver": "postgresql",
        "db_host": "localhost",
        "db_port": "5432",
        "db_username": "postgres",
        "db_password": "password",
        "db_name": "multitenant"
    },
    # Tenants are loaded automatically when requested
    enable_auto_loading=True,
    auto_tenant_validation=True  # Validate tenants exist before processing
)

# Protected endpoint - no need to define tenants in code
@app.get("/data")
async def get_data():
    from hidra import get_current_tenant_id
    tenant_id = get_current_tenant_id()
    return {"tenant_id": tenant_id, "message": "Data retrieved"}
```

### Enhanced Decorators

```python
from hidra import requires_tenant

# Any tenant with access
@app.get("/data")
@requires_tenant()
async def get_data():
    pass

# Specific tenant only
@app.get("/premium-data")
@requires_tenant("premium_company")
async def get_premium_data():
    pass

# Multiple tenants allowed
@app.get("/shared-data")
@requires_tenant(["company1", "company2"])
async def get_shared_data():
    pass
```

### Simplified Database Access

```python
from hidra import HidraDB

# Create database access
hidra_db = HidraDB({
    "db_driver": "postgresql",
    "db_host": "localhost",
    "db_port": "5432",
    "db_username": "postgres",
    "db_password": "password",
    "db_name": "multitenant"
})

# Use with FastAPI Depends
@app.get("/users")
async def get_users(db: Session = Depends(hidra_db.get_tenant_db())):
    pass
```

### Basic Usage (with FastAPI)

Here's a quick example of how to use Hidra with FastAPI.

#### 1. Configure Tenants

First, configure your tenants and the tenancy strategy.

```python
# main.py
from hidra import tenant_context, TenancyStrategy, MultiTenantManager

# Initialize the tenant manager
manager = MultiTenantManager()

# Configure individual tenants
manager.configure_tenant("tenant1", {"db_connection": "postgresql://user:pass@host/db1"})
manager.configure_tenant("tenant2", {"db_connection": "postgresql://user:pass@host/db2"})

# Set the default strategy
manager.set_default_strategy(TenancyStrategy.DATABASE_PER_TENANT)

# Set the manager in the global tenant context
tenant_context.tenant_manager = manager
```

#### 2. Add the Middleware

The middleware identifies the tenant from the request (e.g., using a header) and sets it in the context.

```python
# main.py
from fastapi import FastAPI
from hidra.middleware import TenantMiddleware
from hidra.decorators import tenant_required

app = FastAPI()

# Add the middleware to your application
app.add_middleware(TenantMiddleware)

@app.get("/items")
@tenant_required
async def get_items():
    # The tenant is now available in the context
    current_tenant = tenant_context.require_tenant()
    
    # You can get tenant-specific configuration
    config = tenant_context.tenant_manager.get_tenant_config(current_tenant)
    
    return {"tenant_id": current_tenant, "db_connection": config.get("db_connection")}
```

### 3. Run the Application

To run this example, you would make a request with the `X-Tenant-ID` header:

```bash
curl -X GET "http://127.0.0.1:8000/items" -H "X-Tenant-ID: tenant1"
```

The response would be:

```json
{
  "tenant_id": "tenant1",
  "db_connection": "postgresql://user:pass@host/db1"
}
```

### Complete FastAPI Integration

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from hidra import setup_fastapi_app, requires_tenant

# Create FastAPI app
app = FastAPI()

# Setup Hidra with FastAPI
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

# Protected endpoint
@app.get("/users")
@requires_tenant()  # Requires tenant
async def get_users(db: Session = Depends(hidra["session_getter"])):
    from hidra import get_current_tenant_id
    tenant_id = get_current_tenant_id()
    return {"tenant_id": tenant_id, "message": "Users retrieved"}
```

## Diagnostic Tools

```python
from hidra import diagnose_setup, print_diagnosis

# Get diagnosis as dictionary
diagnosis = diagnose_setup()

# Print formatted diagnosis
print_diagnosis()
```

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue. If you want to contribute code, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Write your code and add tests.
4.  Ensure all tests pass and the code is formatted with `black` and linted with `ruff`.
5.  Submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
