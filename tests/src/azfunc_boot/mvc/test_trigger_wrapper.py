from unittest.mock import MagicMock

from azfunc_boot.mvc.trigger_decorator import TriggerDecorator
from azfunc_boot.mvc.trigger_wrapper import TriggerWrapper


class TestTriggerWrapper:
    def setup_method(self):
        self.mock_blueprint_wrapper = MagicMock()
        self.mock_original_trigger = MagicMock()

    def test_init(self):
        wrapper = TriggerWrapper(self.mock_blueprint_wrapper, self.mock_original_trigger)

        assert wrapper._blueprint_wrapper is self.mock_blueprint_wrapper
        assert wrapper._original_trigger is self.mock_original_trigger

    def test_call_returns_trigger_decorator(self):
        wrapper = TriggerWrapper(self.mock_blueprint_wrapper, self.mock_original_trigger)
        decorator = wrapper("route_name", auth_level="anonymous")

        assert isinstance(decorator, TriggerDecorator)
        assert decorator._blueprint_wrapper is self.mock_blueprint_wrapper
        assert decorator._original_trigger is self.mock_original_trigger
        assert decorator._args == ("route_name",)
        assert decorator._kwargs == {"auth_level": "anonymous"}
