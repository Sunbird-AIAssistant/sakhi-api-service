import os


class BaseStorageClass:
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

