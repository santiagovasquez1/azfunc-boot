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
        Inicializa el controlador base con el contenedor de dependencias y el blueprint.

        Args:
            container: Contenedor de inyección de dependencias.
            bp: Blueprint de Azure Functions.
        """
        self.container: DependencyContainer = container
        # Envuelve el blueprint con ScopedBlueprint para interceptar las llamadas
        # a cualquier trigger (route, timer_trigger, blob_trigger, etc.)
        # y aplicar scope automáticamente
        self.bp: ScopedBlueprint = ScopedBlueprint(bp, self)
        self.register_routes()

    def _json_response(self, data: dict, status_code: int = 200) -> HttpResponse:
        """
        Crea una respuesta HTTP con JSON.

        Args:
            data: Datos a serializar como JSON
            status_code: Código de estado HTTP (default: 200)

        Returns:
            HttpResponse con JSON y mimetype correcto
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
        Crea una respuesta HTTP de error con JSON.

        Args:
            error_message: Mensaje de error
            status_code: Código de estado HTTP (default: 500)

        Returns:
            HttpResponse con error en JSON
        """
        return self._json_response({"error": error_message}, status_code)

    @abstractmethod
    def register_routes(self) -> None:
        """
        Método abstracto que debe ser implementado por las clases hijas
        para registrar las rutas/triggers del controlador.
        """
        pass

    def _wrap_with_scope(self, method: Callable[..., Any]) -> Callable[..., Any]:
        """
        Envuelve un método del controlador para crear automáticamente un scope
        antes de ejecutarlo y limpiarlo después. Similar al comportamiento de
        IServiceScope en .NET cuando se ejecuta un método de un controller.

        Args:
            method: Método del controlador que será envuelto con scope.

        Returns:
            Método envuelto con manejo automático de scope (async o sync según corresponda).
        """
        # Detecta si el método es async o sync
        if asyncio.iscoroutinefunction(method):
            return self._create_async_wrapper(method)
        else:
            return self._create_sync_wrapper(method)

    def _create_async_wrapper(self, method: Callable[..., Any]) -> Callable[..., Any]:
        """
        Crea un wrapper asíncrono que maneja el scope para métodos async.

        Args:
            method: Método del controlador que será envuelto.

        Returns:
            Función async envuelta con manejo de scope.
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
        Crea un wrapper síncrono que maneja el scope para métodos sync.

        Args:
            method: Método del controlador que será envuelto.

        Returns:
            Función sync envuelta con manejo de scope.
        """

        @functools.wraps(method)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            scope = ScopeManager.create_scope()
            ScopeManager.set_current_scope(scope)
            try:
                result = method(*args, **kwargs)
                # Si el resultado es una coroutine, el desarrollador debería usar métodos async
                if asyncio.iscoroutine(result):
                    logging.warning(
                        f"El método {method.__name__} es síncrono pero retorna una coroutine. "
                        "Considere hacer el método async para un mejor manejo del scope."
                    )
                return result
            finally:
                # Para métodos síncronos, hacemos dispose síncrono
                self._dispose_scope_sync(scope)
                ScopeManager.clear_current_scope()

        return sync_wrapper

    @staticmethod
    def _dispose_scope_sync(scope: Dict[Any, Any]) -> None:
        """
        Versión síncrona de dispose_scope para métodos síncronos.
        Solo llama a dispose() si es síncrono. Si es async, registra un warning.

        Args:
            scope: Diccionario que contiene las instancias de servicios scoped.
        """
        for instance in scope.values():
            if isinstance(instance, IDisposable):
                if hasattr(instance, "dispose") and callable(instance.dispose):
                    # Para métodos síncronos, solo llamamos dispose síncrono
                    if not asyncio.iscoroutinefunction(instance.dispose):
                        instance.dispose()
                    else:
                        # Si es async, no podemos llamarlo desde un contexto síncrono
                        logging.warning(
                            f"El servicio {type(instance).__name__} tiene un dispose() async "
                            "pero se está intentando llamar desde un contexto síncrono. "
                            "Considere usar métodos async en los controladores."
                        )
