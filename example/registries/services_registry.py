from azfunc_boot import BaseServiceRegistry, DependencyContainer, register_service
from clients.example_disposable_client import ExampleDisposableClient
from services.example_service import ExampleService, IExampleService


class ServicesRegistry(BaseServiceRegistry):
    def __init__(self, container: DependencyContainer):
        self.container = container
        super().__init__()

    @register_service
    def register_services(self):
        self.container.add_scoped(
            IExampleService,
            lambda: ExampleService(self.container.get_service(ExampleDisposableClient)),
        )
