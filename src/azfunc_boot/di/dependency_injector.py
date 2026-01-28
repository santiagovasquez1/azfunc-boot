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
    Structure to store information for each registered service.
    """

    def __init__(self, factory: Callable[[], Any], lifetime: str):
        self.factory = factory
        self.lifetime = lifetime


class DependencyContainer:
    def __init__(self):
        self._services: Dict[Type, List[ServiceRegistration]] = {}
        # _singletons stores instances of services in SINGLETON mode
        self._singletons: Dict[Type, Any] = {}

    def add_singleton(
        self,
        service_type: Type,
        implementation_factory: Optional[Callable[[], Any]] = None,
    ):
        """
        Registers a service with SINGLETON lifetime.
        If implementation_factory is None, it is assumed that service_type
        is both the "key" and the implementation.
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
        Registers a service with TRANSIENT lifetime.
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
        Registers a service with SCOPED lifetime.
        """
        self.add_service(
            service_type,
            implementation_factory or (lambda: self._create_instance(service_type)),
            lifetime=ServiceLifetime.SCOPED,
        )

    # ----------------------------------------------------------------------
    # Main generic method to register services
    # ----------------------------------------------------------------------
    def add_service(
        self,
        service_type: Type,
        implementation_factory: Callable[[], Any],
        lifetime: str = ServiceLifetime.SINGLETON,
    ):
        """
        Registers a service in the container.
        Allows multiple registrations for the same "key" (service_type).
        """
        if service_type not in self._services:
            self._services[service_type] = []

        self._services[service_type].append(
            ServiceRegistration(factory=implementation_factory, lifetime=lifetime)
        )

    # ----------------------------------------------------------------------
    # Service resolution
    # ----------------------------------------------------------------------
    def get_service(
        self, service_type: Type, scope: Optional[Dict[Type, Any]] = None
    ) -> Any:
        """
        Returns an instance of the first registered implementation for 'service_type'.
        If there are multiple registrations, returns a list of all implementations.

        If scope is None, attempts to get the scope from the current context (similar to .NET).
        """
        # If no explicit scope is provided, attempt to get it from the context
        if scope is None:
            scope = ScopeManager.get_current_scope()

        services = self._services.get(service_type)
        if not services or len(services) == 0:
            raise NotFoundError(
                f"Service has not been registered for {service_type.__name__}"
            )

        # If there is only one registered service, return the instance
        if len(services) == 1:
            return self._resolve_service(services[0], service_type, scope)

        # If there are multiple registered services, return a list of instances
        return [self._resolve_service(reg, service_type, scope) for reg in services]

    def _resolve_service(
        self,
        registration: ServiceRegistration,
        service_type: Type,
        scope: Optional[Dict[Type, Any]],
    ) -> Any:
        """
        Resolves a service instance according to its lifetime.
        """
        lifetime = registration.lifetime
        factory = registration.factory

        if lifetime == ServiceLifetime.SINGLETON:
            # Singleton: reuse the same instance
            if service_type not in self._singletons:
                self._singletons[service_type] = factory()
            return self._singletons[service_type]

        elif lifetime == ServiceLifetime.TRANSIENT:
            # Transient: create a new instance each time it is requested
            return factory()

        elif lifetime == ServiceLifetime.SCOPED:
            # Scoped: one instance per "scope" (e.g., per request)
            # If scope is None, attempt to get it from the context
            if scope is None:
                scope = ScopeManager.get_current_scope()
            if scope is None:
                raise ValidationError(
                    "Scoped services require an explicit scope. "
                    "Make sure the controller method is being executed within a scope."
                )
            if service_type not in scope:
                scope[service_type] = factory()
            return scope[service_type]

        else:
            raise ValidationError(f"Unknown lifetime type: {lifetime}")

    def _create_instance(self, cls: Type) -> Any:
        """
        Creates an instance of the class 'cls' automatically injecting
        its dependencies in the constructor. (similar to C# with reflection)

        This method is completely optional.
        If you prefer to use lambda factories, it is not necessary.
        """
        ctor = getattr(cls, "__init__")
        sig = inspect.signature(ctor)
        # Exclude 'self' from parameters
        params = list(sig.parameters.values())[1:]

        args = []
        for p in params:
            if p.annotation == inspect._empty:
                raise ValidationError(
                    f"Parameter '{p.name}' in constructor of '{cls.__name__}' "
                    "does not have a type annotation to enable automatic injection."
                )

            # Detect if it is a generic type list[Something]
            origin = typing.get_origin(p.annotation)
            if origin == list:
                # Example: list[BaseOcrStrategy]
                item_type = typing.get_args(p.annotation)[0]
                dependency = self.get_service(item_type)
                # get_service(item_type) can return a single instance or a list
                # Normalize to a list
                if not isinstance(dependency, list):
                    dependency = [dependency]
                args.append(dependency)
            else:
                # If it's not a list, resolve normally
                dependency = self.get_service(p.annotation)
                args.append(dependency)

        # Create the class instance with resolved arguments
        return cls(*args)

    # ----------------------------------------------------------------------
    # Shutdown: Dispose of singletons that implement it
    # ----------------------------------------------------------------------
    async def shutdown(self):
        """
        Calls dispose() on all singletons that implement IDisposable.
        """
        for instance in self._singletons.values():
            if isinstance(instance, IDisposable):
                if hasattr(instance, "dispose") and callable(instance.dispose):
                    if asyncio.iscoroutinefunction(instance.dispose):
                        await instance.dispose()
                    else:
                        instance.dispose()
