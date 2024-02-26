from google.cloud import storage
import os
from datetime import timedelta, datetime

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"/home/ttpl-rt-107/Downloads/sunbird-tekdi-34a8f59ba660.json"

def create_bucket(bucket_name, storage_class='STANDARD', location='asia-south1'):
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    bucket.storage_class = storage_class

    bucket = storage_client.create_bucket(bucket, location=location)
    # for dual-location buckets add data_locations=[region_1, region_2]

    return f'Bucket {bucket.name} successfully created.'

print(create_bucket("aiassistenetpord"))