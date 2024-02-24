import os
import boto3
from botocore.exceptions import ClientError

from logger import logger
from dotenv import load_dotenv

load_dotenv()

class OciBucketClass():

    def __init__(self) -> None:
        self.s3_client = boto3.client(
            's3',
            region_name=os.environ["BUCKET_REGION_NAME"],
            aws_secret_access_key=os.environ["BUCKET_SECRET_ACCESS_KEY"],
            aws_access_key_id=os.environ["BUCKET_ACCESS_KEY_ID"],
            endpoint_url=os.environ["BUCKET_ENDPOINT_URL"]
        )

        self.bucket_name = os.environ["BUCKET_NAME"]


    def create_bucket(self):
        pass

    def upload_to_storage(self, file_name, object_name=None):
        """Upload a file to an OCI bucket

        :param file_name: File to upload
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = os.path.basename(file_name)

        try:
            self.s3_client.upload_file(file_name, self.bucket_name, object_name, ExtraArgs={'ACL': 'public-read', "ContentType": "audio/mpeg"})
            logger.info(f"File uploaded to OCI Object Storage bucket: {self.bucket_name}")
        except ClientError as e:
            logger.error(f"Exception uploading a file: {e}", exc_info=True)
            return False
        return True

    def download_from_storage(self, file_name, object_name=None):
        """Download a file to an OCI bucket

        :param file_name: The path to the file to download to
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was downloaded, else False
        """

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = os.path.basename(file_name)

        try:
            self.s3_client.download_file(self.bucket_name, object_name, file_name)
            logger.info(f"File downloaded from OCI Object Storage bucket: {self.bucket_name}")
        except ClientError as e:
            logger.error(f"Exception downloading a file: {e}", exc_info=True)
            return False
        return True

    def list_all_files(self):
        pass

    def generate_presigned_url(self, object_name, expiration=3600):
        """Generate a presigned URL to share an OCI object

        :param object_name: string
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Presigned URL as string. If error, returns None.
        """

        # Generate a presigned URL for the S3 object
        try:
            response = self.s3_client.generate_presigned_url('get_object',
                                                        Params={'Bucket': self.bucket_name,
                                                                'Key': object_name},
                                                        ExpiresIn=expiration)
        except ClientError as e:
            logger.error(f"Exception generating public URL: {e}", exc_info=True)
            return None

        # The response contains the presigned URL
        return response


    def generate_public_url(self, file_name: str):
        """
        Generates the full path to a file in OCI Object Storage.

        Args:
            file_name: The name of the file.

        Returns:
            The full path to the file.
        """
        try:
            bucket_endpoint_url = os.environ["BUCKET_ENDPOINT_URL"]
            public_url = f"{bucket_endpoint_url}{self.bucket_name}/{file_name}"
            return public_url, None
        except Exception as e:
            logger.error(f"Exception Preparing public URL: {e}", exc_info=True)
            return None, "Error while generating public URL"


class AwsS3MainClass():

    def __init__(self) -> None:
        self.s3_client = boto3.client(
            's3',
            region_name=os.environ["BUCKET_REGION_NAME"],
            aws_secret_access_key=os.environ["BUCKET_SECRET_ACCESS_KEY"],
            aws_access_key_id=os.environ["BUCKET_ACCESS_KEY_ID"],
        )

        self.bucket_name = os.environ["BUCKET_NAME"]

    def create_bucket(self):
        pass

    def upload_to_storage(self, file_name, object_name=None):
        """Upload a file to an aws s3 bucket

        :param file_name: File to upload
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = os.path.basename(file_name)

        try:
            self.s3_client.upload_file(file_name,
                                        self.bucket_name,
                                        object_name,
                                        ExtraArgs={
                                            'ACL': 'public-read',
                                            "ContentType": "audio/mpeg"
                                            }
                                        )
            logger.info(f"File uploaded to aws s3 bucket: {self.bucket_name}")
        except ClientError as e:
            logger.error(f"Exception uploading a file: {e}", exc_info=True)
            return False
        return True

    def download_from_storage(self, file_name, object_name=None):
        pass

    def list_all_files(self):
        pass

    def generate_presigned_url(self, object_name, expiration=3600):
        """Generate a presigned URL to share an OCI object

        :param object_name: string
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Presigned URL as string. If error, returns None.
        """

        # Generate a presigned URL for the S3 object
        try:
            response = self.s3_client.generate_presigned_url('get_object',
                                                        Params={'Bucket': self.bucket_name,
                                                                'Key': object_name},
                                                        ExpiresIn=expiration)
        except ClientError as e:
            logger.error(f"Exception generating public URL: {e}", exc_info=True)
            return None

        # The response contains the presigned URL
        return response


    def generate_public_url(self, file_name: str):
        """
        Generates the full path to a file in OCI Object Storage.

        Args:
            file_name: The name of the file.

        Returns:
            The full path to the file.
        """
        try:
            bucket_endpoint_url = os.environ["BUCKET_ENDPOINT_URL"]
            public_url = f"{bucket_endpoint_url}{self.bucket_name}/{file_name}"
            return public_url, None
        except Exception as e:
            logger.error(f"Exception Preparing public URL: {e}", exc_info=True)
            return None, "Error while generating public URL"



from google.cloud import storage
import os
from datetime import timedelta, datetime

class GoogleBucketClass():

    def __init__(self) -> None:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GCP_CONFIG_PATH")
        self.bucket_name = os.getenv("BUCKET_NAME")
        self.gcp_client = storage.Client()

    def create_bucket(self):
        pass

    def upload_to_storage(self, file_name, object_name=None):
        storage_client = self.gcp_client

        bucket = storage_client.bucket(self.bucket_name)

        blob = bucket.blob(file_name)
        blob.upload_from_filename(file_name)

        return True

    def download_from_storage(self):
        pass

    def list_all_files(self):
        pass

    def generate_presigned_url(self):
        pass

    def generate_public_url(self, object_name):
        client = self.gcp_client

        # Get the bucket and object
        bucket = client.get_bucket(self.bucket_name)
        blob = bucket.blob(object_name)

        # Set the object ACL to make it publicly accessible
        blob.acl.all().grant_read()

        # Generate a public URL for the object
        public_url = blob.public_url

        return public_url

