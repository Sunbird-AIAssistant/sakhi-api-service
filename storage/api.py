from env_manager import storage_class as storage

def upload_file_object(file_name, object_name=None):

    status = storage.upload_to_storage(file_name, object_name=None)
    return status

def give_public_url(file_name: str):

    url, errMsg = storage.generate_public_url(file_name)

    return url, errMsg