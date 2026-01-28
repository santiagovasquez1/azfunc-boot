# Azure Functions Boot

A powerful framework for building Azure Functions applications with built-in dependency injection and controller-based architecture.

**Created by:** [Santiago Vasquez Gomez](https://github.com/santiagovasquez1)

## Features

- **Dependency Injection Container**: Full-featured DI container with three service lifetimes (Singleton, Transient, Scoped)
- **Controller-based Architecture**: Organize Azure Functions triggers (HTTP, Queue, Timer, Blob, etc.) using controller classes
- **Automatic Discovery**: Automatically discovers and registers controllers and service registries
- **Scope Management**: Automatic scope creation and disposal for scoped services
- **Async/Sync Support**: Seamless support for both async and synchronous methods
- **Type-Based Resolution**: Automatic dependency resolution using Python type annotations
- **IDisposable Pattern**: Built-in support for resource cleanup
- **Flexible Architecture**: The framework is flexible and doesn't enforce a specific structure. You can organize your code however you prefer.

## Installation

```bash
pip install azfunc-boot
```

## Quick Start

### 1. Create a Service Registry

```python
from azfunc_boot import BaseServiceRegistry, DependencyContainer, register_service

class ServicesRegistry(BaseServiceRegistry):
    def __init__(self, container: DependencyContainer):
        self.container = container
        super().__init__()

    @register_service
    def register_services(self):
        # Simple registration
        self.container.add_scoped(ExampleService)
        
        # Registration with interface using lambda
        self.container.add_scoped(
            IExampleService,
            lambda: ExampleService(self.container.get_service(ExampleDisposableClient)),
        )
```

### 2. Create a Controller

```python
import logging
from azfunc_boot import BaseController, DependencyContainer
import azure.functions as func

from services.example_service import ExampleService


class ExampleController(BaseController):
    PATH = "example"

    def __init__(self, container: DependencyContainer, bp: func.Blueprint):
        super().__init__(container, bp)
        self._logger = logging.getLogger(__name__)

    def register_routes(self):
        self.bp.route(self.PATH, methods=["GET"])(self.example_method)

    async def example_method(self, req: func.HttpRequest) -> func.HttpResponse:
        self._logger.info("Example method called")
        param = req.params.get("param")
        if not param:
            return func.HttpResponse("Param is required", status_code=400)

        service: ExampleService = self.container.get_service(ExampleService)
        try:
            result = await service.example_method(param)
            return func.HttpResponse(result, status_code=200)
        except Exception as e:
            self._logger.error(f"Error in example_method: {e}")
            return func.HttpResponse(f"Error: {e}", status_code=500)
```

### 3. Bootstrap Your Application

```python
import logging
import azure.functions as func
from azfunc_boot import create_app

logging.basicConfig(level=logging.INFO, force=True)

# Create the application using the framework
app, container = create_app(
    controllers_package="controllers", registries_package="registries"
)


@app.route("health_check", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return func.HttpResponse("Healthy", status_code=200)
```

## Service Registration

The framework supports two ways to register services in your registry:

### Simple Registration

When the service class can be instantiated automatically by the container (all dependencies are registered services with type annotations):

```python
@register_service
def register_services(self):
    self.container.add_scoped(ExampleService)
    self.container.add_singleton(Configuration)
    self.container.add_transient(SomeService)
```

### Lambda Registration

Use a lambda function when:
- The service implements an interface/abstraction
- The constructor requires primitive types (strings, numbers, etc.)
- You need custom instantiation logic

**With interface:**
```python
@register_service
def register_services(self):
    self.container.add_scoped(
        IExampleService,
        lambda: ExampleService(self.container.get_service(ExampleDisposableClient)),
    )
```

**With primitive types:**
```python
@register_service
def register_services(self):
    self.container.add_scoped(
        ExampleService,
        lambda: ExampleService(
            connection_string="your-connection-string",
            timeout=30,
            client=self.container.get_service(ExampleDisposableClient)
        ),
    )
```

## Service Lifetimes

The framework supports three service lifetimes:

- **Singleton**: A single instance is created and reused throughout the application lifetime
- **Scoped**: A new instance is created per scope (typically per HTTP request or function invocation)
- **Transient**: A new instance is created every time the service is requested

All three lifetimes support both simple and lambda registration (see [Service Registration](#service-registration) above).

```python
# Singleton
container.add_singleton(ServiceClass)
container.add_singleton(IService, lambda: ServiceClass(...))

# Scoped
container.add_scoped(ServiceClass)
container.add_scoped(IService, lambda: ServiceClass(...))

# Transient
container.add_transient(ServiceClass)
container.add_transient(IService, lambda: ServiceClass(...))
```

## Dependency Injection

### Constructor Injection

The framework automatically resolves dependencies using type annotations:

```python
class UserService:
    def __init__(self, repository: IUserRepository, logger: ILogger):
        self.repository = repository
        self.logger = logger
```

### Manual Resolution

```python
# Get a service
service = container.get_service(IService)

# Get all implementations (if multiple registered)
services = container.get_service(IService)  # Returns list if multiple
```

### List Injection

Inject multiple implementations of the same interface:

```python
class Processor:
    def __init__(self, strategies: list[IStrategy]):
        self.strategies = strategies  # List of all registered IStrategy implementations
```

## Controllers

### Base Controller

All controllers must inherit from `BaseController`:

```python
import logging
from azfunc_boot import BaseController, DependencyContainer
import azure.functions as func

class MyController(BaseController):
    PATH = "my-endpoint"

    def __init__(self, container: DependencyContainer, bp: func.Blueprint):
        super().__init__(container, bp)
        self._logger = logging.getLogger(__name__)
    
    def register_routes(self):
        self.bp.route(self.PATH, methods=["GET"])(self.my_method)
    
    async def my_method(self, req: func.HttpRequest) -> func.HttpResponse:
        # Your route handler logic here
        return func.HttpResponse("OK", status_code=200)
```

### Automatic Scope Management

Controllers automatically create and dispose scoped services:

```python
async def create_user(self, req: func.HttpRequest) -> func.HttpResponse:
    # A scope is automatically created for this request
    # Scoped services are automatically disposed after the request
    user_service = self.container.get_service(IUserService)
    # ... your code
```

### Supported Triggers

The framework supports all Azure Functions triggers:

- HTTP triggers (`self.bp.route`)
- Timer triggers (`self.bp.timer_trigger`)
- Blob triggers (`self.bp.blob_trigger`)
- Service Bus triggers (`self.bp.service_bus_queue_trigger`)
- Event Hub triggers (`self.bp.event_hub_trigger`)
- Cosmos DB triggers (`self.bp.cosmos_db_trigger`)
- And more...

## Resource Cleanup

Implement `IDisposable` for services that need cleanup:

```python
from azfunc_boot import IDisposable

class DatabaseConnection(IDisposable):
    async def dispose(self):
        # Cleanup resources
        await self.connection.close()
```

Scoped services implementing `IDisposable` are automatically disposed when the scope ends.

## Error Handling

The framework provides custom exceptions:

- `NotFoundError`: Raised when a service is not registered
- `ValidationError`: Raised for validation failures

## Architecture

This framework is designed to be flexible and support various architectural patterns:

- **Controllers** (Adapters): Handle HTTP requests and Azure Functions triggers
- **Services** (Application Layer): Business logic and orchestration (optional)
- **Repositories** (Ports/Adapters): Data access abstraction (optional)
- **Domain Models** (Core): Business entities (optional)

**Note**: The framework doesn't enforce any specific structure. You can organize your code however you prefer - with or without service layers, client abstractions, or any other patterns. The only requirement is that controllers extend `BaseController` and registries extend `BaseServiceRegistry`.

## Examples

See the `example/` directory for complete working examples.

## License

MIT License

Copyright (c) 2026 Santiago Vasquez Gomez (https://github.com/santiagovasquez1)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
