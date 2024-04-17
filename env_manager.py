import os
from dotenv import load_dotenv
from logger import logger


## import all classes
from translation.utils import (
                        BhashiniTranslationClass,
                        GoogleCloudTranslationClass,
                        DhruvaTranslationClass,
                        TranslationClass
                    )
from storage.utils import (
                        AwsS3MainClass,
                        GoogleBucketClass,
                        OciBucketClass,
                        StorageClass
                    )
from llm.utils import (
                        BaseChatClient,
                        OpenAIChatClient,
                        AzureChatClient,
                        OllamaChatClient
                    )

class EnvironmentManager():
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
                                "gcp": GoogleBucketClass,
                                "aws": AwsS3MainClass
                            },
                            "env_key": "BUCKET_TYPE"
                        }
                    }

    def create_instance(self, env_key):
        env_var = self.indexes[env_key]["env_key"]
        type_value = os.getenv(env_var)
        logger.info(f"Init {env_key} class for: {type_value}")
        if type_value is not None:
            return self.indexes[env_key]["class"].get(type_value)()


env_class = EnvironmentManager()
# create instances of functions
logger.info(f"Initializing required classes for components")
ai_class: BaseChatClient = env_class.create_instance("llm")
translate_class: TranslationClass = env_class.create_instance("translate")
storage_class: StorageClass = env_class.create_instance("storage")
