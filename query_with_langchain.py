import ast
import os
from typing import (
    Any,
    List,
    Tuple
)
import marqo
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain.vectorstores.marqo import Marqo
from openai import AzureOpenAI, RateLimitError, APIError, InternalServerError

from config_util import get_config_value
from logger import logger

load_dotenv()
marqo_url = get_config_value("database", "MARQO_URL", None)
marqoClient = marqo.Client(url=marqo_url)
client = AzureOpenAI(
    azure_endpoint=os.environ["OPENAI_API_BASE"],
    api_key=os.environ["OPENAI_API_KEY"],
    api_version=os.environ["OPENAI_API_VERSION"]
)


def querying_with_langchain_gpt3(index_id, query, audience_type):
    load_dotenv()
    logger.debug(f"Query: {query}")

    gpt_model = get_config_value("llm", "gpt_model", "gpt-4")
    logger.debug(f"gpt_model: {gpt_model}")

    intent_response = "No"

    enable_bot_intent = get_config_value("llm", "enable_bot_intent", "false")
    logger.debug(f"enable_bot_intent: {enable_bot_intent}")
    if enable_bot_intent.lower() == "true":
        # intent recognition using AI
        intent_system_rules = get_config_value("llm", "intent_prompt", "")
        logger.debug(f"intent_system_rules: {intent_system_rules}")
        if intent_system_rules:
            intent_res = client.chat.completions.create(
                model=gpt_model,
                messages=[
                    {"role": "system", "content": intent_system_rules},
                    {"role": "user", "content": query}
                ],
            )
            intent_message = intent_res.choices[0].message.model_dump()
            intent_response = intent_message["content"]
            logger.info({"label": "openai_intent_response", "intent_response": intent_response})

    if intent_response.lower() == "yes":
        bot_prompt_config = get_config_value("llm", "bot_prompt", "")
        logger.debug(f"bot_prompt_config: {bot_prompt_config}")
        if bot_prompt_config:
            bot_prompt_dict = ast.literal_eval(bot_prompt_config)
            system_rules = bot_prompt_dict.get(audience_type)
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
            logger.info({"label": "openai_bot_response", "bot_response": response})
            return response, None, 200
    else:
        try:
            system_rules = ""
            activity_prompt_config = get_config_value("llm", "activity_prompt", "")
            logger.debug(f"activity_prompt_config: {activity_prompt_config}")
            if activity_prompt_config:
                activity_prompt_dict = ast.literal_eval(activity_prompt_config)
                system_rules = activity_prompt_dict.get(audience_type)

            search_index = Marqo(marqoClient, index_id, searchable_attributes=["text"])
            top_docs_to_fetch = get_config_value("database", "top_docs_to_fetch", "2")

            documents = search_index.similarity_search_with_score(query, k=20)
            logger.debug(f"Marqo documents : {str(documents)}")
            min_score = get_config_value("database", "docs_min_score", "0.7")
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
