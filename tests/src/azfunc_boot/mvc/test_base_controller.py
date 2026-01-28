import asyncio

import pytest
from unittest.mock import MagicMock, patch

from azfunc_boot.common.disposable import IDisposable
from azfunc_boot.di.dependency_injector import DependencyContainer
from azfunc_boot.mvc.base_controller import BaseController
from azfunc_boot.mvc.scoped_blueprint import ScopedBlueprint
from azfunc_boot.di.scope import ScopeManager


class MockController(BaseController):
    def __init__(self, container, bp):
        self.register_routes_called = False
        super().__init__(container, bp)

    def register_routes(self):
        self.register_routes_called = True


class TestBaseController:
    def setup_method(self):
        self.container_mock = MagicMock(spec=DependencyContainer)
        self.bp_mock = MagicMock()
        self.controller = MockController(container=self.container_mock, bp=self.bp_mock)
        ScopeManager.clear_current_scope()

    def test_init(self):
        assert self.controller.container is self.container_mock
        assert isinstance(self.controller.bp, ScopedBlueprint)
        assert self.controller.bp._blueprint is self.bp_mock
        assert self.controller.register_routes_called is True

    def test_wrap_with_scope_async_method(self):
        async def async_method(arg1, arg2):
            await asyncio.sleep(0)
            return arg1 + arg2

        wrapped = self.controller._wrap_with_scope(async_method)
        result = asyncio.run(wrapped("test", "value"))

        assert result == "testvalue"

    def test_wrap_with_scope_sync_method(self):
        def sync_method(arg1, arg2):
            return arg1 + arg2

        wrapped = self.controller._wrap_with_scope(sync_method)
        result = wrapped("test", "value")

        assert result == "testvalue"

    def test_async_wrapper_handles_exception(self):
        async def async_method():
            raise ValueError("test error")

        wrapped = self.controller._wrap_with_scope(async_method)

        with pytest.raises(ValueError, match="test error"):
            asyncio.run(wrapped())

    def test_sync_wrapper_handles_exception(self):
        def sync_method():
            raise ValueError("test error")

        wrapped = self.controller._wrap_with_scope(sync_method)

        with pytest.raises(ValueError, match="test error"):
            wrapped()

    def test_dispose_scope_sync_calls_dispose_on_sync_disposable(self):
        disposable_mock = MagicMock(spec=IDisposable)
        disposable_mock.dispose = MagicMock()
        scope = {type(disposable_mock): disposable_mock}

        BaseController._dispose_scope_sync(scope)

        disposable_mock.dispose.assert_called_once()

    def test_dispose_scope_sync_with_empty_scope(self):
        scope = {}
        BaseController._dispose_scope_sync(scope)

    def test_dispose_scope_sync_with_multiple_disposables(self):
        disposable1 = MagicMock(spec=IDisposable)
        disposable1.dispose = MagicMock()
        disposable2 = MagicMock(spec=IDisposable)
        disposable2.dispose = MagicMock()
        scope = {type(disposable1): disposable1, type(disposable2): disposable2}

        BaseController._dispose_scope_sync(scope)

        disposable1.dispose.assert_called_once()
        disposable2.dispose.assert_called_once()

    def test_json_response(self):
        data = {"key": "value"}
        response = self.controller._json_response(data, 201)

        assert response.status_code == 201
        assert response.mimetype == "application/json"
        assert "key" in response.get_body().decode()

    def test_error_response(self):
        response = self.controller._error_response("Error message", 404)

        assert response.status_code == 404
        assert response.mimetype == "application/json"
        body = response.get_body().decode()
        assert "error" in body
        assert "Error message" in body

    def test_async_wrapper_creates_and_disposes_scope(self):
        async def async_method():
            await asyncio.sleep(0)
            scope = ScopeManager.get_current_scope()
            assert scope is not None
            return "result"

        wrapped = self.controller._wrap_with_scope(async_method)
        result = asyncio.run(wrapped())

        assert result == "result"
        assert ScopeManager.get_current_scope() is None

    def test_sync_wrapper_creates_and_disposes_scope(self):
        def sync_method():
            scope = ScopeManager.get_current_scope()
            assert scope is not None
            return "result"

        wrapped = self.controller._wrap_with_scope(sync_method)
        result = wrapped()

        assert result == "result"
        assert ScopeManager.get_current_scope() is None

    def test_dispose_scope_sync_with_async_disposable(self):
        async_disposable = MagicMock(spec=IDisposable)

        async def async_dispose():
            await asyncio.sleep(0)

        async_disposable.dispose = async_dispose
        scope = {type(async_disposable): async_disposable}

        with patch("azfunc_boot.mvc.base_controller.logging.warning") as mock_warning:
            BaseController._dispose_scope_sync(scope)
            mock_warning.assert_called()
