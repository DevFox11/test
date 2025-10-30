from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declared_attr

class TenantAwareModel:
    """
    Mixin para modelos que usan estrategia Row Level
    Añade automáticamente tenant_id a las tablas
    """
    
    @declared_attr
    def tenant_id(cls):
        return Column(String, nullable=False)