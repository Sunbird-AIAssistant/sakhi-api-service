import os
from typing import Optional, Union
from logger import logger
from google.cloud import storage

from storage.base import BaseStorageClass


class GcpBucketClass(BaseStorageClass):
    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GCP_CONFIG_PATH")
        super().__init__(storage.Client())

    def upload_to_storage(self, file_name: str, object_name: Optional[str] = None) -> bool:
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(file_name)
        blob.upload_from_filename(file_name)

        return True

    def generate_public_url(self, object_name: str):
        try:
            bucket = self.client.get_bucket(self.bucket_name)
            blob = bucket.blob(object_name)

            blob.acl.all().grant_read()
            public_url = blob.public_url

            return public_url,  None
        except Exception as e:
            logger.error(f"Exception Preparing public URL: {e}", exc_info=True)
            return None, "Error while generating public URL"