import asyncio
import inspect
import typing
from typing import Callable, Any, Dict, Type, List, Optional

from azfunc_boot.common.disposable import IDisposable
from azfunc_boot.common.exceptions.not_found_error import NotFoundError
from azfunc_boot.common.exceptions.validation_error import ValidationError
from azfunc_boot.di.scope import ScopeManager


class ServiceLifetime:
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class ServiceRegistration:
    """
    Estructura para guardar la información de cada servicio registrado.
    """

    def __init__(self, factory: Callable[[], Any], lifetime: str):
        self.factory = factory
        self.lifetime = lifetime


class DependencyContainer:
    def __init__(self):
        self._services: Dict[Type, List[ServiceRegistration]] = {}
        # _singletons guarda las instancias de servicios en modo SINGLETON
        self._singletons: Dict[Type, Any] = {}

    def add_singleton(
        self,
        service_type: Type,
        implementation_factory: Optional[Callable[[], Any]] = None,
    ):
        """
        Registra un servicio con ciclo de vida SINGLETON.
        Si implementation_factory es None, se asume que service_type
        es a la vez la "clave" y la implementación.
        """
        self.add_service(
            service_type,
            implementation_factory or (lambda: self._create_instance(service_type)),
            lifetime=ServiceLifetime.SINGLETON,
        )

    def add_transient(
        self,
        service_type: Type,
        implementation_factory: Optional[Callable[[], Any]] = None,
    ):
        """
        Registra un servicio con ciclo de vida TRANSIENT.
        """
        self.add_service(
            service_type,
            implementation_factory or (lambda: self._create_instance(service_type)),
            lifetime=ServiceLifetime.TRANSIENT,
        )

    def add_scoped(
        self,
        service_type: Type,
        implementation_factory: Optional[Callable[[], Any]] = None,
    ):
        """
        Registra un servicio con ciclo de vida SCOPED.
        """
        self.add_service(
            service_type,
            implementation_factory or (lambda: self._create_instance(service_type)),
            lifetime=ServiceLifetime.SCOPED,
        )

    # ----------------------------------------------------------------------
    # Método genérico principal para registrar servicios
    # ----------------------------------------------------------------------
    def add_service(
        self,
        service_type: Type,
        implementation_factory: Callable[[], Any],
        lifetime: str = ServiceLifetime.SINGLETON,
    ):
        """
        Registra un servicio en el contenedor.
        Permite múltiples registros para la misma "clave" (service_type).
        """
        if service_type not in self._services:
            self._services[service_type] = []

        self._services[service_type].append(
            ServiceRegistration(factory=implementation_factory, lifetime=lifetime)
        )

    # ----------------------------------------------------------------------
    # Resolución de servicios
    # ----------------------------------------------------------------------
    def get_service(
        self, service_type: Type, scope: Optional[Dict[Type, Any]] = None
    ) -> Any:
        """
        Devuelve una instancia de la primera implementación registrada para 'service_type'.
        Si hay múltiples registros, retorna una lista de todas las implementaciones.

        Si scope es None, intenta obtener el scope del contexto actual (similar a .NET).
        """
        # Si no se proporciona un scope explícito, intenta obtenerlo del contexto
        if scope is None:
            scope = ScopeManager.get_current_scope()

        services = self._services.get(service_type)
        if not services or len(services) == 0:
            raise NotFoundError(
                f"No se ha registrado el servicio para {service_type.__name__}"
            )

        # Si solo hay un servicio registrado, devolvemos la instancia
        if len(services) == 1:
            return self._resolve_service(services[0], service_type, scope)

        # Si hay múltiples servicios registrados, devolvemos una lista de instancias
        return [self._resolve_service(reg, service_type, scope) for reg in services]

    def _resolve_service(
        self,
        registration: ServiceRegistration,
        service_type: Type,
        scope: Optional[Dict[Type, Any]],
    ) -> Any:
        """
        Resuelve la instancia de un servicio según su ciclo de vida.
        """
        lifetime = registration.lifetime
        factory = registration.factory

        if lifetime == ServiceLifetime.SINGLETON:
            # Singleton: se reutiliza la misma instancia
            if service_type not in self._singletons:
                self._singletons[service_type] = factory()
            return self._singletons[service_type]

        elif lifetime == ServiceLifetime.TRANSIENT:
            # Transient: cada vez que se solicita se crea una nueva instancia
            return factory()

        elif lifetime == ServiceLifetime.SCOPED:
            # Scoped: una instancia por "scope" (p. ej. por request)
            # Si scope es None, intenta obtenerlo del contexto
            if scope is None:
                scope = ScopeManager.get_current_scope()
            if scope is None:
                raise ValidationError(
                    "Scoped services requieren un scope explícito. "
                    "Asegúrate de que el método del controlador esté siendo ejecutado dentro de un scope."
                )
            if service_type not in scope:
                scope[service_type] = factory()
            return scope[service_type]

        else:
            raise ValidationError(f"Tipo de ciclo de vida desconocido: {lifetime}")

    def _create_instance(self, cls: Type) -> Any:
        """
        Crea una instancia de la clase 'cls' inyectando automáticamente
        sus dependencias en el constructor. (similar a C# con reflection)

        Este método es totalmente opcional.
        Si prefieres usar factorías lambda, no es necesario.
        """
        ctor = getattr(cls, "__init__")
        sig = inspect.signature(ctor)
        # Excluimos 'self' de los parámetros
        params = list(sig.parameters.values())[1:]

        args = []
        for p in params:
            if p.annotation == inspect._empty:
                raise ValidationError(
                    f"El parámetro '{p.name}' del constructor de '{cls.__name__}' "
                    "no tiene anotación de tipo para poder inyectar automáticamente."
                )

            # Detectamos si es un tipo genérico list[Something]
            origin = typing.get_origin(p.annotation)
            if origin == list:
                # Ejemplo: list[BaseOcrStrategy]
                item_type = typing.get_args(p.annotation)[0]
                dependency = self.get_service(item_type)
                # get_service(item_type) puede retornar una sola instancia o una lista
                # Normalizamos a una lista
                if not isinstance(dependency, list):
                    dependency = [dependency]
                args.append(dependency)
            else:
                # Si no es list, resolvemos normalmente
                dependency = self.get_service(p.annotation)
                args.append(dependency)

        # Creamos la instancia de la clase con los argumentos resueltos
        return cls(*args)

    # ----------------------------------------------------------------------
    # Shutdown: Dispose de los singletons que lo implementen
    # ----------------------------------------------------------------------
    async def shutdown(self):
        """
        Llama a dispose() en todos los singletons que implementen IDisposable.
        """
        for instance in self._singletons.values():
            if isinstance(instance, IDisposable):
                if hasattr(instance, "dispose") and callable(instance.dispose):
                    if asyncio.iscoroutinefunction(instance.dispose):
                        await instance.dispose()
                    else:
                        instance.dispose()
