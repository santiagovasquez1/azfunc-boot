from typing import Callable, Any, Dict, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from azfunc_boot.mvc.scoped_blueprint import ScopedBlueprint


class TriggerDecorator:
    """
    Decorador que envuelve una función con scope antes de pasarla al trigger original.
    """

    def __init__(
        self,
        blueprint_wrapper: "ScopedBlueprint",
        original_trigger: Callable[..., Any],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        self._blueprint_wrapper = blueprint_wrapper
        self._original_trigger = original_trigger
        self._args = args
        self._kwargs = kwargs

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Envuelve la función con scope antes de pasarla al trigger original.

        Args:
            func: Función del controlador que será envuelta con scope.

        Returns:
            Función envuelta que será registrada en el trigger original.
        """
        wrapped_method = self._blueprint_wrapper._controller._wrap_with_scope(func)
        return self._original_trigger(*self._args, **self._kwargs)(wrapped_method)
