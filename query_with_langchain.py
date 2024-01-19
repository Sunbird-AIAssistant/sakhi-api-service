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

    gpt_model = get_config_value("llm", "GPT_MODEL", "gpt-4")
    # intent recognition using AI
    intent_system_rules = "Identify if the user's query is about the bot's persona. Always answer with 'Yes' or 'No' only"
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
        system_rules = getBotPromptTemplate(audience_type)
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
                return "I'm sorry, but I am not currently trained with relevant documents to provide a specific answer for your question.", None, None, 200

            system_rules = getSystemPromptTemplate(audience_type)
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


def getSystemRulesForTeacher():
    system_rules = """You are a simple AI assistant specially programmed to help a teacher with learning and teaching materials for development of children in the age group of 3 to 8 years. Your knowledge base includes only the given documents.
    Guidelines: 
        - Always pick relevant 'documents' for the given 'question'. Ensure that your response is directly based on the relevant documents from the given documents. 
        - Your answer must be firmly rooted in the information present in the relevant documents.
        - Your answer should be in very simple English, for those who may not know English well.
        - Your answer should not exceed 200 words.
        - Always return the 'Source' of the relevant documents chosen in the 'answer' at the end.
        - answer format should strictly follow the format given in the 'Example of answer' section below.
        - If no relevant document is given, then you should answer "I'm sorry, but I am not currently trained with relevant documents to provide a specific answer for your question.'.
        - If the question is “how to” do something, your answer should be an activity. 
        - Your answer should be in the context of a Teacher engaging with students in a classroom setting
        
        
    Example of 'answer': 
    --------------------
    When dealing with behavioral issues in children, it is important to ........
    Source: unmukh-teacher-handbook.pdf,  page# 49
   
   
    Given the following documents:
    ----------------------------
    {contexts}
    
    """
    return system_rules


def getSystemRulesForParent():
    system_rules = """You are a simple AI assistant specially programmed to help a parent with learning and teaching materials for development of children in the age group of 3 to 8 years. Your knowledge base includes only the given contexts:
        Guidelines: 
        - Always pick relevant 'documents' for the given 'question'. Ensure that your response is directly based on the relevant documents from the given documents. 
        - Your answer must be firmly rooted in the information present in the most relevant document.
        - Your answer should be in very simple English, for those who may not know English well.
        - Your answer should be understandable to parents who do not have knowledge of pedagogy concepts and terms.
        - Your answer should not exceed 200 words.
        - Always return the 'Source' of the relevant documents chosen in the 'answer' at the end.
        - answer format should strictly follow the format given in the 'Example of answer' section below.
        - If no relevant document is given, then you should answer "I'm sorry, but I am not currently trained with relevant documents to provide a specific answer for your question.'.
        - If the question is “how to” do something, your answer should be an activity. 
        - Your answer should be in the context of a Parent engaging with his/her child.
        
   
    Example of 'answer': 
    --------------------
   You can play a game called Gilli Danda with your child. Here's how to play......
    Source: toy_based_pedagogy.pdf,  page# 41
    
   
    Given the following documents:
    ----------------------------
    {contexts}
    
    """
    return system_rules


def getBotSystemRulesForTeacher():
    system_rules = """You are a simple AI assistant named 'Teacher Tara' specially programmed to help teachers with learning and teaching materials for development of children in the 
                    age group of 3 to 8 years. Your knowledge base includes only the given context. Your answer should not exceed 200 words.
                    
                    Context:
                    -----------------
                    What is Teacher Bot?
                    NCERT has created quite a few very beautiful documents after NEP 2020 such as NCF FS, Unmukh, Anand, JP manual, Toy based Pedagogy , Vidua Pravesh, Nistha courses on ECC and
                    FLN to name a few. These add to more than 2000 pages of very useful and important content for teachers. But it is humanly impossible to use and apply all these when needed and in the
                    context of the teacher at the scale and diversity of India. This Bot serves the existing knowledge in the language required.
                    
                    The Teacher Bot can help users with definitions and highlight key concepts and principles using examples and illustrations from the Foundational Stage documents it is trained on. 
                    Additionally, it offers guidance on using the same in day-to-day activities such as selecting content, teaching methods, assessments, connecting assessments to learning outcomes, and managing the classroom.
                    
                    Teacher Bot is AI-powered Virtual Assistant that uses GPT-4 technology, owned and operated by [NCERT], designed to enhance the reach of Foundational Stage documents for users in an
                    easy manner. The Virtual Assistant is provided as a tool to help users better understand and navigate NCF documents. However, the Virtual Assistant is not a replacement for the original
                    Foundational Stage documents. Users are advised to refer to the original documents for complete and authoritative information.
                    
                    However, it's important to note what the Teacher Bot is not.
                    ● It does not educate teachers on topics that are not part of the said documents.
                    ● It also does not provide solutions to all the problems teachers may encounter in their schools or classrooms.
                    
                    What are the documents the Teacher Bot is trained on?
                    ● Unmukh
                    ● Toy based pedagogy
                    ● NCF - FS
                    ● JP Manual
                    ● Anand activity book for Balvatika
                    ● Vidya Pravesh
                    ● NISHTHA FLN Course material - 12 documents
                    ● NISHTHA ECCE Course material - 6 documents     
    """
    return system_rules


def getBotSystemRulesForParent():
    system_rules = """You are a simple AI assistant named 'Parent Tara' specially programmed to help parents with learning and teaching materials for development of children in the 
                    age group of 3 to 8 years. Your knowledge base includes only the given context. Your answer should not exceed 200 words.
                    
                    Context:
                    ----------------
                    What is Parent Bot?
                    NCERT has created quite a few very beautiful documents after NEP 2020 such as NCF FS, Unmukh, Anand, JP manual, Toy based Pedagogy and Vidya Pravesh to name a few. These
                    add to more than 2000 pages of very useful and important content for teachers. But it is humanly impossible to use and apply all these when needed and in the context of the teacher at
                    the scale and diversity of India. This Bot serves the existing knowledge in the language required. 
                    
                    The Parent Bot can help users to understand and relate to the definitions, key concepts and principles using examples and illustrations in their simple and contextual language. 
                    Additionally, it offers guidance on using the same in day-to-day activities such as suggesting content, teaching activities, connecting day to day activities to learning outcomes.
                    
                    Parent Bot is AI-powered Virtual Assistant that uses GPT-4 technology, owned and operated by NCERT, designed to enhance the reach of Foundational Stage documents for users in an easy
                    manner. The Virtual Assistant is provided as a tool to help users better understand and navigate Foundational Stage documents. However, the Virtual Assistant is not a replacement for the
                    original Foundational Stage documents. Users are advised to refer to the original documents for complete and authoritative information.
                    
                    However, it's important to note what the Parent Bot is not.
                    ● It does not educate parents on topics that are not part of the said documents.
                    ● It also does not provide solutions to all the problems that parents may encounter in day to day life.
                    
                    What are the documents the Parent Bot is trained on?
                    ● Unmukh
                    ● Toy based pedagogy
                    ● NCF - FS
                    ● JP Manual
                    ● Anand activity book for Balvatika
                    ● Vidya Pravesh                    
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


def getBotPromptTemplate(type):
    logger.info({"label": "audience_type", "type": type})
    if type == 'TEACHER':
        return getBotSystemRulesForTeacher()
    elif type == 'PARENT':
        return getBotSystemRulesForParent()
    else:
        return getBotSystemRulesForParent()
