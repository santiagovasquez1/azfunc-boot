import asyncio
import logging
from typing import Optional, Callable, Tuple

import azure.functions as func

from azfunc_boot.di.dependency_injector import DependencyContainer
from azfunc_boot.registry.discovery import RegistryManager
from azfunc_boot.mvc.controller_discovery import ControllerDiscovery


async def shutdown_container(container: DependencyContainer) -> None:
    """
    Ejecuta el shutdown del contenedor, llamando a dispose() en todos los singletons.

    Args:
        container: Contenedor de dependencias a cerrar.
    """
    if container:
        try:
            await container.shutdown()
            logging.info("Container shutdown completed successfully")
        except Exception as e:
            logging.error(f"Error during container shutdown: {e}")


class AppFactory:
    """
    Factory para crear y configurar una Azure Function App con el framework.
    """

    def __init__(
        self,
        controllers_package: str = "controllers",
        registries_package: str = "registries",
        pre_setup_hook: Optional[Callable[[DependencyContainer], None]] = None,
        post_setup_hook: Optional[
            Callable[[func.FunctionApp, DependencyContainer], None]
        ] = None,
    ):
        """
        Args:
            controllers_package: Nombre del paquete donde buscar controllers (default: "controllers").
            registries_package: Nombre del paquete donde buscar registries (default: "registries").
            pre_setup_hook: Función opcional a ejecutar después de crear el container pero antes de registrar servicios.
            post_setup_hook: Función opcional a ejecutar después de registrar todo pero antes de retornar.
        """
        self.controllers_package = controllers_package
        self.registries_package = registries_package
        self.pre_setup_hook = pre_setup_hook
        self.post_setup_hook = post_setup_hook

    def create_app(self) -> Tuple[func.FunctionApp, DependencyContainer]:
        """
        Crea y configura la Azure Function App con todos los componentes del framework.

        Returns:
            Tupla con (FunctionApp, DependencyContainer).

        Raises:
            Exception: Si hay algún error durante la configuración.
        """
        logging.info("Setting up Azure Function App with framework")

        # 1. Crear FunctionApp y Blueprint
        app = func.FunctionApp()
        blueprint = func.Blueprint()

        # 2. Crear contenedor de dependencias
        container = DependencyContainer()

        # 3. Pre-setup hook (opcional) - útil para configuraciones específicas del proyecto
        if self.pre_setup_hook:
            try:
                self.pre_setup_hook(container)
            except Exception as e:
                logging.error(f"Error in pre_setup_hook: {e}")
                raise

        # 4. Descubrir y registrar servicios desde registries
        try:
            RegistryManager.create_registry(container=container)
        except Exception as e:
            logging.error(f"Error discovering registries: {e}")
            raise

        # 5. Descubrir y registrar controllers
        try:
            ControllerDiscovery.create(
                container=container,
                blueprint=blueprint,
                package=self.controllers_package,
            )
        except Exception as e:
            logging.error(f"Error discovering controllers: {e}")
            raise

        # 6. Registrar blueprint en la app
        app.register_blueprint(blueprint)

        # 7. Post-setup hook (opcional) - útil para agregar rutas adicionales, middleware, etc.
        if self.post_setup_hook:
            try:
                self.post_setup_hook(app, container)
            except Exception as e:
                logging.error(f"Error in post_setup_hook: {e}")
                raise

        logging.info("Azure Function App setup completed successfully")
        return app, container


def create_app(
    controllers_package: str = "controllers",
    registries_package: str = "registries",
    pre_setup_hook: Optional[Callable[[DependencyContainer], None]] = None,
    post_setup_hook: Optional[
        Callable[[func.FunctionApp, DependencyContainer], None]
    ] = None,
) -> Tuple[func.FunctionApp, DependencyContainer]:
    """
    Función de conveniencia para crear una Azure Function App con el framework.

    Args:
        controllers_package: Nombre del paquete donde buscar controllers.
        registries_package: Nombre del paquete donde buscar registries.
        pre_setup_hook: Función opcional a ejecutar después de crear el container.
        post_setup_hook: Función opcional a ejecutar después de registrar todo.

    Returns:
        Tupla con (FunctionApp, DependencyContainer).

    Example:
        ```python
        app, container = create_app(
            controllers_package="controllers",
            registries_package="registries",
        )
        ```
    """
    factory = AppFactory(
        controllers_package=controllers_package,
        registries_package=registries_package,
        pre_setup_hook=pre_setup_hook,
        post_setup_hook=post_setup_hook,
    )
    return factory.create_app()
