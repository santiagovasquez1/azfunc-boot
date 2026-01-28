import asyncio
import functools
import json
import logging
from abc import ABC, abstractmethod
from typing import Callable, Any, Dict
from azfunc_boot.common.disposable import IDisposable
from azfunc_boot.di.dependency_injector import DependencyContainer
from azfunc_boot.di.scope import ScopeManager
from azfunc_boot.mvc.scoped_blueprint import ScopedBlueprint
from azure.functions import Blueprint, HttpResponse


class BaseController(ABC):
    def __init__(self, container: DependencyContainer, bp: Blueprint) -> None:
        """
        Initializes the base controller with the dependency container and blueprint.

        Args:
            container: Dependency injection container.
            bp: Azure Functions Blueprint.
        """
        self.container: DependencyContainer = container
        # Wraps the blueprint with ScopedBlueprint to intercept calls
        # to any trigger (route, timer_trigger, blob_trigger, etc.)
        # and automatically apply scope
        self.bp: ScopedBlueprint = ScopedBlueprint(bp, self)
        self.register_routes()

    def _json_response(self, data: dict, status_code: int = 200) -> HttpResponse:
        """
        Creates an HTTP response with JSON.

        Args:
            data: Data to serialize as JSON
            status_code: HTTP status code (default: 200)

        Returns:
            HttpResponse with JSON and correct mimetype
        """
        return HttpResponse(
            json.dumps(data),
            status_code=status_code,
            mimetype="application/json",
        )

    def _error_response(
        self, error_message: str, status_code: int = 500
    ) -> HttpResponse:
        """
        Creates an HTTP error response with JSON.

        Args:
            error_message: Error message
            status_code: HTTP status code (default: 500)

        Returns:
            HttpResponse with error in JSON
        """
        return self._json_response({"error": error_message}, status_code)

    @abstractmethod
    def register_routes(self) -> None:
        """
        Abstract method that must be implemented by child classes
        to register the controller's routes/triggers.
        """
        pass

    def _wrap_with_scope(self, method: Callable[..., Any]) -> Callable[..., Any]:
        """
        Wraps a controller method to automatically create a scope
        before executing it and clean it up afterwards. Similar to the behavior of
        IServiceScope in .NET when executing a controller method.

        Args:
            method: Controller method that will be wrapped with scope.

        Returns:
            Method wrapped with automatic scope handling (async or sync as appropriate).
        """
        # Detects if the method is async or sync
        if asyncio.iscoroutinefunction(method):
            return self._create_async_wrapper(method)
        else:
            return self._create_sync_wrapper(method)

    def _create_async_wrapper(self, method: Callable[..., Any]) -> Callable[..., Any]:
        """
        Creates an async wrapper that handles scope for async methods.

        Args:
            method: Controller method that will be wrapped.

        Returns:
            Async function wrapped with scope handling.
        """

        @functools.wraps(method)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            scope = ScopeManager.create_scope()
            ScopeManager.set_current_scope(scope)
            try:
                result = await method(*args, **kwargs)
                return result
            finally:
                await ScopeManager.dispose_scope(scope)
                ScopeManager.clear_current_scope()

        return async_wrapper

    def _create_sync_wrapper(self, method: Callable[..., Any]) -> Callable[..., Any]:
        """
        Creates a sync wrapper that handles scope for sync methods.

        Args:
            method: Controller method that will be wrapped.

        Returns:
            Sync function wrapped with scope handling.
        """

        @functools.wraps(method)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            scope = ScopeManager.create_scope()
            ScopeManager.set_current_scope(scope)
            try:
                result = method(*args, **kwargs)
                # If the result is a coroutine, the developer should use async methods
                if asyncio.iscoroutine(result):
                    logging.warning(
                        f"Method {method.__name__} is sync but returns a coroutine. "
                        "Consider making the method async for better scope handling."
                    )
                return result
            finally:
                # For sync methods, we do sync dispose
                self._dispose_scope_sync(scope)
                ScopeManager.clear_current_scope()

        return sync_wrapper

    @staticmethod
    def _dispose_scope_sync(scope: Dict[Any, Any]) -> None:
        """
        Synchronous version of dispose_scope for sync methods.
        Only calls dispose() if it is synchronous. If it is async, logs a warning.

        Args:
            scope: Dictionary containing instances of scoped services.
        """
        for instance in scope.values():
            if isinstance(instance, IDisposable):
                if hasattr(instance, "dispose") and callable(instance.dispose):
                    # For sync methods, we only call sync dispose
                    if not asyncio.iscoroutinefunction(instance.dispose):
                        instance.dispose()
                    else:
                        # If it's async, we cannot call it from a sync context
                        logging.warning(
                            f"Service {type(instance).__name__} has an async dispose() "
                            "but it is being called from a sync context. "
                            "Consider using async methods in controllers."
                        )
