import os
import boto3
from botocore.exceptions import ClientError
from google.cloud import storage

from logger import logger
from dotenv import load_dotenv

load_dotenv()

class StorageClass:
    def __init__(self, client_type):
        self.client = client_type
        self.bucket_name = os.environ["BUCKET_NAME"]

    def create_bucket(self):
        pass

    def upload_to_storage(self, file_name, object_name=None):
        pass

    def download_from_storage(self):
        pass

    def list_all_files(self):
        pass

    def generate_presigned_url(self):
        pass

    def generate_public_url(self, object_name):
        pass


class OciBucketClass(StorageClass):
    def __init__(self):
        super().__init__(boto3.client(
            's3',
            region_name=os.environ["BUCKET_REGION_NAME"],
            aws_secret_access_key=os.environ["BUCKET_SECRET_ACCESS_KEY"],
            aws_access_key_id=os.environ["BUCKET_ACCESS_KEY_ID"],
            endpoint_url=os.environ["BUCKET_ENDPOINT_URL"]
        ))

    def upload_to_storage(self, file_name, object_name=None):
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

    def generate_public_url(self, object_name):
        """
        Generates the full path to a file in OCI Object Storage.

        Args:
            file_name: The name of the file.

        Returns:
            The full path to the file.
        """
        try:
            oci_endpoint_url = os.environ["BUCKET_ENDPOINT_URL"]
            public_url = f"{oci_endpoint_url}{self.bucket_name}/{object_name}"
            return public_url, None
        except Exception as e:
            logger.error(f"Exception Preparing public URL: {e}", exc_info=True)
            return None, "Error while generating public URL"
    # Additional OCI-specific methods can be implemented here


class AwsS3MainClass(StorageClass):
    def __init__(self):
        super().__init__(boto3.client(
            's3',
            region_name=os.environ["BUCKET_REGION_NAME"],
            aws_secret_access_key=os.environ["BUCKET_SECRET_ACCESS_KEY"],
            aws_access_key_id=os.environ["BUCKET_ACCESS_KEY_ID"],
        ))

    def upload_to_storage(self, file_name, object_name=None):
        if object_name is None:
            object_name = os.path.basename(file_name)

        try:
            self.client.upload_file(file_name, self.bucket_name, object_name,
                                    ExtraArgs={'ACL': 'public-read', "ContentType": "audio/mpeg"})
            logger.info(f"File uploaded to AWS S3 bucket: {self.bucket_name}")
        except ClientError as e:
            logger.error(f"Exception uploading a file: {e}", exc_info=True)
            return False
        return True


    def generate_public_url(self, object_name):
        try:
            public_url = f'https://{self.bucket_name}.s3.amazonaws.com/{object_name}'
            return public_url, None
        except Exception as e:
            logger.error(f"Exception Preparing public URL: {e}", exc_info=True)
            return None, "Error while generating public URL"
    # Additional AWS-specific methods can be implemented here


class GoogleBucketClass(StorageClass):
    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GCP_CONFIG_PATH")
        super().__init__(storage.Client())

    def upload_to_storage(self, file_name, object_name=None):
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(file_name)
        blob.upload_from_filename(file_name)

        return True

    def generate_public_url(self, object_name):
        try:
            bucket = self.client.get_bucket(self.bucket_name)
            blob = bucket.blob(object_name)

            blob.acl.all().grant_read()
            public_url = blob.public_url

            return public_url,  None
        except Exception as e:
            logger.error(f"Exception Preparing public URL: {e}", exc_info=True)
            return None, "Error while generating public URL"
