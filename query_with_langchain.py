import ast
import os
from typing import (
    Any,
    List,
    Tuple
)
import marqo
import tiktoken
from redis_util import read_messages_from_redis, store_messages_in_redis
from dotenv import load_dotenv
from fastapi import HTTPException
from langchain.docstore.document import Document
from langchain.vectorstores.marqo import Marqo
from openai import AzureOpenAI, RateLimitError, APIError, InternalServerError
import json
from config_util import get_config_value
from logger import logger

load_dotenv()
marqo_url = get_config_value("database", "MARQO_URL", None)
gpt_model = get_config_value("llm", "gpt_model", None)
max_messages = int(get_config_value("llm", "max_messages")) # Maximum number of messages to include in conversation history
marqoClient = marqo.Client(url=marqo_url)
client = AzureOpenAI(
    azure_endpoint=os.environ["OPENAI_API_BASE"],
    api_key=os.environ["OPENAI_API_KEY"],
    api_version=os.environ["OPENAI_API_VERSION"]
)


def querying_with_langchain_gpt3(index_id, query, audience_type):

    logger.debug(f"gpt_model: {gpt_model}")
    if gpt_model is None or gpt_model.strip() == "":
        raise HTTPException(status_code=422, detail="Please configure gpt_model under llm section in config file!")

    intent_response = check_bot_intent(query, audience_type)
    if intent_response:
        return intent_response, None, 200
    
    try:
        system_rules = ""
        activity_prompt_config = get_config_value("llm", "activity_prompt", None)
        logger.debug(f"activity_prompt_config: {activity_prompt_config}")
        if activity_prompt_config:
            activity_prompt_dict = ast.literal_eval(activity_prompt_config)
            system_rules = activity_prompt_dict.get(audience_type)

        search_index = Marqo(marqoClient, index_id, searchable_attributes=["text"])
        top_docs_to_fetch = get_config_value("database", "top_docs_to_fetch", None)
        documents = search_index.similarity_search_with_score(query, k=20)
        logger.debug(f"Marqo documents : {str(documents)}")
        min_score = get_config_value("database", "docs_min_score", None)
        filtered_document = get_score_filtered_documents(documents, float(min_score))
        filtered_document = filtered_document[:int(top_docs_to_fetch)]
        logger.info(f"Score filtered documents : {str(filtered_document)}")
        contexts = get_formatted_documents(filtered_document)
        if not documents or not contexts:
            return "I'm sorry, but I am not currently trained with relevant documents to provide a specific answer for your question.", None, 200

        system_rules = system_rules.format(contexts=contexts)
        logger.debug("==== System Rules ====")
        logger.debug(f"System Rules : {system_rules}")
        res = client.chat.completions.create(
            model=gpt_model,
            messages=[
                {"role": "system", "content": system_rules},
                {"role": "user", "content": query}
            ],
        )
        message = res.choices[0].message.model_dump()
        response = message["content"]
        logger.info({"label": "openai_response", "response": response})

        return response.strip(";"), None, 200
    except RateLimitError as e:
        error_message = f"OpenAI API request exceeded rate limit: {e}"
        status_code = 500
    except (APIError, InternalServerError):
        error_message = "Server is overloaded or unable to answer your request at the moment. Please try again later"
        status_code = 503
    except Exception as e:
        error_message = str(e.__context__) + " and " + e.__str__()
        status_code = 500

    return "", error_message, status_code

