from typing import Any
from abc import ABC, abstractmethod

class Handler(ABC):

    _next_handler = None

    def set_next(self, handler: 'Handler') -> 'Handler':
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, request: Any):
        if self._next_handler:
            return self._next_handler.handle(request)
        return None