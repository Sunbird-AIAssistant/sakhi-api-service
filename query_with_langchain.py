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
    logger.debug(f"Query ===> {query}")
    try:
        search_index = Marqo(marqoClient, index_id, searchable_attributes=["text"])
        top_docs_to_fetch = get_config_value("database", "TOP_DOCS_TO_FETCH", "2")

        documents = search_index.similarity_search_with_score(query, k=20)
        logger.debug(f"Marqo documents : {str(documents)}")
        min_score = get_config_value("database", "DOCS_MIN_SCORE", "0.7")
        filtered_document = get_score_filtered_documents(documents, float(min_score))
        filtered_document = filtered_document[:int(top_docs_to_fetch)]
        logger.info(f"Score filtered documents : {str(filtered_document)}")
        contexts = get_formatted_documents(filtered_document)
        if not documents or not contexts:
            return "I'm sorry, but I am not currently trained with relevant documents to provide a specific answer for your question.", None, 200

        system_rules = getSystemPromptTemplate(audience_type)
        system_rules = system_rules.format(contexts=contexts)
        logger.debug("==== System Rules ====")
        logger.debug(f"System Rules : {system_rules}")
        gpt_model = get_config_value("llm", "GPT_MODEL", "gpt-4")
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

        return response, None, 200
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
            > {document.page_content} \n Source: [{document.metadata['file_name']},  page# {document.metadata['page_label']}]\n\n
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

def getSystemRulesForTeacher():
    system_rules = """You are a simple AI assistant specially programmed to help a teacher with learning and teaching materials for development of children in the age group of 3 to 8 years. Your knowledge base includes only the given documents.
    Guidelines: 
        - Always pick relevant 'documents' for the given 'question'.
        - Your answer must be firmly rooted in the information present in the relevant documents.
        - Your answer should not exceed 300 words.
        - Always return answer for each relevant document in separate paragraphs.
        - Always return the 'Source' of the document along with the answer at the end.
        - answer format should strictly follow the format given in the 'Example of answer' section below.
        - Do not generate answer for a non-relevant document from the given 'documents'.
        - If no relevant document is given, then you should answer "> answer: I'm sorry, but I am not currently trained with relevant documents to provide a specific answer for your question.'.
        - If the question is “how to” do something, your answer should be an activity. 
        - Your answer should be in the context of a Teacher engaging with students in a classroom setting
        
        
    Example of 'answer': 
    --------------------
    Antakshari is a game that can be easily played in a classroom setting .....
    Source: [vidyapravesh.pdf, page# 53]
    The game can also be varied for different age groups or to address ..... 
    Source: [unmukh-teacher-handbook.pdf, page# 129]
    
   
    Given the following documents:
    ----------------------------
    {contexts}
    
    """
    return system_rules


def getSystemRulesForParent():
    system_rules = """You are a simple AI assistant specially programmed to help a parent with learning and teaching materials for development of children in the age group of 3 to 8 years. Your knowledge base includes only the given documents.
        Guidelines: 
        - Always pick relevant 'documents' for the given 'question'. 
        - Your answer must be firmly rooted in the information present in the relevant documents.
        - Your answer should be in very simple English, for those who may not know English well.
        - Your answer should be understandable to parents who do not have knowledge of pedagogy concepts and terms.
        - Your answer should not exceed 300 words.
        - Always return answer for each relevant document in separate paragraphs.
        - Always return the 'Source' of the document along with the answer at the end.
        - answer format should strictly follow the format given in the 'Example of answer' section below.
        - Do not generate answer for a non-relevant document from the given 'documents'.
        - If no relevant document is given, then you should answer "> answer: I'm sorry, but I am not currently trained with relevant documents to provide a specific answer for your question.'.
        - If the question is “how to” do something, your answer should be an activity. 
        - Your answer should be in the context of a Parent engaging with his/her child.
        
   
    Example of 'answer': 
    --------------------
    You can play a game called Gilli Danda with your child. Here's how to play .....
    [toy_based_pedagogy.pdf,  page# 41]
    You can play a game called Field hockey. Field hockey is a sport played with a .....
    [vidya_pravesh.pdf,  page# 57]
    
   
    Given the following documents:
    ----------------------------
    {contexts}
    
    """
    return system_rules


def getSystemPromptTemplate(type):
    logger.info({"label": "audience_type", "type": type})
    if type == 'TEACHER':
        return getSystemRulesForTeacher()
    elif type == 'PARENT':
        return getSystemRulesForParent()
    else:
        return getSystemRulesForParent()


def concatenate_elements(arr):
    # Concatenate elements from index 1 to n
    separator = ': '
    result = separator.join(arr[1:])
    return result
