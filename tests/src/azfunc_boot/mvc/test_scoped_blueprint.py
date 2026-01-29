from unittest.mock import MagicMock

import pytest

from azfunc_boot.mvc.scoped_blueprint import ScopedBlueprint
from azfunc_boot.mvc.trigger_wrapper import TriggerWrapper


class TestScopedBlueprint:
    def setup_method(self):
        self.mock_blueprint = MagicMock()
        self.mock_controller = MagicMock()

    def test_init(self):
        scoped_bp = ScopedBlueprint(self.mock_blueprint, self.mock_controller)

        assert scoped_bp._blueprint is self.mock_blueprint
        assert scoped_bp._controller is self.mock_controller
        assert scoped_bp._cached_methods == {}

    def test_getattr_with_trigger_method(self):
        mock_trigger = MagicMock()
        self.mock_blueprint.route = mock_trigger

        scoped_bp = ScopedBlueprint(self.mock_blueprint, self.mock_controller)
        result = scoped_bp.route

        assert isinstance(result, TriggerWrapper)
        assert result._blueprint_wrapper is scoped_bp
        assert result._original_trigger is mock_trigger
        assert "route" in scoped_bp._cached_methods

    def test_getattr_with_non_trigger_method(self):
        mock_method = MagicMock()
        self.mock_blueprint.register_blueprint = mock_method

        scoped_bp = ScopedBlueprint(self.mock_blueprint, self.mock_controller)
        result = scoped_bp.register_blueprint

        assert result is mock_method
        assert "register_blueprint" not in scoped_bp._cached_methods

    def test_getattr_with_private_method(self):
        mock_private = MagicMock()
        self.mock_blueprint._private_method = mock_private

        scoped_bp = ScopedBlueprint(self.mock_blueprint, self.mock_controller)
        result = scoped_bp._private_method

        assert result is mock_private
        assert "_private_method" not in scoped_bp._cached_methods

    def test_getattr_with_non_callable_attribute(self):
        self.mock_blueprint.some_attribute = "test_value"

        scoped_bp = ScopedBlueprint(self.mock_blueprint, self.mock_controller)
        result = scoped_bp.some_attribute

        assert result == "test_value"
        assert "some_attribute" not in scoped_bp._cached_methods

    def test_getattr_caches_trigger_methods(self):
        mock_trigger = MagicMock()
        self.mock_blueprint.timer_trigger = mock_trigger

        scoped_bp = ScopedBlueprint(self.mock_blueprint, self.mock_controller)
        result1 = scoped_bp.timer_trigger
        result2 = scoped_bp.timer_trigger

        assert result1 is result2
        assert isinstance(result1, TriggerWrapper)
        assert "timer_trigger" in scoped_bp._cached_methods
        assert scoped_bp._cached_methods["timer_trigger"] is result1

    def test_setattr_with_private_attribute(self):
        scoped_bp = ScopedBlueprint(self.mock_blueprint, self.mock_controller)
        scoped_bp._private_attr = "test_value"

        assert scoped_bp._private_attr == "test_value"
        assert "_private_attr" in scoped_bp.__dict__
        assert scoped_bp.__dict__["_private_attr"] == "test_value"

    def test_setattr_with_public_attribute(self):
        scoped_bp = ScopedBlueprint(self.mock_blueprint, self.mock_controller)
        scoped_bp.public_attr = "test_value"

        assert hasattr(self.mock_blueprint, "public_attr")
        assert self.mock_blueprint.public_attr == "test_value"

    def test_getattr_with_different_triggers(self):
        mock_route = MagicMock()
        mock_timer = MagicMock()
        mock_blob = MagicMock()

        self.mock_blueprint.route = mock_route
        self.mock_blueprint.timer_trigger = mock_timer
        self.mock_blueprint.blob_trigger = mock_blob

        scoped_bp = ScopedBlueprint(self.mock_blueprint, self.mock_controller)
        route_wrapper = scoped_bp.route
        timer_wrapper = scoped_bp.timer_trigger
        blob_wrapper = scoped_bp.blob_trigger

        assert isinstance(route_wrapper, TriggerWrapper)
        assert isinstance(timer_wrapper, TriggerWrapper)
        assert isinstance(blob_wrapper, TriggerWrapper)
        assert route_wrapper is not timer_wrapper
        assert timer_wrapper is not blob_wrapper
        assert len(scoped_bp._cached_methods) == 3
