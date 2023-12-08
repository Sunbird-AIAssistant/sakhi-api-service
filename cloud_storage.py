from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv
import os


def cloud_authentication():
    load_dotenv()
    credentials = service_account.Credentials.from_service_account_file("gcp_credentials.json")
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.get_bucket(os.environ["BUCKET_NAME"])
    return bucket


def upload_file(folder_name, filename):
    bucket = cloud_authentication()
    full_folder_name = "generic_qa/" + str(folder_name) + "/"
    destination_blob_name = full_folder_name + filename
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(filename)


def read_given_file(uuid_number, file_name):
    bucket = cloud_authentication()
    folder_name = "generic_qa/" + uuid_number + "/" + file_name
    blobs = list(bucket.list_blobs(prefix=folder_name))
    if len(blobs):
        for blob in blobs:
            blob.download_to_filename(file_name)
    return len(blobs)


def read_files(uuid_number):
    bucket = cloud_authentication()
    folder_name = "generic_qa/" + uuid_number + "/"
    blobs = list(bucket.list_blobs(prefix=folder_name))
    blobs = [blob for blob in blobs if ("index.json" not in blob.name)
             and ("index.faiss" not in blob.name) and ("index.pkl" not in blob.name)]
    if len(blobs):
        destination_folder = uuid_number + "/"
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
        for blob in blobs:
            file_name = destination_folder + str(blob.name).replace(folder_name, "")
            blob.download_to_filename(file_name)
    return len(blobs)


def read_langchain_index_files(uuid_number):
    if (os.path.isfile(uuid_number + "/" + "index.faiss") and os.path.isfile(uuid_number + "/" + "index.faiss")): 
        return 2
    else:
        bucket = cloud_authentication()
        folder_name = "generic_qa/" + uuid_number + "/"
        blobs = list(bucket.list_blobs(prefix=folder_name))
        blobs = [blob for blob in blobs if ("index.faiss" in blob.name) or ("index.pkl" in blob.name)]
        print("Reading the blobs", blobs)
        if len(blobs) == 2:
            destination_folder = uuid_number + "/"
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)
            for blob in blobs:
                file_name = destination_folder + str(blob.name).replace(folder_name, "")
                print("Writing the blob to file", file_name)
                blob.download_to_filename(file_name)
        return len(blobs)


def give_public_url(filename):
    bucket = cloud_authentication()
    file_name = "generic_qa/output_audio_files/" + filename
    blobs = bucket.list_blobs(prefix=file_name)
    for blob in blobs:
        blob.make_public()
        return blob.public_url


def check_bucket_cors_policy():
    bucket = cloud_authentication()
    print(f"ID: {bucket.id}")
    print(f"Name: {bucket.name}")
    print(f"Cors: {bucket.cors}")
