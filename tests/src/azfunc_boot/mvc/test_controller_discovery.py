import types
from unittest.mock import MagicMock, patch

from azfunc_boot.di.dependency_injector import DependencyContainer
from azfunc_boot.mvc.base_controller import BaseController
from azfunc_boot.mvc.controller_discovery import ControllerDiscovery


class MockController(BaseController):
    def register_routes(self):
        # Intentionally empty for testing
        pass


class MockController2(BaseController):
    def register_routes(self):
        # Intentionally empty for testing
        pass


class TestControllerDiscovery:
    def setup_method(self):
        self.container = MagicMock(spec=DependencyContainer)
        self.blueprint = MagicMock()

    def test_create(self):
        with patch.object(ControllerDiscovery, "_discover"), patch.object(
            ControllerDiscovery, "_register_all_controllers"
        ):
            discovery = ControllerDiscovery.create(self.container, self.blueprint, "test_package")

            assert discovery.container is self.container
            assert discovery.blueprint is self.blueprint
            assert discovery.controllers_instances == []
            assert discovery.registered_controllers == []

    def test_register_single_controller(self):
        with patch.object(ControllerDiscovery, "_discover"):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")
            discovery.registered_controllers.append(MockController)
            discovery._register_all_controllers()

            assert MockController in discovery.registered_controllers
            assert len(discovery.controllers_instances) == 1
            assert isinstance(discovery.controllers_instances[0], MockController)

    def test_register_multiple_controllers(self):
        with patch.object(ControllerDiscovery, "_discover"):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")
            discovery.registered_controllers.extend([MockController, MockController2])
            discovery._register_all_controllers()

            assert MockController in discovery.registered_controllers
            assert MockController2 in discovery.registered_controllers
            assert len(discovery.controllers_instances) == 2
            assert isinstance(discovery.controllers_instances[0], MockController)
            assert isinstance(discovery.controllers_instances[1], MockController2)

    def test_no_controllers_available(self):
        with patch.object(ControllerDiscovery, "_discover"):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")

            assert len(discovery.registered_controllers) == 0
            assert len(discovery.controllers_instances) == 0

    def test_discover_with_valid_controller(self):
        with patch.object(ControllerDiscovery, "_discover") as mock_discover, patch.object(
            ControllerDiscovery, "_register_all_controllers"
        ):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")
            discovery.registered_controllers.append(MockController)

            mock_discover.assert_called_once_with("test_package")
            assert MockController in discovery.registered_controllers

    def test_discover_import_error(self):
        with patch("azfunc_boot.mvc.controller_discovery.importlib.import_module") as mock_import, patch.object(
            ControllerDiscovery, "_register_all_controllers"
        ):
            mock_import.side_effect = ImportError("Cannot import package")

            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")

            assert len(discovery.registered_controllers) == 0

    def test_discover_module_import_error(self):
        mock_package = MagicMock()
        mock_package.__path__ = ["fake_path"]
        mock_package.__name__ = "test_package"

        with patch("azfunc_boot.mvc.controller_discovery.importlib.import_module") as mock_import, patch(
            "azfunc_boot.mvc.controller_discovery.pkgutil.walk_packages"
        ) as mock_walk, patch.object(ControllerDiscovery, "_register_all_controllers"):
            def import_side_effect(name):
                if name == "test_package":
                    return mock_package
                elif name == "test_package.test_module":
                    raise ImportError("Cannot import module")
                return MagicMock()

            mock_import.side_effect = import_side_effect
            mock_walk.return_value = [(None, "test_module", False)]

            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")

            assert len(discovery.registered_controllers) == 0

    def test_get_package_info_success(self):
        with patch.object(ControllerDiscovery, "_discover"), patch.object(
            ControllerDiscovery, "_register_all_controllers"
        ):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")
            mock_package = MagicMock()
            mock_package.__path__ = ["fake_path"]
            mock_package.__name__ = "test_package"

            with patch("azfunc_boot.mvc.controller_discovery.importlib.import_module", return_value=mock_package):
                path, prefix = discovery._get_package_info("test_package")

                assert path == ["fake_path"]
                assert prefix == "test_package."

    def test_get_package_info_import_error(self):
        with patch.object(ControllerDiscovery, "_discover"), patch.object(
            ControllerDiscovery, "_register_all_controllers"
        ):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")

            with patch("azfunc_boot.mvc.controller_discovery.importlib.import_module", side_effect=ImportError()):
                path, prefix = discovery._get_package_info("test_package")

                assert path == ["test_package"]
                assert prefix == ""

    def test_build_full_module_name_with_prefix(self):
        with patch.object(ControllerDiscovery, "_discover"), patch.object(
            ControllerDiscovery, "_register_all_controllers"
        ):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")
            result = discovery._build_full_module_name("test_package.module", "test_package", "test_package.")

            assert result == "test_package.module"

    def test_build_full_module_name_without_prefix(self):
        with patch.object(ControllerDiscovery, "_discover"), patch.object(
            ControllerDiscovery, "_register_all_controllers"
        ):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")
            result = discovery._build_full_module_name("module", "test_package", "")

            assert result == "test_package.module"

    def test_import_module_safely_success(self):
        with patch.object(ControllerDiscovery, "_discover"), patch.object(
            ControllerDiscovery, "_register_all_controllers"
        ):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")
            mock_module = MagicMock()

            with patch("azfunc_boot.mvc.controller_discovery.importlib.import_module", return_value=mock_module):
                result = discovery._import_module_safely("test_module")

                assert result is mock_module

    def test_import_module_safely_error(self):
        with patch.object(ControllerDiscovery, "_discover"), patch.object(
            ControllerDiscovery, "_register_all_controllers"
        ):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")

            with patch("azfunc_boot.mvc.controller_discovery.importlib.import_module", side_effect=ImportError()):
                result = discovery._import_module_safely("test_module")

                assert result is None

    def test_is_controller_class(self):
        with patch.object(ControllerDiscovery, "_discover"), patch.object(
            ControllerDiscovery, "_register_all_controllers"
        ):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")

            assert discovery._is_controller_class(MockController) is True
            assert discovery._is_controller_class(BaseController) is False

            class NotAController:
                pass

            assert discovery._is_controller_class(NotAController) is False

    def test_register_controller_class(self):
        with patch.object(ControllerDiscovery, "_discover"), patch.object(
            ControllerDiscovery, "_register_all_controllers"
        ):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")

            discovery._register_controller_class(MockController)

            assert MockController in discovery.registered_controllers
            assert len(discovery.registered_controllers) == 1

    def test_register_controller_class_duplicate(self):
        with patch.object(ControllerDiscovery, "_discover"), patch.object(
            ControllerDiscovery, "_register_all_controllers"
        ):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")

            discovery._register_controller_class(MockController)
            discovery._register_controller_class(MockController)

            assert len(discovery.registered_controllers) == 1

    def test_discover_controllers_in_module(self):
        with patch.object(ControllerDiscovery, "_discover"), patch.object(
            ControllerDiscovery, "_register_all_controllers"
        ):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")
            mock_module = types.ModuleType("test_module")
            mock_module.MockController = MockController

            class NotAController:
                pass

            mock_module.NotAController = NotAController

            discovery._discover_controllers_in_module(mock_module)

            assert MockController in discovery.registered_controllers
            assert NotAController not in discovery.registered_controllers

    def test_discover_full_flow(self):
        with patch.object(ControllerDiscovery, "_register_all_controllers"):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")
            mock_module = types.ModuleType("test_module")
            mock_module.MockController = MockController
            mock_module.MockController2 = MockController2

            with patch.object(discovery, "_get_package_info", return_value=(["fake_path"], "test_package.")), patch(
                "azfunc_boot.mvc.controller_discovery.pkgutil.walk_packages"
            ) as mock_walk, patch.object(discovery, "_import_module_safely", return_value=mock_module):
                mock_walk.return_value = [(None, "test_module", False)]

                discovery._discover("test_package")

                assert MockController in discovery.registered_controllers
                assert MockController2 in discovery.registered_controllers
                assert len(discovery.registered_controllers) == 2

    def test_discover_processes_multiple_modules(self):
        with patch.object(ControllerDiscovery, "_register_all_controllers"):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")
            mock_module1 = types.ModuleType("test_module1")
            mock_module1.MockController = MockController
            mock_module2 = types.ModuleType("test_module2")
            mock_module2.MockController2 = MockController2

            with patch.object(discovery, "_get_package_info", return_value=(["fake_path"], "test_package.")), patch(
                "azfunc_boot.mvc.controller_discovery.pkgutil.walk_packages"
            ) as mock_walk, patch.object(discovery, "_import_module_safely") as mock_import:
                mock_walk.return_value = [
                    (None, "test_module1", False),
                    (None, "test_module2", False),
                ]

                def import_side_effect(name):
                    if "test_module1" in name:
                        return mock_module1
                    elif "test_module2" in name:
                        return mock_module2
                    return None

                mock_import.side_effect = import_side_effect

                discovery._discover("test_package")

                assert mock_import.call_count == 2
                assert MockController in discovery.registered_controllers
                assert MockController2 in discovery.registered_controllers

    def test_discover_handles_none_module(self):
        with patch.object(ControllerDiscovery, "_register_all_controllers"):
            discovery = ControllerDiscovery(self.container, self.blueprint, "test_package")

            with patch.object(discovery, "_get_package_info", return_value=(["fake_path"], "test_package.")), patch(
                "azfunc_boot.mvc.controller_discovery.pkgutil.walk_packages"
            ) as mock_walk, patch.object(discovery, "_import_module_safely", return_value=None):
                mock_walk.return_value = [(None, "test_module", False)]

                discovery._discover("test_package")

                assert len(discovery.registered_controllers) == 0
