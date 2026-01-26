from typing import Callable, Any, Dict, TYPE_CHECKING
from azure.functions import Blueprint
from azfunc_boot.mvc.trigger_wrapper import TriggerWrapper

if TYPE_CHECKING:
    from azfunc_boot.mvc.base_controller import BaseController


class ScopedBlueprint:
    """
    Wrapper del Blueprint que intercepta las llamadas a cualquier trigger
    (route, timer_trigger, blob_trigger, service_bus_queue_trigger, etc.)
    y automáticamente envuelve los métodos con scope. Esto permite que los
    controladores usen self.bp.trigger_name() normalmente sin necesidad de
    cambios en su código.
    """

    # Métodos del Blueprint que NO son triggers y no deben ser envueltos
    _NON_TRIGGER_METHODS = {
        "register_blueprint",
        "register_functions",
        "get_functions",
        "validate_function_names",
        "function_name",
        "http_type",
        "retry",
    }

    def __init__(self, blueprint: Blueprint, controller: "BaseController") -> None:
        self._blueprint: Blueprint = blueprint
        self._controller: "BaseController" = controller
        # Cache para métodos ya procesados
        self._cached_methods: Dict[str, Callable[..., Any]] = {}

    def __getattr__(self, name: str) -> Any:
        """
        Intercepta el acceso a cualquier atributo/método del blueprint.
        Si es un método callable que es un trigger, lo envuelve para aplicar scope automáticamente.

        Args:
            name: Nombre del atributo/método a obtener.

        Returns:
            El atributo o método envuelto si es un trigger, o el atributo original.
        """
        # Si ya lo tenemos en cache, devolverlo
        if name in self._cached_methods:
            return self._cached_methods[name]

        # Obtener el atributo del blueprint original
        attr: Any = getattr(self._blueprint, name)

        # Verificar si es un trigger que debe ser envuelto:
        # 1. Debe ser callable
        # 2. No debe empezar con "_" (métodos privados)
        # 3. No debe estar en la lista de métodos que NO son triggers
        is_trigger: bool = (
            callable(attr)
            and not name.startswith("_")
            and name not in self._NON_TRIGGER_METHODS
        )

        if is_trigger:
            # Crear un wrapper que intercepte la llamada al trigger
            trigger_wrapper: Callable[..., Any] = self._create_trigger_wrapper(attr)
            # Cachear el método envuelto
            self._cached_methods[name] = trigger_wrapper
            return trigger_wrapper

        # Si no es un trigger, devolverlo tal cual (atributos, métodos no-trigger, etc.)
        return attr

    def _create_trigger_wrapper(
        self, original_trigger: Callable[..., Any]
    ) -> Callable[..., Any]:
        """
        Crea un wrapper para un trigger que intercepta la llamada y devuelve un decorador
        que envuelve la función con scope.

        Args:
            original_trigger: Método del trigger original del Blueprint.

        Returns:
            Función wrapper que devuelve un TriggerDecorator.
        """
        return TriggerWrapper(self, original_trigger)

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Maneja la asignación de atributos. Los atributos privados se guardan
        localmente, los demás se delegan al blueprint original.

        Args:
            name: Nombre del atributo a asignar.
            value: Valor a asignar.
        """
        # Maneja nuestros atributos privados
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            # Delega al blueprint original
            setattr(self._blueprint, name, value)