def conversation_retrieval_chain(index_id, query, session_id, context):
    logger.debug(f"gpt_model: {gpt_model}")
    if gpt_model is None or gpt_model.strip() == "":
        raise HTTPException(status_code=422, detail="Please configure gpt_model under llm section in config file!")

    intent_response = check_bot_intent(query, context)
    if intent_response:
        return intent_response, None, 200
    
    try:
        system_rules = ""
        activity_prompt_config = get_config_value("llm", "activity_prompt", None)
        logger.debug(f"activity_prompt_config: {activity_prompt_config}")
        activity_prompt_dict = ast.literal_eval(activity_prompt_config)
        system_rules = activity_prompt_dict.get(context)
        previous_messages  = read_messages_from_redis(session_id)
        formatted_messages = format_previous_messages(previous_messages)
        user_message = {"role":"user","content": query}
        intent_system_prompt = get_chat_intent_prompt()
        intent_payload = create_payload_by_message_count(user_message, intent_system_prompt, messages=formatted_messages, max_messages=max_messages)
        logger.debug(f"intent_payload :: {intent_payload}")
        search_intent = get_intent_query(intent_payload)
        logger.info(f"search_intent :: {search_intent}")
        search_index = Marqo(marqoClient, index_id, searchable_attributes=["text"])
        top_docs_to_fetch = get_config_value("database", "top_docs_to_fetch", None)
        documents = search_index.similarity_search_with_score(search_intent, k=20)
        logger.debug(f"Marqo documents : {str(documents)}")
        min_score = get_config_value("database", "docs_min_score", None)
        filtered_document = get_score_filtered_documents(documents, float(min_score))
        filtered_document = filtered_document[:int(top_docs_to_fetch)]
        logger.info(f"Score filtered documents : {str(filtered_document)}")
        contexts = get_formatted_documents(filtered_document)
        if not documents or not contexts:
            return "I'm sorry, but I am not currently trained with relevant documents to provide a specific answer for your question.", None, 200

        system_rules = system_rules.format(contexts=contexts)
        system_rules = {"role": "system", "content": system_rules}
        logger.debug(f"System Rules : {system_rules}")
        message_payload  = create_payload_by_message_count(user_message,system_rules,formatted_messages,max_messages=max_messages)
        logger.debug(f"message_payload :: {message_payload}")
        response = call_chat_model(message_payload)
        logger.info({"label": "openai_response", "response": response})
        assistant_message = format_assistant_message(response.strip(";"))
        messages = read_messages_from_redis(session_id)
        messages.extend([user_message,assistant_message])
        store_messages_in_redis(session_id, messages)
        return response.strip(";"), None, 200
    except RateLimitError as e:
        error_message = f"OpenAI API request exceeded rate limit: {e}"
        status_code = 500
    except (APIError, InternalServerError):
        error_message = "Server is overloaded or unable to answer your request at the moment. Please try again later"
        status_code = 503
    except Exception as e:
        error_message = str(e.__context__) + " and " + e.__str__()
        status_code = 500

    return "", error_message, status_code

def call_chat_model(messages: List[dict]) -> str:
    res = client.chat.completions.create(
            model=gpt_model,
            messages=messages,
            temperature=0.7
    )
    message = res.choices[0].message.model_dump()
    return message["content"]

def format_assistant_message(a):
    """Formats the assistant message
    Args:
        a (str, optional): assistant's reply.
    Returns:
        dict: formatted assistant message
    """
    return {'role': 'assistant', 'content': a.strip()}

def get_chat_intent_prompt():
    intent_prompt = get_config_value("llm", "chat_intent_prompt")
    return {'role': "system", 'content': intent_prompt }

def get_intent_query(messages=[]):
    """    
    Force function calling with openai.ChatCompletion.create()

    Args:
        - func (dict): function schema
        - messages (list): list of messages to complete the chat with
        - model (str): model to use for completion
    """
    function_info = {
        "name": "get_search_intent",
        "description": "This function takes the user's previous interactions and synthesizes it into a focused English search query that can be used to find the most relevant documents.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "description": "A precise English search query (typically 5-10 words long) generated from the user's previous interactions with the chatbot and/or the available documents.",
                    "type": "string"
                }
            },
            "required": ["query"]
        }
    }
    gpt_model = get_config_value("llm", "GPT_MODEL", "gpt-4")
    response = client.chat.completions.create(
        model=gpt_model,
        messages=messages,
        # functions=[function_info],
        # function_call= {"name": function_info.get("name")},
        stream=False,
        temperature=0.1,
    )
    # message = response.choices[0].message
    # function_call = message.function_call
    # arguments = json.loads(function_call.arguments)
    # print("response ====>", arguments)
    # return arguments
    message = response.choices[0].message.model_dump()
    return message["content"]

def count_tokens_str(doc, model="gpt-4"):
    """Count tokens in a string.

    Args:
        doc (str): String to count tokens for.
    Returns:
        int: number of tokens in the string

    """
    encoder = tiktoken.encoding_for_model(model)  # BPE encoder # type: ignore
    return len(encoder.encode(doc, disallowed_special=()))

def count_tokens(messages):
    """
    Counts tokens in a list of messages.
    Source: https://platform.openai.com/docs/guides/chat/introduction

    Args:
        messages (list): list of messages to count tokens for
    Returns:
        int: number of tokens in the list of messages
    """
    num_tokens = 0
    for message in messages:
        # every message follows <im_start>{role/name}\n{content}<im_end>\n
        num_tokens += 4
        for key, value in message.items():
            num_tokens += count_tokens_str(value)
            if key == "name":  # if there's a name, the role is omitted
                num_tokens += -1  # role is always required and always 1 token
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens

