# Azure Function Boot Example

A sample Azure Function application demonstrating the use of `azfunc_boot`, a Python extension library for Azure Functions that provides dependency injection capabilities and a structured approach to building serverless applications.

## Overview

This project showcases how to build Azure Functions using the `azfunc_boot` framework, which extends the standard Azure Functions Python programming model with:

- **Dependency Injection (DI)**: Automatic dependency resolution and lifecycle management
- **Controller-based Architecture**: Organize Azure Functions triggers (HTTP, Queue, Timer, Blob, Event Hub, etc.) using controller classes
- **Flexible Architecture**: The framework is flexible and doesn't enforce a specific structure. You can organize your code however you prefer - with or without service layers, client abstractions, or any other patterns.

**Note**: This example demonstrates one possible architecture using service layers and disposable clients, but the framework allows you to structure your application in any way that fits your needs.

## Project Structure

This example project uses the following structure, but remember: **the framework is flexible and doesn't enforce any specific organization**. You can structure your code however you prefer.

```
azfunc-boot-example/
├── function_app.py              # Main application entry point
├── controllers/                 # Function trigger controllers (HTTP, Queue, Timer, etc.)
│   └── example_controller.py
├── services/                    # Business logic services (optional - example pattern)
│   └── example_service.py
├── clients/                     # External resource clients (optional - example pattern)
│   └── example_disposable_client.py
├── registries/                  # Dependency injection registries
│   ├── clients_registry.py      # Client registrations
│   └── services_registry.py     # Service registrations
├── host.json                    # Azure Functions host configuration
├── local.settings.json          # Local development settings
└── requirements.txt             # Python dependencies
```

**Important**: The `services/` and `clients/` folders are examples of common patterns, but you're free to:
- Put business logic directly in controllers
- Organize code in different folders (e.g., `handlers/`, `business/`, `domain/`, etc.)
- Use any architectural pattern that suits your project
- Skip service layers or client abstractions entirely if not needed

## Features

### Dependency Injection

The framework provides a dependency injection container that supports:

- **Singleton**: Single instance shared across all requests
- **Scoped**: One instance per function invocation
- **Transient**: New instance created each time (not shown in this example)

### Controller Pattern

Controllers extend `BaseController` and can handle any type of Azure Functions trigger, not just HTTP endpoints. The framework supports:

- **HTTP Triggers**: REST API endpoints
- **Queue Triggers**: Azure Storage Queue and Service Bus Queue messages
- **Timer Triggers**: Scheduled functions (cron jobs)
- **Blob Triggers**: Azure Blob Storage events
- **Event Hub Triggers**: Event Hub stream processing
- **Cosmos DB Triggers**: Database change feed processing
- **And more**: Any Azure Functions trigger type

Example HTTP controller:

```python
class ExampleController(BaseController):
    PATH = "example"
    
    def register_routes(self):
        self.bp.route(self.PATH, methods=["GET"])(self.example_method)
```

Controllers provide a consistent way to organize and structure your functions regardless of the trigger type, with full access to dependency injection and service layer patterns.

### Service Layer (Optional Pattern)

This example demonstrates a service layer pattern where business logic is separated into service classes. However, **this is optional** - you can put business logic directly in controllers or organize it however you prefer:

```python
# Using a service (optional pattern)
service: ExampleService = self.container.get_service(ExampleService)
result = await service.example_method(param)

# Or directly in controller (also valid)
# You can implement logic directly in controller methods if preferred
```

### Disposable Clients (Optional Pattern)

This example shows how to use disposable clients for resources that need cleanup. This pattern is **optional** - use it when you need proper resource management (HTTP clients, database connections, etc.), but you can also work with resources directly if preferred:

```python
class ExampleDisposableClient(IDisposable):
    async def dispose(self):
        # Cleanup logic here
        pass
```

The framework's dependency injection works with any class - you don't need to create a separate "client" layer unless it makes sense for your architecture.

### Framework Flexibility

`azfunc_boot` is designed to be flexible and non-prescriptive. Key points:

- **No enforced structure**: You can organize your code in any way that makes sense for your project
- **Optional patterns**: Service layers, client abstractions, and other patterns are optional - use them when they add value
- **Any class can be injected**: Register any class in the DI container, regardless of where it lives or what it's called
- **Custom organization**: Name your packages and folders however you prefer (e.g., `handlers/`, `business/`, `domain/`, `modules/`, etc.)
- **Mix and match**: You can combine different patterns or use none at all - the framework adapts to your needs

The only requirement is that controllers extend `BaseController` and registries extend `BaseServiceRegistry`. Everything else is up to you.

## Prerequisites

- Python 3.8 or higher
- Azure Functions Core Tools v4
- Azure subscription (for deployment)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd azfunc-boot-example
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - **Windows**: `venv\Scripts\activate`
   - **Linux/Mac**: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

Note: The `azfunc_boot` library is installed as an editable package. Make sure you have the `azfunc-boot` library available in your development environment.

## Configuration

### Local Development

The `local.settings.json` file contains local development settings. Make sure to configure:

- Azure Storage connection strings (for local development with Azurite)
- Application Insights connection string (optional)
- Any custom application settings

### Application Entry Point

The `function_app.py` file initializes the application:

```python
from azfunc_boot import create_app

app, container = create_app(
    controllers_package="controllers",
    registries_package="registries"
)
```

This creates the Azure Function app and dependency injection container, automatically discovering and registering:
- All controllers in the `controllers` package
- All registries in the `registries` package

**Flexibility Note**: While this example uses `controllers` and `registries` packages, you can name and organize these packages however you prefer. The framework will discover controllers and registries from whatever package names you specify.

## Running Locally

