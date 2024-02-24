import os
from dotenv import load_dotenv


## import all classes
from translation.utils import (
                        BhashiniTranslationClass,
                        GoogleCloudTranslationClass
                    )
from storage.utils import (
                        AwsS3MainClass,
                        GoogleBucketClass,
                        OciBucketClass
                    )
from llm.utils import (
                        AzureAiClass,
                        OpenAiClass
                    )

load_dotenv()


indexes = {
    "gpt_type": {
        "openai": OpenAiClass,
        "azure": AzureAiClass
    },
    "translation": {
        "bhashini": BhashiniTranslationClass,
        "google": GoogleCloudTranslationClass,
    },
    "storage_type":{
        "oci": OciBucketClass,
        "gcp": GoogleBucketClass,
        "aws": AwsS3MainClass
    }
}

ai_type = os.getenv("OPENAI_TYPE")
ai_class = indexes["gpt_type"][ai_type]()
ai_client = ai_class.get_client()

translate_type = os.getenv("TRANSLATION_TYPE")
translate_class = indexes["translation"][translate_type]()

storage_type = os.getenv("BUCKET_TYPE")
storage_class = indexes["storage_type"][storage_type]()