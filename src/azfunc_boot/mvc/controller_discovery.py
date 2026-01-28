import logging
import inspect
import pkgutil
import importlib
from typing import List, Type
from azfunc_boot.di.dependency_injector import DependencyContainer
from azfunc_boot.mvc.base_controller import BaseController
from azure.functions import Blueprint


class ControllerDiscovery:
    def __init__(
        self, container: DependencyContainer, blueprint: Blueprint, package: str
    ):
        self.container = container
        self.blueprint = blueprint
        self.controllers_instances: List = []
        self.registered_controllers: List[Type] = []
        self._discover(package)
        self._register_all_controllers()

    @staticmethod
    def create(
        container: DependencyContainer, blueprint: Blueprint, package: str
    ) -> "ControllerDiscovery":
        """
        Static method to instantiate the ControllerDiscovery class.
        """
        return ControllerDiscovery(
            container=container, blueprint=blueprint, package=package
        )

    def _discover(self, package: str):
        """
        Automatically discovers classes that inherit from BaseController in the specified package
        and registers them dynamically.
        """
        package_path, package_prefix = self._get_package_info(package)
        
        for _, module_name, is_pkg in pkgutil.walk_packages(package_path, package_prefix):
            full_module_name = self._build_full_module_name(
                module_name, package, package_prefix
            )
            module = self._import_module_safely(full_module_name)
            
            if module:
                self._discover_controllers_in_module(module)

    def _get_package_info(self, package: str) -> tuple[list[str], str]:
        """
        Gets package path and prefix by importing the package.
        Falls back to using the package string as a directory path if import fails.
        
        Returns:
            tuple: (package_path, package_prefix)
        """
        try:
            package_module = importlib.import_module(package)
            package_path = package_module.__path__
            package_prefix = package_module.__name__ + '.'
        except ImportError as e:
            logging.error(f"Could not import package {package}: {e}")
            # Fallback: try to use the string as a directory path
            package_path = [package]
            package_prefix = ''
        
        return package_path, package_prefix

    def _build_full_module_name(
        self, module_name: str, package: str, package_prefix: str
    ) -> str:
        """
        Builds the full module name based on whether package_prefix is available.
        
        Args:
            module_name: The module name from pkgutil.walk_packages
            package: The original package name
            package_prefix: The package prefix (empty if package import failed)
        
        Returns:
            str: The full module name
        """
        if package_prefix:
            # Already includes the full prefix
            return module_name
        else:
            return f"{package}.{module_name}"

    def _import_module_safely(self, full_module_name: str):
        """
        Safely imports a module, logging errors and returning None on failure.
        
        Args:
            full_module_name: The full name of the module to import
        
        Returns:
            Module object if import succeeds, None otherwise
        """
        try:
            return importlib.import_module(full_module_name)
        except ImportError as e:
            logging.error(f"Could not import module {full_module_name}: {e}")
            return None

    def _discover_controllers_in_module(self, module):
        """
        Discovers and registers controller classes in a given module.
        
        Args:
            module: The module object to inspect for controllers
        """
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if self._is_controller_class(obj):
                self._register_controller_class(obj)

    def _is_controller_class(self, obj) -> bool:
        """
        Checks if an object is a controller class (subclass of BaseController but not BaseController itself).
        
        Args:
            obj: The object to check
        
        Returns:
            bool: True if obj is a controller class, False otherwise
        """
        return issubclass(obj, BaseController) and obj is not BaseController

    def _register_controller_class(self, controller_cls: Type):
        """
        Registers a controller class if it hasn't been registered yet.
        
        Args:
            controller_cls: The controller class to register
        """
        if controller_cls not in self.registered_controllers:
            self.registered_controllers.append(controller_cls)
            logging.info(f"Controller discovered and registered: {controller_cls.__name__}")

    def _register_all_controllers(self):
        """
        Instantiates and registers all classes that inherit from BaseController.
        """
        for controller_cls in self.registered_controllers:
            instance = controller_cls(container=self.container, bp=self.blueprint)
            self.controllers_instances.append(instance)
            logging.info(
                f"Controller {controller_cls.__name__} instantiated and registered."
            )
