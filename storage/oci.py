import os
from typing import Optional, Union
import boto3
from botocore.exceptions import ClientError
from logger import logger

from storage.base import BaseStorageClass


class OciBucketClass(BaseStorageClass):
    def __init__(self):
        super().__init__(boto3.client(
            's3',
            region_name=os.getenv("BUCKET_REGION_NAME"),
            aws_secret_access_key=os.getenv("BUCKET_SECRET_ACCESS_KEY"),
            aws_access_key_id=os.getenv("BUCKET_ACCESS_KEY_ID"),
            endpoint_url=os.getenv("BUCKET_ENDPOINT_URL")
        ))

    def upload_to_storage(self, file_name: str, object_name: Optional[str] = None) -> bool:
        if object_name is None:
            object_name = os.path.basename(file_name)

        try:
            self.client.upload_file(file_name, self.bucket_name, object_name,
                                    ExtraArgs={'ACL': 'public-read', "ContentType": "audio/mpeg"})
            logger.info(f"File uploaded to OCI Object Storage bucket: {self.bucket_name}")
        except ClientError as e:
            logger.error(f"Exception uploading a file: {e}", exc_info=True)
            return False
        return True

    def generate_public_url(self, object_name: str):
        """
        Generates the full path to a file in OCI Object Storage.

        Args:
            file_name: The name of the file.

        Returns:
            The full path to the file.
        """
        try:
            oci_endpoint_url = os.getenv("BUCKET_ENDPOINT_URL")
            public_url = f"{oci_endpoint_url}{self.bucket_name}/{object_name}"
            return public_url, None
        except Exception as e:
            logger.error(f"Exception Preparing public URL: {e}", exc_info=True)
            return None, "Error while generating public URL"
    # Additional OCI-specific methods can be implemented here
