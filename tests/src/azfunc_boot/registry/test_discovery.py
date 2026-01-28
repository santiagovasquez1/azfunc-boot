import logging
from unittest.mock import MagicMock, patch
from azfunc_boot.di.dependency_injector import DependencyContainer
from azfunc_boot.registry.base_service_registry import BaseServiceRegistry
from azfunc_boot.registry.discovery import RegistryManager


class MockServiceRegistry(BaseServiceRegistry):
    def __init__(self, container):
        super().__init__()
        self.container = container


class TestRegistryManager:
    def setup_method(self):
        self.container = MagicMock(spec=DependencyContainer)
        self.registry_manager = RegistryManager(self.container, "test_package")

    def test_create_registry(self):
        with patch.object(RegistryManager, "register_services") as mock_register:
            registry = RegistryManager.create_registry(self.container, "test_package")
            assert registry.container == self.container
            assert registry.registries_package == "test_package"
            assert registry.registered_services == []
            mock_register.assert_called_once()

    def test_register_services_with_valid_registry(self):
        mock_module = MagicMock()
        mock_module.__name__ = "test_module"

        with patch.object(self.registry_manager, "_load_base_package", return_value=["fake_path"]), patch.object(
            self.registry_manager, "_process_all_modules"
        ) as mock_process:
            self.registry_manager.register_services()
            mock_process.assert_called_once_with(["fake_path"])

    def test_create_registry_instance(self):
        with patch.object(logging, "info") as mock_info:
            self.registry_manager._create_registry_instance(MockServiceRegistry)

            assert len(self.registry_manager.registered_services) == 1
            assert isinstance(self.registry_manager.registered_services[0], MockServiceRegistry)
            assert self.registry_manager.registered_services[0].container == self.container
            mock_info.assert_called_with("Registered services from MockServiceRegistry")

    def test_register_services_invalid_package(self):
        with patch("azfunc_boot.registry.discovery.importlib.import_module") as mock_import, patch.object(
            logging, "warning"
        ) as mock_warning:
            mock_import.side_effect = ImportError("No module named 'invalid'")

            self.registry_manager.registries_package = "invalid"
            self.registry_manager.register_services()

            assert len(self.registry_manager.registered_services) == 0
            mock_warning.assert_called()

    def test_register_services_package_not_valid(self):
        mock_package = MagicMock()
        mock_package.__path__ = None

        with patch("azfunc_boot.registry.discovery.importlib.import_module") as mock_import, patch.object(
            logging, "warning"
        ) as mock_warning:
            mock_import.return_value = mock_package

            self.registry_manager.register_services()

            assert len(self.registry_manager.registered_services) == 0
            mock_warning.assert_called()

    def test_is_valid_registry_class(self):
        assert self.registry_manager._is_valid_registry_class(MockServiceRegistry) is True
        assert self.registry_manager._is_valid_registry_class(BaseServiceRegistry) is False

        class NotARegistry:
            pass

        assert self.registry_manager._is_valid_registry_class(NotARegistry) is False

    def test_process_module_import_error(self):
        with patch("azfunc_boot.registry.discovery.importlib.import_module") as mock_import, patch.object(
            logging, "error"
        ) as mock_error:
            mock_import.side_effect = ImportError("Cannot import")

            self.registry_manager._process_module("test_module")

            mock_error.assert_called()
            assert len(self.registry_manager.registered_services) == 0

    def test_process_all_modules(self):
        with patch("azfunc_boot.registry.discovery.pkgutil.iter_modules") as mock_iter, patch.object(
            self.registry_manager, "_process_module"
        ) as mock_process:
            mock_iter.return_value = [
                (None, "module1", False),
                (None, "module2", False),
                (None, "subpackage", True),  # Subpaquete, debe ser ignorado
            ]

            self.registry_manager._process_all_modules(["fake_path"])

            assert mock_process.call_count == 2
            mock_process.assert_any_call("module1")
            mock_process.assert_any_call("module2")

    def test_register_registry_classes(self):
        class AnotherRegistry(BaseServiceRegistry):
            def __init__(self, container):
                super().__init__()
                self.container = container

        class NotARegistry:
            pass

        mock_module = MagicMock()
        mock_module.MockServiceRegistry = MockServiceRegistry
        mock_module.AnotherRegistry = AnotherRegistry
        mock_module.NotARegistry = NotARegistry

        with patch("azfunc_boot.registry.discovery.inspect.getmembers") as mock_getmembers, patch.object(
            logging, "info"
        ) as mock_info:
            mock_getmembers.return_value = [
                ("MockServiceRegistry", MockServiceRegistry),
                ("AnotherRegistry", AnotherRegistry),
                ("NotARegistry", NotARegistry),
            ]

            self.registry_manager._register_registry_classes(mock_module)

            assert len(self.registry_manager.registered_services) == 2
            assert isinstance(self.registry_manager.registered_services[0], (MockServiceRegistry, AnotherRegistry))
            assert isinstance(self.registry_manager.registered_services[1], (MockServiceRegistry, AnotherRegistry))
            assert mock_info.call_count == 2
