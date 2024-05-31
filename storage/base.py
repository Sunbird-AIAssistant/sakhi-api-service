import os
from abc import ABC, abstractmethod
from typing import Optional, Union

class BaseStorageClass(ABC):
    def __init__(self, client_type):
        self.client = client_type
        self.bucket_name = os.environ["BUCKET_NAME"]

    def create_bucket(self):
        pass

    @abstractmethod
    def upload_to_storage(self, file_name: str, object_name: Optional[str] = None) -> bool:
        pass

    def download_from_storage(self):
        pass

    def list_all_files(self):
        pass

    def generate_presigned_url(self):
        pass

    @abstractmethod
    def generate_public_url(self, object_name: str):
        pass

