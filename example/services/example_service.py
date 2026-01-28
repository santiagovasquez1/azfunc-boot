from abc import ABC, abstractmethod
import asyncio
import logging
from clients.example_disposable_client import ExampleDisposableClient


class IExampleService(ABC):
    @abstractmethod
    async def example_method(self, param: str):
        pass

class ExampleService(IExampleService):
    def __init__(self, example_disposable_client: ExampleDisposableClient):
        self._logger = logging.getLogger(__name__)
        self.example_disposable_client = example_disposable_client

    async def example_method(self, param: str):
        await asyncio.sleep(0.5)
        return self.example_disposable_client.mock_method(param)
