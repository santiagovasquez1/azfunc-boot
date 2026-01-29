from unittest.mock import MagicMock

from azfunc_boot.mvc.trigger_decorator import TriggerDecorator


class TestTriggerDecorator:
    def setup_method(self):
        self.mock_blueprint_wrapper = MagicMock()
        self.mock_original_trigger = MagicMock()
        self.mock_controller = MagicMock()
        self.mock_wrapped_func = MagicMock()
        self.mock_trigger_decorator = MagicMock(return_value=self.mock_wrapped_func)

        self.mock_blueprint_wrapper._controller = self.mock_controller
        self.mock_controller._wrap_with_scope = MagicMock(return_value=self.mock_wrapped_func)
        self.mock_original_trigger.return_value = self.mock_trigger_decorator

    def test_init(self):
        decorator = TriggerDecorator(
            self.mock_blueprint_wrapper,
            self.mock_original_trigger,
            ("route_name",),
            {"auth_level": "anonymous"},
        )

        assert decorator._blueprint_wrapper is self.mock_blueprint_wrapper
        assert decorator._original_trigger is self.mock_original_trigger
        assert decorator._args == ("route_name",)
        assert decorator._kwargs == {"auth_level": "anonymous"}

    def test_call_wraps_function_with_scope(self):
        decorator = TriggerDecorator(
            self.mock_blueprint_wrapper,
            self.mock_original_trigger,
            ("route_name",),
            {"auth_level": "anonymous"},
        )

        def test_func():
            """Test function"""
            pass

        result = decorator(test_func)

        self.mock_controller._wrap_with_scope.assert_called_once_with(test_func)
        self.mock_original_trigger.assert_called_once_with("route_name", auth_level="anonymous")
        self.mock_trigger_decorator.assert_called_once_with(self.mock_wrapped_func)
        assert result is self.mock_wrapped_func
