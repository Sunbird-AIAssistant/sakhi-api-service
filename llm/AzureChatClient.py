import os
from typing import Any

from langchain.chat_models.azure_openai import AzureChatOpenAI

from llm.BaseChatClient import BaseChatClient


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
