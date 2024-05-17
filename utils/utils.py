import base64
import binascii
import uuid
from urllib.parse import urlparse
from typing import (
    Any,
    Dict,
    List,
    Sequence,
)
from langchain.schema.messages import BaseMessage
from langchain.adapters.openai import convert_dict_to_message


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

def prepare_redis_key(x_source, x_consumer_id, context):
    key = "history"

    if x_source is not None:
        key += f"_{x_source}"

    if x_consumer_id is not None:
         key += f"_{x_consumer_id}"

    if context is not None:
         key += f"_{context}"

    return key

def convert_chat_messages(messages: Sequence[Dict[str, Any]]) -> List[BaseMessage]:
    """Convert dictionaries representing common messages to LangChain format.

    Args:
        messages: List of dictionaries representing common messages

    Returns:
        List of LangChain BaseMessage objects.
    """
    return [convert_dict_to_message(m) for m in messages]