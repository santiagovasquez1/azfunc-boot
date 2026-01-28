import asyncio
from unittest.mock import MagicMock

import pytest

from azfunc_boot.di.dependency_injector import DependencyContainer, ServiceLifetime
from azfunc_boot.common.disposable import IDisposable
from azfunc_boot.common.exceptions.not_found_error import NotFoundError
from azfunc_boot.common.exceptions.validation_error import ValidationError
from azfunc_boot.di.scope import ScopeManager


class MockService:
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1

    def get_value(self):
        return self.value


class TestDependencyInjector:
    def setup_method(self):
        self.container = DependencyContainer()
        # Clear any existing scope before each test
        ScopeManager.clear_current_scope()

    def test_add_transient(self):
        self.container.add_transient(MockService)
        assert MockService in self.container._services

    def test_add_singleton(self):
        self.container.add_singleton(MockService)
        assert MockService in self.container._services

    def test_add_service(self):
        self.container.add_service(MockService, lambda: MockService())
        assert MockService in self.container._services

    def test_get_service(self):
        self.container.add_transient(MockService)
        service = self.container.get_service(MockService)
        assert isinstance(service, MockService)

    def test_add_singleton_with_dependencies(self):
        class ClassA:
            def __init__(self):
                self.value = 0

        class ClassB:
            def __init__(self, a: ClassA):
                self.a = a

        self.container.add_singleton(ClassA)
        self.container.add_singleton(ClassB)

        b = self.container.get_service(ClassB)
        assert isinstance(b, ClassB)
        assert isinstance(b.a, ClassA)

    def test_add_singleton_with_factory(self):
        self.container.add_singleton(MockService, lambda: MockService())
        service = self.container.get_service(MockService)
        assert isinstance(service, MockService)

    def test_add_scoped(self):
        self.container.add_scoped(MockService)
        scope = {}
        service = self.container.get_service(MockService, scope)
        assert MockService in self.container._services
        assert isinstance(service, MockService)

    def test_singleton_reuses_instance(self):
        self.container.add_singleton(MockService)
        service1 = self.container.get_service(MockService)
        service2 = self.container.get_service(MockService)
        assert service1 is service2  # Same instance
        service1.increment()
        assert service1.get_value() == 1
        assert service2.get_value() == 1  # Same instance, same value

    def test_transient_creates_new_instance(self):
        self.container.add_transient(MockService)
        service1 = self.container.get_service(MockService)
        service2 = self.container.get_service(MockService)
        assert service1 is not service2  # Different instances
        service1.increment()
        assert service1.get_value() == 1
        assert service2.get_value() == 0  # Different instances, different values

    def test_scoped_reuses_instance_in_same_scope(self):
        self.container.add_scoped(MockService)
        scope = {}
        service1 = self.container.get_service(MockService, scope)
        service2 = self.container.get_service(MockService, scope)
        assert service1 is service2  # Same instance in same scope
        service1.increment()
        assert service1.get_value() == 1
        assert service2.get_value() == 1

    def test_scoped_creates_different_instance_in_different_scope(self):
        self.container.add_scoped(MockService)
        scope1 = {}
        scope2 = {}
        service1 = self.container.get_service(MockService, scope1)
        service2 = self.container.get_service(MockService, scope2)
        assert service1 is not service2  # Different instances in different scopes
        service1.increment()
        assert service1.get_value() == 1
        assert service2.get_value() == 0

    def test_get_service_raises_not_found_error(self):
        with pytest.raises(NotFoundError) as exc_info:
            self.container.get_service(MockService)
        assert "has not been registered" in str(exc_info.value)

    def test_get_service_with_multiple_registrations_returns_list(self):
        self.container.add_transient(MockService)
        self.container.add_transient(MockService)
        services = self.container.get_service(MockService)
        assert isinstance(services, list)
        assert len(services) == 2
        assert all(isinstance(s, MockService) for s in services)

    def test_scoped_service_requires_scope(self):
        self.container.add_scoped(MockService)
        with pytest.raises(ValidationError) as exc_info:
            self.container.get_service(MockService)
        assert "Scoped services require an explicit scope" in str(exc_info.value)

    def test_scoped_service_with_current_scope(self):
        self.container.add_scoped(MockService)
        scope = ScopeManager.create_scope()
        ScopeManager.set_current_scope(scope)
        try:
            service = self.container.get_service(MockService)
            assert isinstance(service, MockService)
        finally:
            ScopeManager.clear_current_scope()

    def test_create_instance_with_list_dependency(self):
        class BaseStrategy:
            pass

        class StrategyA(BaseStrategy):
            pass

        class StrategyB(BaseStrategy):
            pass

        class ServiceWithList:
            def __init__(self, strategies: list[BaseStrategy]):
                self.strategies = strategies

        self.container.add_transient(BaseStrategy, lambda: StrategyA())
        self.container.add_transient(BaseStrategy, lambda: StrategyB())
        self.container.add_transient(ServiceWithList)

        service = self.container.get_service(ServiceWithList)
        assert isinstance(service, ServiceWithList)
        assert len(service.strategies) == 2
        assert isinstance(service.strategies[0], StrategyA)
        assert isinstance(service.strategies[1], StrategyB)

    def test_create_instance_with_single_list_dependency(self):
        class BaseStrategy:
            pass

        class StrategyA(BaseStrategy):
            pass

        class ServiceWithList:
            def __init__(self, strategies: list[BaseStrategy]):
                self.strategies = strategies

        self.container.add_transient(BaseStrategy, lambda: StrategyA())
        self.container.add_transient(ServiceWithList)

        service = self.container.get_service(ServiceWithList)
        assert isinstance(service, ServiceWithList)
        assert len(service.strategies) == 1
        assert isinstance(service.strategies[0], StrategyA)

    def test_create_instance_without_type_annotation_raises_error(self):
        class ServiceWithoutAnnotation:
            def __init__(self, param):
                self.param = param

        self.container.add_transient(ServiceWithoutAnnotation)
        with pytest.raises(ValidationError) as exc_info:
            self.container.get_service(ServiceWithoutAnnotation)
        assert "does not have a type annotation" in str(exc_info.value)

    def test_add_service_with_custom_lifetime(self):
        self.container.add_service(MockService, lambda: MockService(), lifetime=ServiceLifetime.TRANSIENT)
        service1 = self.container.get_service(MockService)
        service2 = self.container.get_service(MockService)
        assert service1 is not service2

    def test_unknown_lifetime_raises_error(self):
        self.container.add_service(MockService, lambda: MockService(), lifetime="unknown")
        with pytest.raises(ValidationError) as exc_info:
            self.container.get_service(MockService)
        assert "Unknown lifetime type" in str(exc_info.value)

    def test_shutdown_with_async_dispose(self):
        class ClassA(IDisposable):
            def __init__(self):
                self.value = 0

            async def dispose(self):
                self.value = 1

        self.container.add_singleton(ClassA)
        service = self.container.get_service(ClassA)
        asyncio.run(self.container.shutdown())
        assert service.value == 1

    def test_shutdown_with_sync_dispose(self):
        class ClassA(IDisposable):
            def __init__(self):
                self.value = 0

            def dispose(self):
                self.value = 1

        self.container.add_singleton(ClassA)
        service = self.container.get_service(ClassA)
        asyncio.run(self.container.shutdown())
        assert service.value == 1

    def test_shutdown_with_multiple_disposables(self):
        class ClassA(IDisposable):
            def __init__(self):
                self.value = 0

            async def dispose(self):
                self.value = 1

        class ClassB(IDisposable):
            def __init__(self):
                self.value = 0

            def dispose(self):
                self.value = 2

        class ClassC:
            def __init__(self):
                self.value = 0

        self.container.add_singleton(ClassA)
        self.container.add_singleton(ClassB)
        self.container.add_singleton(ClassC)

        service_a = self.container.get_service(ClassA)
        service_b = self.container.get_service(ClassB)
        service_c = self.container.get_service(ClassC)

        asyncio.run(self.container.shutdown())

        assert service_a.value == 1
        assert service_b.value == 2
        assert service_c.value == 0  # Not disposable, should not change

    def test_add_transient_with_factory(self):
        factory_called = False

        def factory():
            nonlocal factory_called
            factory_called = True
            return MockService()

        self.container.add_transient(MockService, factory)
        service1 = self.container.get_service(MockService)
        service2 = self.container.get_service(MockService)
        assert factory_called
        assert service1 is not service2

    def test_add_scoped_with_factory(self):
        factory_called = 0

        def factory():
            nonlocal factory_called
            factory_called += 1
            return MockService()

        self.container.add_scoped(MockService, factory)
        scope = {}
        service1 = self.container.get_service(MockService, scope)
        service2 = self.container.get_service(MockService, scope)
        assert factory_called == 1  # Factory called only once per scope
        assert service1 is service2
