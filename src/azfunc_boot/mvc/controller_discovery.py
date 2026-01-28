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
        Método estático para instanciar la clase ControllersRegistry.
        """
        return ControllerDiscovery(
            container=container, blueprint=blueprint, package=package
        )

    def _discover(self, package: str):
        """
        Descubre automáticamente las clases hijas de BaseController en el paquete especificado
        y las registra dinámicamente.
        """
        try:
            # Importar el paquete primero para obtener su __path__
            package_module = importlib.import_module(package)
            package_path = package_module.__path__
            package_prefix = package_module.__name__ + '.'
        except ImportError as e:
            logging.error(f"No se pudo importar el paquete {package}: {e}")
            # Fallback: intentar usar el string como ruta de directorio
            package_path = [package]
            package_prefix = ''
        
        for _, module_name, is_pkg in pkgutil.walk_packages(package_path, package_prefix):
            # Importa el módulo
            # Si package_prefix está vacío, module_name no incluye el prefijo
            if package_prefix:
                full_module_name = module_name  # Ya incluye el prefijo completo
            else:
                full_module_name = f"{package}.{module_name}"
            
            try:
                module = importlib.import_module(full_module_name)
            except ImportError as e:
                logging.error(f"No se pudo importar el módulo {full_module_name}: {e}")
                continue

            # Inspecciona las clases en el módulo
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseController) and obj is not BaseController:
                    # Registra la clase si no está ya registrada
                    if obj not in self.registered_controllers:
                        self.registered_controllers.append(obj)
                        logging.info(
                            f"Controlador descubierto y registrado: {obj.__name__}"
                        )

    def _register_all_controllers(self):
        """
        Instancia y registra todas las clases que heredan de BaseController.
        """
        for controller_cls in self.registered_controllers:
            instance = controller_cls(container=self.container, bp=self.blueprint)
            self.controllers_instances.append(instance)
            logging.info(
                f"Controller {controller_cls.__name__} instanciado y registrado."
            )
