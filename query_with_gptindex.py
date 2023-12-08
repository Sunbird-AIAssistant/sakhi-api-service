import openai
from llama_index import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
from cloud_storage import *


def querying_with_gptindex(uuid_number, query):
    files_count = read_given_file(uuid_number, "index.json")
    if files_count:
        storage_context = StorageContext.from_defaults(persist_dir="./storage")
        index = load_index_from_storage(storage_context)
        try:
            response = index.query(query)
            source_node = response.source_nodes
            source_text = ""
            if len(source_node):
                source_text = source_node[0].source_text
            os.remove("index.json")
            return str(response).strip(), source_text.strip(), None, 200
        except openai.error.RateLimitError as e:
            error_message = f"OpenAI API request exceeded rate limit: {e}"
            status_code = 500
        except (openai.error.APIError, openai.error.ServiceUnavailableError):
            error_message = "Server is overloaded or unable to answer your request at the moment. Please try again later"
            status_code = 503
        except Exception as e:
            error_message = str(e.__context__) + " and " + e.__str__()
            status_code = 500
    else:
        error_message = "The UUID number is incorrect"
        status_code = 422
    return None, None, error_message, status_code


def gpt_indexing(uuid_number):
    try:
        documents = SimpleDirectoryReader(uuid_number).load_data()
        index = VectorStoreIndex().from_documents(documents)
        index.storage_context.persist()
        index.save_to_disk("index.json")
        error_message = None
        status_code = 200
    except openai.error.RateLimitError as e:
        error_message = f"OpenAI API request exceeded rate limit: {e}"
        status_code = 500
    except (openai.error.APIError, openai.error.ServiceUnavailableError):
        error_message = "Server is overloaded or unable to answer your request at the moment. Please try again later"
        status_code = 503
    except Exception as e:
        error_message = str(e.__context__) + " and " + e.__str__()
        status_code = 500
    return error_message, status_code
