import os
from openai import OpenAI
from openai import AzureOpenAI, RateLimitError, APIError, InternalServerError



class AzureAiClass():

    def __init__(self) -> None:

        self.azure_endpoint=os.environ["OPENAI_API_BASE"],
        self.api_key=os.environ["OPENAI_API_KEY"],
        self.api_version=os.environ["OPENAI_API_VERSION"]

    def get_client(self):
        client = AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
        return client

class OpenAiClass():

    def __init__(self) -> None:
        pass

    def get_client(self):
        client = OpenAI()
        return client