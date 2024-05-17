from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain.chat_models.base import BaseChatModel


class BaseChatClient(ABC):
    """
    Abstract base class for Chat clients.

    This class defines the interface for creating different Chat clients.
    """

    @abstractmethod
    def get_client(self, model: Optional[str] = None, **kwargs: Any) -> BaseChatModel:
        """
        This method must be implemented by subclasses to create and return a specific chat client instance.

        Args:
          model: Name of the Chat model to use.
          kwargs: Additional keyword arguments to be passed to the specific Chat client constructor.

        Returns:
          An instance of a subclass of BaseChatModel representing the specific Chat client.
        """

        pass
