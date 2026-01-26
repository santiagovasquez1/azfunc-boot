import asyncio
from contextvars import ContextVar
from typing import Any, Dict, Type, Optional
from azfunc_boot.common.disposable import IDisposable


class ScopeManager:
    """
    Gestor estático de scopes para servicios scoped.
    Encapsula toda la funcionalidad relacionada con la gestión de scopes,
    similar a IServiceScopeFactory en .NET.
    
    Esta clase es estática y no necesita ser instanciada.
    Todos los métodos son estáticos y acceden a una instancia interna privada.
    """

    # Context variable para mantener el scope actual (similar a AsyncLocal en .NET)
    _current_scope: ContextVar[Optional[Dict[Type, Any]]] = ContextVar(
        "_current_scope", default=None
    )

    @staticmethod
    def create_scope() -> Dict[Type, Any]:
        """
        Crea un nuevo scope para servicios scoped.
        Similar a IServiceScopeFactory.CreateScope() en .NET.
        """
        return {}

    @staticmethod
    def set_current_scope(scope: Dict[Type, Any]) -> None:
        """
        Establece el scope actual en el contexto.
        Similar a establecer el scope en el AsyncLocal en .NET.
        """
        ScopeManager._current_scope.set(scope)

    @staticmethod
    def get_current_scope() -> Optional[Dict[Type, Any]]:
        """
        Obtiene el scope actual del contexto.
        """
        return ScopeManager._current_scope.get()

    @staticmethod
    def clear_current_scope() -> None:
        """
        Limpia el scope actual del contexto.
        """
        ScopeManager._current_scope.set(None)

    @staticmethod
    async def _dispose_instance(instance: Any) -> None:
        """
        Helper function to dispose a single instance.
        Handles both async and sync dispose methods.
        """
        if hasattr(instance, "dispose") and callable(instance.dispose):
            if asyncio.iscoroutinefunction(instance.dispose):
                await instance.dispose()
            else:
                instance.dispose()

    @staticmethod
    async def dispose_scope(scope: Dict[Type, Any]) -> None:
        """
        Llama a dispose() en todos los servicios scoped que implementen IDisposable.
        """
        for instance in scope.values():
            if isinstance(instance, IDisposable):
                await ScopeManager._dispose_instance(instance)
