from abc import ABC, abstractmethod
from typing import Any, Optional
from langchain.chat_models.openai import ChatOpenAI
from langchain.chat_models.azure_openai import AzureChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.chat_models.ollama import ChatOllama
import os

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

class AzureChatClient(BaseChatClient):
    """
    This class provides a chat interface for interacting with AzuureOpenAI.
    """

    def get_client(self, model= os.getenv("AZURE_MODEL"), **kwargs: Any) -> AzureChatOpenAI:
        """
        This method creates and returns a AzureChatOpenAI instance.

        Args:
            model (str, optional): The AzureOpenAI model to use. Defaults to the value of the environment variable "AZURE_MODEL".
            **kwargs: Additional arguments to be passed to the AzureChatOpenAI constructor.

        Returns:
            An instance of the AzureChatOpenAI class.
        """
        return AzureChatOpenAI(
            model=model,
            **kwargs,
        )


class OpenAIChatClient(BaseChatClient):
    """
    This class provides a chat interface for interacting with ChatOpenAI.
    """
    def get_client(self, model=os.getenv("GPT_MODEL"), **kwargs: Any) -> ChatOpenAI:
        """
        This method creates and returns a ChatOpenAI instance.

        Args:
            model (str, optional): The OpenAI model to use. Defaults to the value of the environment variable "GPT_MODEL".
            **kwargs: Additional arguments to be passed to the ChatOpenAI constructor.

        Returns:
            An instance of the ChatOpenAI class.
        """
        return ChatOpenAI(model=model, **kwargs)


class OllamaChatClient(BaseChatClient):
    """
    This class provides a ollama chat interface.
    """
     
    ollama_api_endpoint: str

    def __init__(self) -> None:
        self.ollama_api_endpoint = os.getenv(
            "OLLAMA_API_ENDPOINT", "http://localhost:11434")

    def get_client(self, model=os.getenv("LLM_MODEL"), **kwargs: Any) -> ChatOllama:
        """
        This method creates and returns a ChatOllama instance.

        Args:
            model (str, optional): The LLM model to use. Defaults to the value of the environment variable "LLM_MODEL".
            **kwargs: Additional arguments to be passed to the ChatOllama constructor.

        Returns:
            An instance of the ChatOllama class.
        """
        return ChatOllama(
            base_url=self.ollama_api_endpoint,
            model=model,
            **kwargs
        )