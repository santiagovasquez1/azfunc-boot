from typing import Callable, Any, Dict, TYPE_CHECKING
from azure.functions import Blueprint
from azfunc_boot.mvc.trigger_wrapper import TriggerWrapper

if TYPE_CHECKING:
    from azfunc_boot.mvc.base_controller import BaseController


class ScopedBlueprint:
    """
    Blueprint wrapper that intercepts calls to any trigger
    (route, timer_trigger, blob_trigger, service_bus_queue_trigger, etc.)
    and automatically wraps methods with scope. This allows controllers
    to use self.bp.trigger_name() normally without needing to
    change their code.
    """

    # Blueprint methods that are NOT triggers and should not be wrapped
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
        # Cache for already processed methods
        self._cached_methods: Dict[str, Callable[..., Any]] = {}

    def __getattr__(self, name: str) -> Any:
        """
        Intercepts access to any attribute/method of the blueprint.
        If it is a callable method that is a trigger, wraps it to automatically apply scope.

        Args:
            name: Name of the attribute/method to get.

        Returns:
            The wrapped attribute or method if it is a trigger, or the original attribute.
        """
        # If we already have it in cache, return it
        if name in self._cached_methods:
            return self._cached_methods[name]

        # Get the attribute from the original blueprint
        attr: Any = getattr(self._blueprint, name)

        # Verify if it is a trigger that should be wrapped:
        # 1. Must be callable
        # 2. Must not start with "_" (private methods)
        # 3. Must not be in the list of methods that are NOT triggers
        is_trigger: bool = (
            callable(attr)
            and not name.startswith("_")
            and name not in self._NON_TRIGGER_METHODS
        )

        if is_trigger:
            # Create a wrapper that intercepts the trigger call
            trigger_wrapper: Callable[..., Any] = self._create_trigger_wrapper(attr)
            # Cache the wrapped method
            self._cached_methods[name] = trigger_wrapper
            return trigger_wrapper

        # If it's not a trigger, return it as is (attributes, non-trigger methods, etc.)
        return attr

    def _create_trigger_wrapper(
        self, original_trigger: Callable[..., Any]
    ) -> Callable[..., Any]:
        """
        Creates a wrapper for a trigger that intercepts the call and returns a decorator
        that wraps the function with scope.

        Args:
            original_trigger: Original trigger method from the Blueprint.

        Returns:
            Wrapper function that returns a TriggerDecorator.
        """
        return TriggerWrapper(self, original_trigger)

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Handles attribute assignment. Private attributes are stored
        locally, others are delegated to the original blueprint.

        Args:
            name: Name of the attribute to assign.
            value: Value to assign.
        """
        # Handle our private attributes
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            # Delegate to the original blueprint
            setattr(self._blueprint, name, value)
