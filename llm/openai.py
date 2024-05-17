import os
from typing import Any

from langchain.chat_models import ChatOpenAI
from llm.base import BaseChatClient


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