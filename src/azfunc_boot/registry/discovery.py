import importlib
import inspect
import logging
import pkgutil

from azfunc_boot.di.dependency_injector import DependencyContainer
from azfunc_boot.registry.base_service_registry import BaseServiceRegistry


class RegistryManager:
    """
    Manager that automatically discovers and executes all registries
    that inherit from BaseServiceRegistry in a specified package.
    """

    def __init__(self, container: DependencyContainer, registries_package: str):
        """
        Args:
            container: Dependency container where services will be registered.
            registries_package: Name of the package where to search for registries (e.g.: "registries").
        """
        self.container = container
        self.registries_package = registries_package
        self.registered_services = []

    @staticmethod
    def create_registry(
        container: DependencyContainer, registries_package: str = "registries"
    ) -> "RegistryManager":
        """
        Factory method to create and execute registry discovery.

        Args:
            container: Dependency container.
            registries_package: Package where to search for registries (default: "registries").

        Returns:
            RegistryManager with all discovered and executed registries.
        """
        registry = RegistryManager(container, registries_package)
        registry.register_services()
        return registry

    def register_services(self):
        """
        Automatically discovers all classes that inherit from BaseServiceRegistry
        in the specified package and instantiates them to execute their registrations.
        """
        package_path = self._load_base_package()
        if package_path is None:
            return

        self._process_all_modules(package_path)

    def _load_base_package(self):
        """
        Loads and validates the base package where registries are located.

        Returns:
            Package path if valid, None otherwise.
        """
        try:
            base_package = importlib.import_module(self.registries_package)
            package_path = getattr(base_package, "__path__", None)

            if package_path is None:
                logging.warning(
                    f"Package '{self.registries_package}' is not a valid package. "
                    "Skipping registry discovery."
                )
                return None

            return package_path
        except ImportError as e:
            logging.warning(
                f"Could not import package '{self.registries_package}': {e}. "
                "Skipping registry discovery."
            )
            return None

    def _process_all_modules(self, package_path):
        """
        Iterates over all modules in the package and processes them.

        Args:
            package_path: Package path where to search for modules.
        """
        for _, module_name, is_pkg in pkgutil.iter_modules(package_path):
            if not is_pkg:  # Only modules, not subpackages
                self._process_module(module_name)

    def _process_module(self, module_name: str):
        """
        Processes an individual module, importing it and registering its registry classes.

        Args:
            module_name: Name of the module to process.
        """
        try:
            full_module_name = f"{self.registries_package}.{module_name}"
            module = importlib.import_module(full_module_name)
            self._register_registry_classes(module)
        except ImportError as e:
            logging.error(
                f"Could not import module '{full_module_name}': {e}"
            )
        except Exception as e:
            logging.error(
                f"Error processing module '{module_name}': {e}"
            )

    def _register_registry_classes(self, module):
        """
        Searches and registers all classes that inherit from BaseServiceRegistry in a module.

        Args:
            module: Module where to search for registry classes.
        """
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if self._is_valid_registry_class(cls):
                self._create_registry_instance(cls)

    def _is_valid_registry_class(self, cls) -> bool:
        """
        Validates if a class is a valid registry.

        Args:
            cls: Class to validate.

        Returns:
            True if the class is a valid registry, False otherwise.
        """
        return (
            issubclass(cls, BaseServiceRegistry)
            and cls != BaseServiceRegistry
        )

    def _create_registry_instance(self, registry_class):
        """
        Creates a registry instance and adds it to the list of registered services.

        Args:
            registry_class: Registry class to instantiate.
        """
        instance = registry_class(self.container)
        self.registered_services.append(instance)
        logging.info(f"Registered services from {registry_class.__name__}")
