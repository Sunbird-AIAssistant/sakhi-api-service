import boto3
from botocore.exceptions import ClientError
import os


# Create S3 client for OCI object storage
s3_client = boto3.client(
 's3',
 region_name=os.environ["OCI_REGION_NAME"],
 aws_secret_access_key=os.environ["OCI_SECRET_ACCESS_KEY"],
 aws_access_key_id=os.environ["OCI_ACCESS_KEY_ID"],
 endpoint_url=os.environ["OCI_ENDPOINT_URL"]
)

# OCI Bucket Name
bucket_name = os.environ["OCI_BUCKET_NAME"]

def upload_file_object(file_name, object_name = None):
    """Upload a file to an OCI bucket

    :param file_name: File to upload    
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    try:
        s3_client.upload_file(file_name, bucket_name, object_name, ExtraArgs={'ACL': 'public-read'})
        print(f"File uploaded to OCI Object Storage bucket: {bucket_name}")
    except ClientError as e:
        print(f"Error uploading file: {e}")
        return False
    return True

def download_file_object(file_name, object_name = None):
    """Download a file to an OCI bucket

    :param file_name: The path to the file to download to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was downloaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    try:
        s3_client.download_file(bucket_name, object_name, file_name)
        print(f"File downloaded from OCI Object Storage bucket: {bucket_name}")
    except ClientError as e:
        print(f"Error downloading file: {e}")
        return False
    return True

def create_presigned_url(object_name, expiration=3600):
    """Generate a presigned URL to share an OCI object

    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        print(f"Error generating public URL: {e}")
        return None

    # The response contains the presigned URL
    return response

def give_public_url(file_name: str):
    """
    Generates the full path to a file in OCI Object Storage.

    Args:
        file_name: The name of the file.

    Returns:
        The full path to the file.
    """
    oci_endpoint_url = os.environ["OCI_ENDPOINT_URL"]
    public_url = f"{oci_endpoint_url}{bucket_name}/{file_name}"
    return public_url