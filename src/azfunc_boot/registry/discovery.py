import importlib
import inspect
import logging
import pkgutil

from azfunc_boot.di.dependency_injector import DependencyContainer
from azfunc_boot.registry.base_service_registry import BaseServiceRegistry


class RegistryManager:
    """
    Manager que descubre y ejecuta automáticamente todos los registries
    que heredan de BaseServiceRegistry en un paquete especificado.
    """

    def __init__(self, container: DependencyContainer, registries_package: str):
        """
        Args:
            container: Contenedor de dependencias donde se registrarán los servicios.
            registries_package: Nombre del paquete donde buscar registries (ej: "registries").
        """
        self.container = container
        self.registries_package = registries_package
        self.registered_services = []

    @staticmethod
    def create_registry(
        container: DependencyContainer, registries_package: str = "registries"
    ) -> "RegistryManager":
        """
        Factory method para crear y ejecutar el discovery de registries.

        Args:
            container: Contenedor de dependencias.
            registries_package: Paquete donde buscar registries (default: "registries").

        Returns:
            RegistryManager con todos los registries descubiertos y ejecutados.
        """
        registry = RegistryManager(container, registries_package)
        registry.register_services()
        return registry

    def register_services(self):
        """
        Descubre automáticamente todas las clases que heredan de BaseServiceRegistry
        en el paquete especificado y las instancia para ejecutar sus registros.
        """
        package_path = self._load_base_package()
        if package_path is None:
            return

        self._process_all_modules(package_path)

    def _load_base_package(self):
        """
        Carga y valida el paquete base donde se encuentran los registries.

        Returns:
            Path del paquete si es válido, None en caso contrario.
        """
        try:
            base_package = importlib.import_module(self.registries_package)
            package_path = getattr(base_package, "__path__", None)

            if package_path is None:
                logging.warning(
                    f"El paquete '{self.registries_package}' no es un paquete válido. "
                    "Skipping registry discovery."
                )
                return None

            return package_path
        except ImportError as e:
            logging.warning(
                f"No se pudo importar el paquete '{self.registries_package}': {e}. "
                "Skipping registry discovery."
            )
            return None

    def _process_all_modules(self, package_path):
        """
        Itera sobre todos los módulos en el paquete y los procesa.

        Args:
            package_path: Path del paquete donde buscar módulos.
        """
        for _, module_name, is_pkg in pkgutil.iter_modules(package_path):
            if not is_pkg:  # Solo módulos, no subpaquetes
                self._process_module(module_name)

    def _process_module(self, module_name: str):
        """
        Procesa un módulo individual, importándolo y registrando sus clases de registry.

        Args:
            module_name: Nombre del módulo a procesar.
        """
        try:
            full_module_name = f"{self.registries_package}.{module_name}"
            module = importlib.import_module(full_module_name)
            self._register_registry_classes(module)
        except ImportError as e:
            logging.error(
                f"No se pudo importar el módulo '{full_module_name}': {e}"
            )
        except Exception as e:
            logging.error(
                f"Error al procesar el módulo '{module_name}': {e}"
            )

    def _register_registry_classes(self, module):
        """
        Busca y registra todas las clases que heredan de BaseServiceRegistry en un módulo.

        Args:
            module: Módulo donde buscar clases de registry.
        """
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if self._is_valid_registry_class(cls):
                self._create_registry_instance(cls)

    def _is_valid_registry_class(self, cls) -> bool:
        """
        Valida si una clase es un registry válido.

        Args:
            cls: Clase a validar.

        Returns:
            True si la clase es un registry válido, False en caso contrario.
        """
        return (
            issubclass(cls, BaseServiceRegistry)
            and cls != BaseServiceRegistry
        )

    def _create_registry_instance(self, registry_class):
        """
        Crea una instancia de registry y la agrega a la lista de servicios registrados.

        Args:
            registry_class: Clase de registry a instanciar.
        """
        instance = registry_class(self.container)
        self.registered_services.append(instance)
        logging.info(f"Registered services from {registry_class.__name__}")
