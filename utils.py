import base64
import binascii
import uuid
from urllib.parse import urlparse
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Sequence,
)
from langchain.schema.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage
)

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

def convert_dict_to_message(_dict: Mapping[str, Any]) -> BaseMessage:
    """Convert a dictionary to a LangChain message.

    Args:
        _dict: The dictionary.

    Returns:
        The LangChain message.
    """
    role = _dict["role"]
    if role == "user":
        return HumanMessage(content=_dict["content"])
    elif role == "assistant":
        # Fix for azures
        # Also OpenAI returns None for tool invocations
        content = _dict.get("content", "") or ""
        additional_kwargs: Dict = {}
        if _dict.get("function_call"):
            additional_kwargs["function_call"] = dict(_dict["function_call"])
        if _dict.get("tool_calls"):
            additional_kwargs["tool_calls"] = _dict["tool_calls"]
        return AIMessage(content=content, additional_kwargs=additional_kwargs)
    elif role == "system":
        return SystemMessage(content=_dict["content"])
    elif role == "function":
        return FunctionMessage(content=_dict["content"], name=_dict["name"])
    elif role == "tool":
        return ToolMessage(content=_dict["content"], tool_call_id=_dict["tool_call_id"])
    else:
        return ChatMessage(content=_dict["content"], role=role)