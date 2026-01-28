from typing import Callable, Any, TYPE_CHECKING
from azfunc_boot.mvc.trigger_decorator import TriggerDecorator

if TYPE_CHECKING:
    from azfunc_boot.mvc.scoped_blueprint import ScopedBlueprint


class TriggerWrapper:
    """
    Wrapper for a trigger that intercepts the call and returns a decorator
    that wraps the function with scope.
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
        Generic wrapper for any trigger. Intercepts the trigger call
        and returns a decorator that wraps the function with scope.

        Args:
            *args: Positional arguments for the trigger.
            **kwargs: Named arguments for the trigger.

        Returns:
            TriggerDecorator that wraps the function with scope.
        """
        return TriggerDecorator(
            self._blueprint_wrapper, self._original_trigger, args, kwargs
        )
