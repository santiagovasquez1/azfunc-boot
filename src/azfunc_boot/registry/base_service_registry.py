import inspect
import logging
from abc import ABC
from typing import Callable

def register_service(func: Callable):
    func._is_register_service = True
    return func


class BaseServiceRegistry(ABC):
    def __init__(self):
        self.register_all_services()

    def register_all_services(self):
        for _, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if getattr(method, "_is_register_service", False):
                try:
                    method()
                    logging.info(f"Servicio registrado correctamente: {method.__name__}")
                except Exception as e:
                    logging.error(f"Error al registrar el servicio '{method.__name__}': {e}")
