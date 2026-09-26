from abc import ABC, abstractmethod
from typing import Any

from app.connectors.base import BaseConnector


class BaseCollector(ABC):
    def __init__(self, connector: BaseConnector) -> None:
        self.connector = connector

    @abstractmethod
    async def collect(self) -> dict[str, Any]:
        ...
