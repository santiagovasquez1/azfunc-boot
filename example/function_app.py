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
