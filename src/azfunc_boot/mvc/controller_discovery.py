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
        try:
            # Import the package first to get its __path__
            package_module = importlib.import_module(package)
            package_path = package_module.__path__
            package_prefix = package_module.__name__ + '.'
        except ImportError as e:
            logging.error(f"Could not import package {package}: {e}")
            # Fallback: try to use the string as a directory path
            package_path = [package]
            package_prefix = ''
        
        for _, module_name, is_pkg in pkgutil.walk_packages(package_path, package_prefix):
            # Import the module
            # If package_prefix is empty, module_name does not include the prefix
            if package_prefix:
                full_module_name = module_name  # Already includes the full prefix
            else:
                full_module_name = f"{package}.{module_name}"
            
            try:
                module = importlib.import_module(full_module_name)
            except ImportError as e:
                logging.error(f"Could not import module {full_module_name}: {e}")
                continue

            # Inspect classes in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseController) and obj is not BaseController:
                    # Register the class if it's not already registered
                    if obj not in self.registered_controllers:
                        self.registered_controllers.append(obj)
                        logging.info(
                            f"Controller discovered and registered: {obj.__name__}"
                        )

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
