import ast
import os
from typing import (
    Any,
    List,
    Tuple
)
import marqo
from dotenv import load_dotenv
from fastapi import HTTPException
from langchain.docstore.document import Document
from langchain.vectorstores.marqo import Marqo
from openai import RateLimitError, APIError, InternalServerError

from config_util import get_config_value
from logger import logger

load_dotenv()
marqo_url = get_config_value("database", "MARQO_URL", None)
marqoClient = marqo.Client(url=marqo_url)




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
