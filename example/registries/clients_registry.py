from azfunc_boot.registry.base_service_registry import (
    BaseServiceRegistry,
    register_service,
)
from azfunc_boot.di.dependency_injector import DependencyContainer
from azfunc_boot.config.configuration import Configuration

from clients.example_disposable_client import ExampleDisposableClient


class ClientsRegistry(BaseServiceRegistry):
    def __init__(self, container: DependencyContainer):
        self.container = container
        super().__init__()

    @register_service
    def register_clients(self):
        self.container.add_singleton(Configuration)
        self.container.add_scoped(ExampleDisposableClient)
