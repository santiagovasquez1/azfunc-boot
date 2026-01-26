# Azure Functions Boot

A powerful framework for building Azure Functions applications with built-in dependency injection and hexagonal architecture support.

## Features

- **Dependency Injection Container**: Full-featured DI container with three service lifetimes (Singleton, Transient, Scoped)
- **MVC Architecture**: Controller-based architecture with automatic route registration
- **Hexagonal Architecture Support**: Clean separation of concerns with service registries
- **Automatic Controller Discovery**: Automatically discovers and registers controllers from your package
- **Scope Management**: Automatic scope creation and disposal for scoped services
- **Async/Sync Support**: Seamless support for both async and synchronous methods
- **Type-Based Resolution**: Automatic dependency resolution using Python type annotations
- **IDisposable Pattern**: Built-in support for resource cleanup

## Installation

```bash
pip install azfunc-boot
```

## Quick Start

### 1. Create a Service Registry

```python
from azfunc_boot.registry.base_service_registry import BaseServiceRegistry, register_service
from azfunc_boot.di.dependency_injector import DependencyContainer

class MyServiceRegistry(BaseServiceRegistry):
    def __init__(self, container: DependencyContainer):
        self.container = container
        super().__init__()
    
    @register_service
    def register_user_service(self):
        self.container.add_scoped(IUserService, UserService)
    
    @register_service
    def register_repository(self):
        self.container.add_singleton(IUserRepository, UserRepository)
```

### 2. Create a Controller

```python
from azfunc_boot.mvc.base_controller import BaseController
from azfunc_boot.di.dependency_injector import DependencyContainer
from azure.functions import Blueprint, HttpRequest, HttpResponse

class UserController(BaseController):
    def __init__(self, container: DependencyContainer, bp: Blueprint):
        self.user_service = None  # Will be injected
        super().__init__(container, bp)
    
    def register_routes(self):
        @self.bp.route(route="users", methods=["GET"])
        async def get_users(req: HttpRequest) -> HttpResponse:
            # Dependency injection happens automatically
            user_service = self.container.get_service(IUserService)
            users = await user_service.get_all()
            return self._json_response({"users": users})
```

### 3. Bootstrap Your Application

```python
from azfunc_boot.di.dependency_injector import DependencyContainer
from azfunc_boot.mvc.controller_discovery import ControllerDiscovery
from azure.functions import Blueprint

# Create container and blueprint
container = DependencyContainer()
bp = Blueprint()

# Register services
registry = MyServiceRegistry(container)

# Discover and register controllers
ControllerDiscovery.create(container, bp, "your_package.controllers")

# Register functions
bp.register_functions()
```

## Service Lifetimes

### Singleton
A single instance is created and reused throughout the application lifetime.

```python
container.add_singleton(IService, ServiceImplementation)
```

### Transient
A new instance is created every time the service is requested.

```python
container.add_transient(IService, ServiceImplementation)
```

### Scoped
A new instance is created per scope (typically per HTTP request or function invocation).

```python
container.add_scoped(IService, ServiceImplementation)
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
# Get a single service
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
class MyController(BaseController):
    def __init__(self, container: DependencyContainer, bp: Blueprint):
        super().__init__(container, bp)
    
    def register_routes(self):
        # Register your routes here
        pass
```

### Automatic Scope Management

Controllers automatically create and dispose scoped services:

```python
@self.bp.route(route="users", methods=["POST"])
async def create_user(req: HttpRequest) -> HttpResponse:
    # A scope is automatically created for this request
    # Scoped services are automatically disposed after the request
    user_service = self.container.get_service(IUserService)
    # ... your code
```

### Supported Triggers

The framework supports all Azure Functions triggers:

- HTTP triggers (`@self.bp.route`)
- Timer triggers (`@self.bp.timer_trigger`)
- Blob triggers (`@self.bp.blob_trigger`)
- Service Bus triggers (`@self.bp.service_bus_queue_trigger`)
- And more...

## Service Registry Pattern

Use the `BaseServiceRegistry` to organize your service registrations:

```python
class AppServiceRegistry(BaseServiceRegistry):
    def __init__(self, container: DependencyContainer):
        self.container = container
        super().__init__()
    
    @register_service
    def register_database(self):
        self.container.add_singleton(IDatabase, Database)
    
    @register_service
    def register_repositories(self):
        self.container.add_scoped(IUserRepository, UserRepository)
        self.container.add_scoped(IOrderRepository, OrderRepository)
```

## Resource Cleanup

Implement `IDisposable` for services that need cleanup:

```python
from azfunc_boot.common.disposable import IDisposable

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

This framework is designed to support hexagonal architecture:

- **Controllers** (Adapters): Handle HTTP requests and Azure Functions triggers
- **Services** (Application Layer): Business logic and orchestration
- **Repositories** (Ports/Adapters): Data access abstraction
- **Domain Models** (Core): Business entities

## Examples

See the `examples/` directory for complete working examples.

## License

[Your License Here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
