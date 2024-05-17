import os
from typing import Any

from langchain.chat_models import ChatOllama

from llm.BaseChatClient import BaseChatClient


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
