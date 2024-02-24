from env_manager import storage_class

def upload_file_object(file_name, object_name=None):

    status = storage_class.upload_to_storage(file_name, object_name=None)
    return status

def give_public_url(file_name: str):

    url = storage_class.generate_public_url(file_name)

    return url, None