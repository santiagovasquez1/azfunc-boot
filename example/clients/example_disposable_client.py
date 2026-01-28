import asyncio
import logging
from azfunc_boot import IDisposable
from azfunc_boot import Configuration


class ExampleDisposableClient(IDisposable):
    def __init__(self, config: Configuration):
        self.config = config
        self._logger = logging.getLogger(__name__)

    def mock_method(self, param: str):
        return f"Example mock method with param: {param}"

    async def dispose(self):
        await asyncio.sleep(0.5)
        self._logger.info("Disposing ExampleDisposableClient instance")
