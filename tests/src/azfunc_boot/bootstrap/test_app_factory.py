import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from azfunc_boot.bootstrap.app_factory import AppFactory, create_app, shutdown_container
from azfunc_boot.di.dependency_injector import DependencyContainer


class TestAppFactory:
    def setup_method(self):
        self.factory = AppFactory()

    def test_init_with_defaults(self):
        assert self.factory.controllers_package == "controllers"
        assert self.factory.registries_package == "registries"
        assert self.factory.pre_setup_hook is None
        assert self.factory.post_setup_hook is None

    def test_init_with_custom_values(self):
        pre_hook = MagicMock()
        post_hook = MagicMock()

        factory = AppFactory(
            controllers_package="custom_controllers",
            registries_package="custom_registries",
            pre_setup_hook=pre_hook,
            post_setup_hook=post_hook,
        )

        assert factory.controllers_package == "custom_controllers"
        assert factory.registries_package == "custom_registries"
        assert factory.pre_setup_hook is pre_hook
        assert factory.post_setup_hook is post_hook

    def test_create_app(self):
        with patch("azfunc_boot.bootstrap.app_factory.RegistryManager.create_registry"), patch(
            "azfunc_boot.bootstrap.app_factory.ControllerDiscovery.create"
        ), patch("azure.functions.FunctionApp.register_blueprint"):
            app, container = self.factory.create_app()

            assert app is not None
            assert isinstance(container, DependencyContainer)

    def test_create_app_with_pre_setup_hook(self):
        pre_hook = MagicMock()

        factory = AppFactory(pre_setup_hook=pre_hook)

        with patch("azfunc_boot.bootstrap.app_factory.RegistryManager.create_registry"), patch(
            "azfunc_boot.bootstrap.app_factory.ControllerDiscovery.create"
        ), patch("azure.functions.FunctionApp.register_blueprint"):
            _, container = factory.create_app()

            pre_hook.assert_called_once_with(container)

    def test_create_app_with_post_setup_hook(self):
        post_hook = MagicMock()

        factory = AppFactory(post_setup_hook=post_hook)

        with patch("azfunc_boot.bootstrap.app_factory.RegistryManager.create_registry"), patch(
            "azfunc_boot.bootstrap.app_factory.ControllerDiscovery.create"
        ), patch("azure.functions.FunctionApp.register_blueprint"):
            app, container = factory.create_app()

            post_hook.assert_called_once_with(app, container)

    def test_create_app_pre_setup_hook_error(self):
        def failing_hook(container):
            raise ValueError("Hook error")

        factory = AppFactory(pre_setup_hook=failing_hook)

        with pytest.raises(ValueError, match="Hook error"):
            factory.create_app()

    def test_create_app_registry_error(self):
        with patch(
            "azfunc_boot.bootstrap.app_factory.RegistryManager.create_registry", side_effect=Exception("Registry error")
        ):
            with pytest.raises(Exception, match="Registry error"):
                self.factory.create_app()

    def test_create_app_controller_error(self):
        with patch("azfunc_boot.bootstrap.app_factory.RegistryManager.create_registry"), patch(
            "azfunc_boot.bootstrap.app_factory.ControllerDiscovery.create", side_effect=Exception("Controller error")
        ):
            with pytest.raises(Exception, match="Controller error"):
                self.factory.create_app()

    def test_create_app_function(self):
        with patch("azfunc_boot.bootstrap.app_factory.RegistryManager.create_registry"), patch(
            "azfunc_boot.bootstrap.app_factory.ControllerDiscovery.create"
        ), patch("azure.functions.FunctionApp.register_blueprint"):
            app, container = create_app()

            assert app is not None
            assert isinstance(container, DependencyContainer)

    def test_shutdown_container_success(self):
        container = MagicMock(spec=DependencyContainer)
        container.shutdown = AsyncMock()

        asyncio.run(shutdown_container(container))

        container.shutdown.assert_called_once()

    def test_shutdown_container_none(self):
        asyncio.run(shutdown_container(None))

    def test_shutdown_container_error(self):
        container = MagicMock(spec=DependencyContainer)

        async def failing_shutdown():
            raise ValueError("Shutdown error")

        container.shutdown = failing_shutdown

        asyncio.run(shutdown_container(container))