1. Start the Azure Functions runtime:
```bash
func start
```

2. The application will be available at `http://localhost:7071`

3. Test the endpoints:
   - Health check: `GET http://localhost:7071/api/health_check`
   - Example endpoint: `GET http://localhost:7071/api/example?param=test`

## API Endpoints

### Health Check
- **URL**: `/api/health_check`
- **Method**: `GET`
- **Auth Level**: Anonymous
- **Description**: Simple health check endpoint

### Example Endpoint
- **URL**: `/api/example`
- **Method**: `GET`
- **Query Parameters**: 
  - `param` (required): Example parameter
- **Description**: Demonstrates dependency injection and service layer usage

## Architecture

### Request Flow

The execution flow varies by trigger type, but follows a consistent pattern:

1. **Trigger Event** → Azure Functions runtime (HTTP request, queue message, timer, blob event, etc.)
2. **Controller Invocation** → Appropriate controller method is called
3. **Dependency Resolution** → Container resolves required services
4. **Service Execution** → Business logic in service layer
5. **Client Usage** → External resources accessed via disposable clients
6. **Response/Completion** → Trigger-specific response (HTTP response, queue completion, etc.)
7. **Cleanup** → Disposable clients are disposed after execution

### Dependency Graph

```
ExampleController
    └── ExampleService (scoped)
            └── ExampleDisposableClient (scoped)
                    └── Configuration (singleton)
```

## Adding New Features

### Creating a New Controller

Controllers can handle any Azure Functions trigger type. Here are examples for different triggers:

#### HTTP Trigger Controller

1. Create a new file in `controllers/`:
```python
from azfunc_boot import BaseController
import azure.functions as func

class MyHttpController(BaseController):
    PATH = "my-endpoint"
    
    def register_routes(self):
        self.bp.route(self.PATH, methods=["GET"])(self.my_method)
    
    async def my_method(self, req: func.HttpRequest) -> func.HttpResponse:
        # Your logic here
        return func.HttpResponse("OK", status_code=200)
```

#### Queue Trigger Controller

```python
from azfunc_boot import BaseController
import azure.functions as func

class MyQueueController(BaseController):
    def register_routes(self):
        # Register queue trigger
        self.bp.queue_trigger(arg_name="msg", queue_name="myqueue", connection="AzureWebJobsStorage")(self.process_message)
    
    async def process_message(self, msg: func.QueueMessage):
        # Process queue message
        service: MyService = self.container.get_service(MyService)
        await service.process(msg.get_body().decode('utf-8'))
```

#### Timer Trigger Controller

```python
from azfunc_boot import BaseController
import azure.functions as func

class MyTimerController(BaseController):
    def register_routes(self):
        # Register timer trigger (runs every 5 minutes)
        self.bp.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False)(self.timer_function)
    
    async def timer_function(self, timer: func.TimerRequest):
        # Scheduled task logic
        service: MyService = self.container.get_service(MyService)
        await service.scheduled_task()
```

2. The controller will be automatically discovered and registered regardless of trigger type.

### Creating a New Service (Optional)

If you want to use a service layer pattern (optional), you can:

1. Create a service class anywhere in your project (doesn't have to be in `services/`):
```python
class MyService:
    def __init__(self, dependency: SomeDependency):
        self.dependency = dependency
    
    async def my_method(self):
        # Business logic
        pass
```

2. Register it in any registry file:
```python
@register_service
def register_services(self):
    self.container.add_scoped(MyService)
```

**Note**: You can also put business logic directly in controllers or organize it however you prefer. The framework doesn't enforce any structure.

### Creating a Disposable Client (Optional)

If you need to manage resources that require cleanup, you can create a disposable client:

1. Create a class implementing `IDisposable` anywhere in your project:
```python
from azfunc_boot import IDisposable

class MyClient(IDisposable):
    async def dispose(self):
        # Cleanup logic
        pass
```

2. Register it in any registry file:
```python
@register_service
def register_clients(self):
    self.container.add_scoped(MyClient)
```

**Note**: This pattern is only needed if you have resources that require explicit cleanup. You can also work with resources directly without this abstraction.

## Deployment

### Deploy to Azure

1. Login to Azure:
```bash
az login
```

2. Create a Function App (if not exists):
```bash
az functionapp create --resource-group <resource-group> --consumption-plan-location <location> --runtime python --runtime-version 3.11 --functions-version 4 --name <app-name> --storage-account <storage-account>
```

3. Deploy the function:
```bash
func azure functionapp publish <app-name>
```

## Development Best Practices

1. **Flexible Architecture**: The framework doesn't enforce any specific structure. Organize your code in a way that makes sense for your project - with or without service layers, client abstractions, or other patterns.
2. **Service Registration**: Register any classes you want to inject in registry files. You can organize registries however you prefer (by feature, by layer, etc.).
3. **Lifecycle Management**: Use `IDisposable` only when you have resources that need explicit cleanup (HTTP clients, database connections, etc.). It's optional.
4. **Async Operations**: Use async/await for I/O operations to improve performance.
5. **Error Handling**: Implement proper error handling in your controllers and business logic.
6. **Logging**: Use the logging module for debugging and monitoring.

## Dependencies

- `azure-functions==1.24.0`: Azure Functions Python SDK
- `azfunc-boot`: Dependency injection framework for Azure Functions (editable install)
- `Werkzeug==3.1.5`: WSGI utilities
- `MarkupSafe==3.0.3`: String escaping library

## License

[Specify your license here]

## Contributing

[Add contribution guidelines if applicable]

## Support

For issues related to `azfunc_boot`, please refer to the library's documentation or repository.

For issues with this example project, please open an issue in this repository.
