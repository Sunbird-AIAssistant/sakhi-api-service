import logging
import openai
import os
from langchain.docstore.document import Document
from langchain.vectorstores.marqo import Marqo
import marqo
from langchain.prompts.prompt import PromptTemplate
from langchain.llms.openai import OpenAI
from langchain.chains.llm import LLMChain
from dotenv import load_dotenv
from openai import OpenAI
from typing import (
    Any,
    Dict,
    List,
    Tuple
)

log_format = '%(asctime)s - %(thread)d - %(threadName)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('jugalbandi_api')

default_language = 'en'
languages_mapping = {
    'en': "English",
    'hi': "Hindi",
    'kn': "Kannada"
}
source_default_msg = {
    'en': "Here are some references links that you may enjoy:",
    'hi': "यहां कुछ संदर्भ लिंक दिए गए हैं जिनका आप आनंद ले सकते हैं:",
    'kn': "ನೀವು ಆನಂದಿಸಬಹುದಾದ ಕೆಲವು ಉಲ್ಲೇಖ ಲಿಂಕ್‌ಗಳು ಇಲ್ಲಿವೆ:"
}

load_dotenv()
marqo_url = os.environ["MARQO_URL"]
marqoClient = marqo.Client(url=marqo_url)

def rephrased_question(user_query):
    template = """
    Write the same question as user input and make it more descriptive without adding new information and without making the facts incorrect.

    User: {question}
    Rephrased User input:"""
    prompt = PromptTemplate(template=template, input_variables=["question"])
    llm_chain = LLMChain(prompt=prompt, llm=OpenAI(temperature=0), verbose=False)
    response = llm_chain.predict(question=user_query)
    return response.strip()

def querying_with_langchain_gpt3(index_id, query):
    load_dotenv()
    try:
        search_index = Marqo(marqoClient, index_id, searchable_attributes=["text"])
        documents = search_index.similarity_search_with_score(query, k=4)
        
        if not documents:
                return "I'm sorry, but I don't have enough information to provide a specific answer for your question. Please provide more information or context about what you are referring to.", None, None, None, 200

        print(str(documents))
        contexts =  [document.page_content for document, search_score in documents]
        contexts = "\n\n---\n\n".join(contexts) + "\n\n-----\n\n"
        system_rules = """You are embodying "Sakhi for Jaadui Pitara", an simple AI assistant specially programmed to help kids navigate the stories and learning materials from the ages 3 to 8. Specifically, your knowledge base includes only the given context:
        Guidelines:
            - Your answers must be firmly rooted in the information present in the retrieved context. Ensure that your responses are directly based on these resources, not on prior knowledge or assumptions.
            - If no contexts are retrieved, then you should not answer the question.
        
        Given the following contexts:                
        {context}

        All answers should be in MARKDOWN (.md) Format:"""

        system_rules = system_rules.format(context=contexts)
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        res = client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": system_rules},
                {"role": "user", "content": query},
            ],
        )
        message = res.choices[0].message.model_dump()
        response = message["content"]
        return response, documents, None, None, 200
    except openai.RateLimitError as e:
        error_message = f"OpenAI API request exceeded rate limit: {e}"
        status_code = 500
    except (openai.APIError, openai.InternalServerError):
        error_message = "Server is overloaded or unable to answer your request at the moment. Please try again later"
        status_code = 503
    except Exception as e:
        error_message = str(e.__context__) + " and " + e.__str__()
        status_code = 500
    return "", None, None, error_message, status_code

def get_source_markdown(documents: List[Tuple[Document, Any]], language = default_language) -> str:
    sources =  [document.metadata for document, search_score in documents]
    added_sources = []
    sources_markdown = f'\n\n{source_default_msg[language]} \n\n'
    counter = 1
    for data in sources:  
        print(data) 
        if not data["file_name"] in added_sources:
            sources_markdown = sources_markdown + f'''{counter}. {data["file_name"]} \n\n'''
            added_sources.append(data["file_name"])
            counter += 1

    return sources_markdown

# User feedback
async def record_user_feedback(engine, qa_id, feedback_type):
    try:
       async with engine.acquire() as connection:
            record_exists = await connection.fetchval("SELECT id FROM sb_qa_logs WHERE question_id = $1", qa_id)
            if record_exists is not None:
                if feedback_type.lower() == "up":
                    await connection.execute("UPDATE sb_qa_logs SET upvotes = upvotes + 1 WHERE question_id = $1", qa_id)
                elif feedback_type.lower() == "down":
                    await connection.execute("UPDATE sb_qa_logs SET downvotes = downvotes + 1 WHERE question_id = $1", qa_id)
                return 'OK', None, 200
            else:
                 return None, f"Record with ID {qa_id} not found", 404
    except Exception as e:
        error_message = str(e.__context__) + " and " + e.__str__()
        status_code = 500
        print(f"Error while giving feedback: {e}")
        return None, error_message, status_code
