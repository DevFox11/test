"""
Clase simplificada para manejo de base de datos multitenant
"""
from typing import Dict, Any, Callable
from .database import MultiTenantSession
from .core import TenancyStrategy
from sqlalchemy.orm import Session

class HidraDB:
    """Clase simplificada para manejo de base de datos multitenant"""
    
    def __init__(self, config: Dict[str, Any], strategy: TenancyStrategy = None):
        self.session_manager = MultiTenantSession(config, strategy)
    
    def get_session(self) -> Session:
        """Obtiene sesión para el tenant actual"""
        return self.session_manager.get_session()
    
    def get_tenant_db(self) -> Callable:
        """Función lista para usar con FastAPI Depends()"""
        def _get_db():
            db = self.get_session()
            try:
                yield db
            finally:
                db.close()
        return _get_db

def create_db_session(config: Dict[str, Any], strategy: TenancyStrategy = None):
    """Función de conveniencia para crear una sesión de base de datos"""
    return HidraDB(config, strategy)