def create_payload_by_message_count(user_message, system_message, messages=[], max_messages=4):  # IMPORTANT
    """Get the message history for the conversation, limited by message count.

    Args:
        user_message (str): User message to add to the history.
        system_message (str): System message to add to the history.
        messages (list, optional): List of previous messages. Defaults to [].
        max_messages (int, optional): Maximum number of messages to include. Defaults to 4.

    Returns:
        list: Message history
    """
    message_history = [system_message]
    total_count =  max_messages * 2
    message_history.extend(messages[-total_count:])
    message_history.append(user_message)
    return message_history

def create_message_payload(user_message, system_message, messages=[], max_tokens=3000):  # IMPORTANT
    """Get the message history for the conversation.
    # NOTE: Include user message {role=user,content=user_q} in the message history

    Args:
        message_payload (dict, optional): Formatted RAG prompt to add (temporarily) to the conversation. Defaults to {}.
        max_tokens (int, optional): Maximum number of tokens to limit the message history to. Defaults to 3000.

    Returns:
        list: message history

    NOTE: 
        - System-Prompt is always added to the beginning of the message history
        - message_payload is added to the end of the message history (if provided)

    """
    message_history = []
    total_tokens = 0
    system_token_count = count_tokens([system_message])
    max_tokens -= system_token_count  # subtract the system prompt tokens
    if len(user_message) > 0:
        messages = messages + [user_message]
    else:
        messages = messages

    for message in reversed(messages):
        message_tokens = count_tokens([message])
        if total_tokens + message_tokens <= max_tokens:
            total_tokens += message_tokens
            # This inserts the message at the beginning of the list
            message_history.insert(0, message)
        else:
            break
    message_history.insert(0, system_message)
    return message_history

def format_previous_messages(messages):
    """
    Format previous messages for display
    """
    formatted_messages = []
    for message in messages:
        if message['role'] == 'user':
            formatted_messages.append({"role":"user", "content":f"Question: {message['content']}"})
        elif message['role'] == 'assistant':
            formatted_messages.append({"role":"assistant", "content":message['content']})
    return formatted_messages


def check_bot_intent(query: str, context: str):

    enable_bot_intent = get_config_value("llm", "enable_bot_intent", None)
    logger.debug(f"enable_bot_intent: {enable_bot_intent}")
    if enable_bot_intent.lower() == "false":
        return None

    intent_prompt = get_config_value("llm", "intent_prompt")
    res = client.chat.completions.create(
        model=gpt_model,
        messages=[{"role": "system", "content": intent_prompt}, {"role": "user", "content": query}]
    )
    intent_message = res.choices[0].message.model_dump()
    intent_response = intent_message["content"]
    logger.info({"label": "openai_intent_response", "intent_response": intent_response})

    if intent_response.lower() == "yes":
        bot_prompt_config = get_config_value("llm", "bot_prompt", "")
        logger.debug(f"bot_prompt_config: {bot_prompt_config}")
        bot_prompt_dict = ast.literal_eval(bot_prompt_config)
        system_rules = bot_prompt_dict.get(context)
        logger.debug(f"Intent System Rules : {system_rules}")
        res = client.chat.completions.create(
            model=gpt_model,
            messages=[
                {"role": "system", "content": system_rules},
                {"role": "user", "content": query}
            ],
        )
        message = res.choices[0].message.model_dump()
        response = message["content"]
        logger.info({"label": "openai_bot_response", "bot_response": response})
        return response
    else:
        return None
            
 

def get_score_filtered_documents(documents: List[Tuple[Document, Any]], min_score=0.0):
    return [(document, search_score) for document, search_score in documents if search_score > min_score]


def get_formatted_documents(documents: List[Tuple[Document, Any]]):
    sources = ""
    for document, _ in documents:
        sources += f"""
            > {document.page_content} \n Source: {document.metadata['file_name']},  page# {document.metadata['page_label']};\n\n
            """
    return sources


def generate_source_format(documents: List[Tuple[Document, Any]]) -> str:
    """Generates an answer format based on the given data.

    Args:
    data: A list of tuples, where each tuple contains a Document object and a
        score.

    Returns:
    A string containing the formatted answer, listing the source documents
    and their corresponding pages.
    """
    try:
        sources = {}
        for doc, _ in documents:
            file_name = doc.metadata['file_name']
            page_label = doc.metadata['page_label']
            sources.setdefault(file_name, []).append(page_label)

        answer_format = "\nSources:\n"
        counter = 1
        for file_name, pages in sources.items():
            answer_format += f"{counter}. {file_name} - (Pages: {', '.join(pages)})\n"
            counter += 1
        return answer_format
    except Exception as e:
        error_message = "Error while preparing source markdown"
        logger.error(f"{error_message}: {e}", exc_info=True)
        return ""

def concatenate_elements(arr):
    # Concatenate elements from index 1 to n
    separator = ': '
    result = separator.join(arr[1:])
    return result
