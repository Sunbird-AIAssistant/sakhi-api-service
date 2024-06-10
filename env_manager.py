import os
from dotenv import load_dotenv
from logger import logger

from translation import (
    BaseTranslationClass,
    BhashiniTranslationClass,
    DhruvaTranslationClass,
    GoogleCloudTranslationClass
)
from storage import (
    BaseStorageClass,
    AwsS3BucketClass,
    GcpBucketClass,
    OciBucketClass
)
from llm import (
    BaseChatClient,
    AzureChatClient,
    OpenAIChatClient,
    OllamaChatClient
)
from utils import get_from_env_or_config

from vectorstores import (
    BaseVectorStore,
    MarqoVectorStore
)

disable_services = get_from_env_or_config("default", "disable_services", "").split(",")
logger.info(f"Disable Services: {disable_services}")


class EnvironmentManager:
    """
    Class for initializing functions respective to the env variable provided
    """

    def __init__(self):
        load_dotenv()
        self.indexes = {
            "llm": {
                "class": {
                    "openai": OpenAIChatClient,
                    "azure": AzureChatClient,
                    "ollama": OllamaChatClient
                },
                "env_key": "LLM_TYPE"
            },
            "translate": {
                "class": {
                    "bhashini": BhashiniTranslationClass,
                    "google": GoogleCloudTranslationClass,
                    "dhruva": DhruvaTranslationClass
                },
                "env_key": "TRANSLATION_TYPE"
            },
            "storage": {
                "class": {
                    "oci": OciBucketClass,
                    "gcp": GcpBucketClass,
                    "aws": AwsS3BucketClass
                },
                "env_key": "BUCKET_TYPE"
            },
            "vectorstore": {
                "class": {
                    "marqo": MarqoVectorStore
                },
                "env_key": "VECTOR_STORE_TYPE"
            }
        }

    def create_instance(self, env_key):
        env_var = self.indexes[env_key]["env_key"]
        type_value = os.getenv(env_var)

        if (type_value is None or type_value == "") and env_var not in disable_services:
            raise ValueError(
                f"Missing credentials. Please pass the `{env_var}` environment variable"
            )
        elif (type_value is None or type_value == "") and env_var in disable_services:
            return None
        else:
            logger.info(f"Init {env_key} class for: {type_value}")
            return self.indexes[env_key]["class"].get(type_value)()


env_class = EnvironmentManager()

# create instances of functions
logger.info(f"Initializing required classes for components")
llm_class: BaseChatClient = env_class.create_instance("llm")
translate_class: BaseTranslationClass = env_class.create_instance("translate")
storage_class: BaseStorageClass = env_class.create_instance("storage")
vectorstore_class: BaseVectorStore = env_class.create_instance("vectorstore")
