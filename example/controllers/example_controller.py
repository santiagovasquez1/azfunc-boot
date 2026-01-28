import logging
from azfunc_boot import BaseController
from azfunc_boot import DependencyContainer
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
