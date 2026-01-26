from typing import Callable, Any, TYPE_CHECKING
from azfunc_boot.mvc.trigger_decorator import TriggerDecorator

if TYPE_CHECKING:
    from azfunc_boot.mvc.scoped_blueprint import ScopedBlueprint


class TriggerWrapper:
    """
    Wrapper para un trigger que intercepta la llamada y devuelve un decorador
    que envuelve la función con scope.
    """

    def __init__(
        self,
        blueprint_wrapper: "ScopedBlueprint",
        original_trigger: Callable[..., Any],
    ) -> None:
        self._blueprint_wrapper = blueprint_wrapper
        self._original_trigger = original_trigger

    def __call__(self, *args: Any, **kwargs: Any) -> TriggerDecorator:
        """
        Wrapper genérico para cualquier trigger. Intercepta la llamada
        al trigger y devuelve un decorador que envuelve la función con scope.

        Args:
            *args: Argumentos posicionales para el trigger.
            **kwargs: Argumentos con nombre para el trigger.

        Returns:
            TriggerDecorator que envuelve la función con scope.
        """
        return TriggerDecorator(
            self._blueprint_wrapper, self._original_trigger, args, kwargs
        )
