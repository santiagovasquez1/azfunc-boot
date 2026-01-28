import asyncio
from azfunc_boot.di.scope import ScopeManager
from azfunc_boot.common.disposable import IDisposable


class MockService:
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1


class MockDisposable(IDisposable):
    def __init__(self):
        self.value = 0
        self.disposed = False

    def dispose(self):
        self.disposed = True
        self.value = -1


class MockAsyncDisposable(IDisposable):
    def __init__(self):
        self.value = 0
        self.disposed = False

    async def dispose(self):
        self.disposed = True
        self.value = -1


class MockNonDisposable:
    def __init__(self):
        self.value = 0


class TestScopeManager:
    def setup_method(self):
        # Clear any existing scope before each test
        ScopeManager.clear_current_scope()

    def test_create_scope(self):
        scope = ScopeManager.create_scope()
        assert isinstance(scope, dict)
        assert len(scope) == 0

    def test_set_and_get_current_scope(self):
        scope = ScopeManager.create_scope()
        ScopeManager.set_current_scope(scope)
        retrieved_scope = ScopeManager.get_current_scope()
        assert retrieved_scope is scope

    def test_get_current_scope_returns_none_when_not_set(self):
        ScopeManager.clear_current_scope()
        scope = ScopeManager.get_current_scope()
        assert scope is None

    def test_clear_current_scope(self):
        scope = ScopeManager.create_scope()
        ScopeManager.set_current_scope(scope)
        assert ScopeManager.get_current_scope() is scope

        ScopeManager.clear_current_scope()
        assert ScopeManager.get_current_scope() is None

    def test_multiple_scopes_are_independent(self):
        scope1 = ScopeManager.create_scope()
        scope2 = ScopeManager.create_scope()

        ScopeManager.set_current_scope(scope1)
        assert ScopeManager.get_current_scope() is scope1

        ScopeManager.set_current_scope(scope2)
        assert ScopeManager.get_current_scope() is scope2
        assert ScopeManager.get_current_scope() is not scope1

    def test_scope_can_store_services(self):
        scope = ScopeManager.create_scope()
        service = MockService()
        scope[MockService] = service

        assert scope[MockService] is service
        assert len(scope) == 1

    def test_dispose_instance_with_sync_dispose(self):
        disposable = MockDisposable()
        assert not disposable.disposed
        assert disposable.value == 0

        asyncio.run(ScopeManager._dispose_instance(disposable))

        assert disposable.disposed
        assert disposable.value == -1

    def test_dispose_instance_with_async_dispose(self):
        disposable = MockAsyncDisposable()
        assert not disposable.disposed
        assert disposable.value == 0

        asyncio.run(ScopeManager._dispose_instance(disposable))

        assert disposable.disposed
        assert disposable.value == -1

    def test_dispose_instance_with_non_disposable(self):
        non_disposable = MockNonDisposable()
        # Should not raise an error
        asyncio.run(ScopeManager._dispose_instance(non_disposable))
        assert non_disposable.value == 0

    def test_dispose_instance_with_object_without_dispose_method(self):
        obj = object()
        # Should not raise an error
        asyncio.run(ScopeManager._dispose_instance(obj))

    def test_dispose_scope_with_single_disposable(self):
        scope = ScopeManager.create_scope()
        disposable = MockDisposable()
        scope[MockDisposable] = disposable

        assert not disposable.disposed

        asyncio.run(ScopeManager.dispose_scope(scope))

        assert disposable.disposed
        assert disposable.value == -1

    def test_dispose_scope_with_multiple_disposables(self):
        scope = ScopeManager.create_scope()
        disposable1 = MockDisposable()
        disposable2 = MockDisposable()
        scope[MockDisposable] = disposable1
        scope[dict] = disposable2  # Using different key type

        assert not disposable1.disposed
        assert not disposable2.disposed

        asyncio.run(ScopeManager.dispose_scope(scope))

        assert disposable1.disposed
        assert disposable2.disposed
        assert disposable1.value == -1
        assert disposable2.value == -1

    def test_dispose_scope_with_mixed_disposables_and_non_disposables(self):
        scope = ScopeManager.create_scope()
        disposable = MockDisposable()
        non_disposable = MockNonDisposable()
        scope[MockDisposable] = disposable
        scope[MockNonDisposable] = non_disposable

        assert not disposable.disposed
        assert non_disposable.value == 0

        asyncio.run(ScopeManager.dispose_scope(scope))

        assert disposable.disposed
        assert disposable.value == -1
        assert non_disposable.value == 0  # Should not be affected

    def test_dispose_scope_with_async_disposables(self):
        scope = ScopeManager.create_scope()
        async_disposable = MockAsyncDisposable()
        scope[MockAsyncDisposable] = async_disposable

        assert not async_disposable.disposed

        asyncio.run(ScopeManager.dispose_scope(scope))

        assert async_disposable.disposed
        assert async_disposable.value == -1

    def test_dispose_scope_with_mixed_async_and_sync_disposables(self):
        scope = ScopeManager.create_scope()
        async_disposable = MockAsyncDisposable()
        sync_disposable = MockDisposable()
        scope[MockAsyncDisposable] = async_disposable
        scope[MockDisposable] = sync_disposable

        assert not async_disposable.disposed
        assert not sync_disposable.disposed

        asyncio.run(ScopeManager.dispose_scope(scope))

        assert async_disposable.disposed
        assert sync_disposable.disposed
        assert async_disposable.value == -1
        assert sync_disposable.value == -1

    def test_dispose_scope_with_empty_scope(self):
        scope = ScopeManager.create_scope()
        # Should not raise an error
        asyncio.run(ScopeManager.dispose_scope(scope))

    def test_dispose_scope_preserves_scope_structure(self):
        scope = ScopeManager.create_scope()
        disposable = MockDisposable()
        non_disposable = MockNonDisposable()
        scope[MockDisposable] = disposable
        scope[MockNonDisposable] = non_disposable

        asyncio.run(ScopeManager.dispose_scope(scope))

        # Scope should still contain the services
        assert MockDisposable in scope
        assert MockNonDisposable in scope
        assert len(scope) == 2

    def test_dispose_instance_handles_object_with_dispose_but_not_callable(self):
        class ObjectWithNonCallableDispose:
            dispose = "not a method"

        obj = ObjectWithNonCallableDispose()
        # Should not raise an error
        asyncio.run(ScopeManager._dispose_instance(obj))

    def test_dispose_instance_handles_object_with_dispose_attribute_but_not_idisposable(
        self,
    ):
        class ObjectWithDisposeMethod:
            def dispose(self):
                self.disposed = True

        obj = ObjectWithDisposeMethod()
        # Should not be disposed by dispose_scope (not IDisposable)
        # But _dispose_instance should handle it if called directly
        asyncio.run(ScopeManager._dispose_instance(obj))
        assert hasattr(obj, "disposed")
        # Note: dispose_scope only disposes IDisposable instances
