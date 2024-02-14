import base64
import binascii
import uuid
from urllib.parse import urlparse


def is_base64(base64_string):
    try:
        base64.b64decode(base64_string)
        return True
    except (binascii.Error, UnicodeDecodeError):
        # If an error occurs during decoding, the string is not Base64
        return False


def is_url(string):
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
    
def generate_temp_filename(ext, prefix = "temp"):
    return f"{prefix}_{uuid.uuid4()}.{ext}"

def prepare_redis_key(x_source, x_consumer_id, audience_type):
    key = "history"

    if x_source is not None:
        key += f"_{x_source}"

    if x_consumer_id is not None:
         key += f"_{x_consumer_id}"

    if audience_type is not None:
         key += f"_{audience_type}"

    return key