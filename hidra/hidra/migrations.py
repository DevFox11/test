from typing import Callable, Awaitable, Optional
import asyncio
import inspect
from sqlalchemy.orm.session import Session

from hidra.core import tenant_context

def run_migrations_for_all_tenants(
    session_factory: Callable[[], Session],
    migration_func: Callable[[Session, str], Optional[Awaitable[None]]]
):
    """
    Ejecuta migraciones para todos los tenants registrados.

    - Acepta funciones de migración síncronas o asíncronas.
    - Funciona en contextos síncronos, ejecutando internamente el bucle de eventos.
    """

    async def _run_async():
        manager = tenant_context.tenant_manager
        all_tenants = await manager.get_all_tenant_ids()

        if not all_tenants:
            print("No tenants found to migrate.")
            return

        print(f"Found {len(all_tenants)} tenants to migrate: {all_tenants}")

        for tenant_id in all_tenants:
            print(f"--- Running migration for tenant: {tenant_id} ---")
            try:
                tenant_context.set_tenant(tenant_id)
                session = session_factory()

                result = migration_func(session, tenant_id)
                if inspect.isawaitable(result):
                    await result

                session.commit()
                print(f"✅ Migration successful for tenant: {tenant_id}")
            except Exception as e:
                print(f"❌ Migration FAILED for tenant: {tenant_id}")
                print(f"   Error: {e}")
                if 'session' in locals() and session.is_active:
                    session.rollback()
            finally:
                if 'session' in locals():
                    session.close()
                tenant_context.set_tenant(None)

        print("--- All tenant migrations complete. ---")

    try:
        asyncio.get_running_loop()
        # Si ya hay bucle, programar tarea
        return asyncio.create_task(_run_async())
    except RuntimeError:
        # No hay bucle: ejecutar de forma bloqueante
        asyncio.run(_run_async())