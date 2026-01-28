import asyncio
from contextvars import ContextVar
from typing import Any, Dict, Type, Optional
from azfunc_boot.common.disposable import IDisposable


class ScopeManager:
    """
    Static scope manager for scoped services.
    Encapsulates all functionality related to scope management,
    similar to IServiceScopeFactory in .NET.
    
    This class is static and does not need to be instantiated.
    All methods are static and access an internal private instance.
    """

    # Context variable to maintain the current scope (similar to AsyncLocal in .NET)
    _current_scope: ContextVar[Optional[Dict[Type, Any]]] = ContextVar(
        "_current_scope", default=None
    )

    @staticmethod
    def create_scope() -> Dict[Type, Any]:
        """
        Creates a new scope for scoped services.
        Similar to IServiceScopeFactory.CreateScope() in .NET.
        """
        return {}

    @staticmethod
    def set_current_scope(scope: Dict[Type, Any]) -> None:
        """
        Sets the current scope in the context.
        Similar to setting the scope in AsyncLocal in .NET.
        """
        ScopeManager._current_scope.set(scope)

    @staticmethod
    def get_current_scope() -> Optional[Dict[Type, Any]]:
        """
        Gets the current scope from the context.
        """
        return ScopeManager._current_scope.get()

    @staticmethod
    def clear_current_scope() -> None:
        """
        Clears the current scope from the context.
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
        Calls dispose() on all scoped services that implement IDisposable.
        """
        for instance in scope.values():
            if isinstance(instance, IDisposable):
                await ScopeManager._dispose_instance(instance)
