import asyncio
import logging
from typing import Optional, Callable, Tuple

import azure.functions as func

from azfunc_boot.di.dependency_injector import DependencyContainer
from azfunc_boot.registry.discovery import RegistryManager
from azfunc_boot.mvc.controller_discovery import ControllerDiscovery


async def shutdown_container(container: DependencyContainer) -> None:
    """
    Executes the container shutdown, calling dispose() on all singletons.

    Args:
        container: Dependency container to close.
    """
    if container:
        try:
            await container.shutdown()
            logging.info("Container shutdown completed successfully")
        except Exception as e:
            logging.error(f"Error during container shutdown: {e}")


class AppFactory:
    """
    Factory to create and configure an Azure Function App with the framework.
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
            controllers_package: Name of the package where to search for controllers (default: "controllers").
            registries_package: Name of the package where to search for registries (default: "registries").
            pre_setup_hook: Optional function to execute after creating the container but before registering services.
            post_setup_hook: Optional function to execute after registering everything but before returning.
        """
        self.controllers_package = controllers_package
        self.registries_package = registries_package
        self.pre_setup_hook = pre_setup_hook
        self.post_setup_hook = post_setup_hook

    def create_app(self) -> Tuple[func.FunctionApp, DependencyContainer]:
        """
        Creates and configures the Azure Function App with all framework components.

        Returns:
            Tuple with (FunctionApp, DependencyContainer).

        Raises:
            Exception: If there is any error during configuration.
        """
        logging.info("Setting up Azure Function App with framework")

        # 1. Create FunctionApp and Blueprint
        app = func.FunctionApp()
        blueprint = func.Blueprint()

        # 2. Create dependency container
        container = DependencyContainer()

        # 3. Pre-setup hook (optional) - useful for project-specific configurations
        if self.pre_setup_hook:
            try:
                self.pre_setup_hook(container)
            except Exception as e:
                logging.error(f"Error in pre_setup_hook: {e}")
                raise

        # 4. Discover and register services from registries
        try:
            RegistryManager.create_registry(container=container)
        except Exception as e:
            logging.error(f"Error discovering registries: {e}")
            raise

        # 5. Discover and register controllers
        try:
            ControllerDiscovery.create(
                container=container,
                blueprint=blueprint,
                package=self.controllers_package,
            )
        except Exception as e:
            logging.error(f"Error discovering controllers: {e}")
            raise

        # 6. Register blueprint in the app
        app.register_blueprint(blueprint)

        # 7. Post-setup hook (optional) - useful for adding additional routes, middleware, etc.
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
    Convenience function to create an Azure Function App with the framework.

    Args:
        controllers_package: Name of the package where to search for controllers.
        registries_package: Name of the package where to search for registries.
        pre_setup_hook: Optional function to execute after creating the container.
        post_setup_hook: Optional function to execute after registering everything.

    Returns:
        Tuple with (FunctionApp, DependencyContainer).

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
