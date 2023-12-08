import requests
import json
import os.path
from llama_index import SimpleDirectoryReader
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.marqo import Marqo
import marqo
import shutil

marqo_url = "http://localhost:8882"
marqo_discovery_index_name = "sakhi_discovery_all"
marqo_converse_index_name = "sakhi_converse_english"

mimeTypes = ["application/pdf", "video/mp4"]
default_language = "english"

def make_post_api_request(url, headers, data):
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()

def make_get_api_request(url, headers, data):
    response = requests.get(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()

def get_all_identifiers(response):
    identifiers = []
    for result in response["result"]["content"]:
        identifiers.append(result["identifier"])
    return identifiers

def find_children_with_mime_type(content):
    contentMetdata = []
    for child in content["children"]:
        if child["mimeType"] in mimeTypes:
            contentMetdata.append(child)
        elif child["mimeType"] == "application/vnd.ekstep.content-collection":
            contentMetdata.extend(find_children_with_mime_type(child))
    return contentMetdata

def get_metadata_of_children(identifiers):
    contents = []
    for identifier in identifiers:
        url = "https://sunbirdsaas.com/action/content/v3/hierarchy/{}".format(identifier)
        response = make_get_api_request(url, None, None)
        childrens = find_children_with_mime_type(response["result"]["content"])
        contents = contents + childrens
    return contents

def extract_filename_from_url(url):
  """Extracts the file name from the given URL.

  Args:
    url: The URL to extract the file name from.

  Returns:
    The file name, or None if the URL does not contain a file name.
  """
  url_parts = url.split("/")
  filename = url_parts[-1]
  if filename == "":
    return None
  return filename

def download_file(url, save_path):
    """Downloads a big file from the given URL and saves it to the given filename.

    Args:
        url: The URL of the file.
        filename: The filename to save the file to.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        print("Content downloaded and saved successfully ===>" , save_path)
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        print("Content download and save process failed ===>" , save_path)

def get_all_collection(): 
    url = "https://sunbirdsaas.com/api/content/v1/search"
    headers = {"Content-Type": "application/json"}
    data = {
        "request": {
            "filters": {
                "channel": "013812745304276992183",
                "contentType": ["Collection"],
                "keywords": ["djp_category_toys", "djp_category_games", "djp_category_stories", "djp_category_flashc", "djp_category_activitys", "djp_category_manuals"]
            }
        }
    }
    response = make_post_api_request(url, headers, data)
    return response

def get_language_code(data):
    language = None
    try:
        language = data["languages"][0]
    except:
        language = default_language
    return language

def get_english_documents(contents):
    source_chunks = []
    indexed_content = []
    for data in contents:
        language = get_language_code(data)
        if not data["identifier"] in indexed_content and language.lower() == "english":
            sources = SimpleDirectoryReader(input_files=[data["filepath"]],recursive=True).load_data()
            splitter = RecursiveCharacterTextSplitter(chunk_size=4 * 1024, chunk_overlap=200)
            for source in sources:
                for chunk in splitter.split_text(source.text):
                    source_chunks.append(Document(page_content=chunk, metadata={ 
                    "name": data["name"],
                    "previewUrl": data["previewUrl"],
                    "artifactUrl": data["artifactUrl"],
                    "downloadUrl": data["downloadUrl"],
                    "mimeType": data["mimeType"],
                    "identifier" : data["identifier"],
                    "contentType": data["contentType"]
                }))
            indexed_content.append(data["identifier"])
    
    print("Total english contents ===> ", len(indexed_content))
    return source_chunks

def get_all_documents(contents):
    source_chunks = []
    indexed_content = []
    data:dict
    for data in contents:
        if not data["identifier"] in indexed_content:  
            source_chunks.append({
                "name": data["name"],
                "keywords": data.get("keywords", ''),
                "description": data.get("description", ''),
                "themes": data.get("themes", ''),
                "languages": data.get("languages", ''),
                "metadata" : json.dumps({
                    "name": data["name"],
                    "previewUrl": data["previewUrl"],
                    "artifactUrl": data["artifactUrl"],
                    "downloadUrl": data["downloadUrl"],
                    "mimeType": data["mimeType"],
                    "identifier" : data["identifier"],
                    "contentType": data["contentType"]
                })
            })
            indexed_content.append(data["identifier"])
    
    print("Total contents ===> ", len(indexed_content))
    return source_chunks

def index_english_documents(documents, index_name):
    try:
        add_documents_settings = { "auto_refresh": True, "client_batch_size" : 50 }
        Marqo.from_documents(documents, index_name=index_name, add_documents_settings = add_documents_settings)
        error_message = None
        status_code = 200
    except Exception as e:
        error_message = str(e.__context__) + " and " + e.__str__()
        status_code = 500
    return error_message, status_code

def index_all_documents(documents, index_name):
    try:
        client = marqo.Client(url=marqo_url)
        try:
            client.create_index(index_name)
            print(f"Created {index_name} successfully.")
        except Exception:
            print(f"Index {index_name} exists.")
        client.index(index_name).add_documents(documents, client_batch_size=50, tensor_fields = ["name", "description"]) # keywords, themes
        error_message = None
        status_code = 200
    except Exception as e:
        error_message = str(e.__context__) + " and " + e.__str__()
        status_code = 500
    return error_message, status_code

def main():
    output_dir_path = 'data/'
    shutil.rmtree(output_dir_path)
    
     # Make the first API request to search for collections
    collections = get_all_collection()

    # Get all the identifiers from the response
    identifiers = get_all_identifiers(collections)
    print("Total collections ::", len(identifiers))

    # Get all the contents
    contents = get_metadata_of_children(identifiers)
    print("Total contents ::", len(contents))

    # Create output directory if not exist
    os.makedirs(output_dir_path, exist_ok=True)

   # Download all the contents and save it to the given filename.
    for data in contents:
        filename = extract_filename_from_url(data["artifactUrl"])
        data["filepath"] = output_dir_path + filename
        download_file(data["artifactUrl"], data["filepath"])

    print("All the contents have been downloaded successfully")

    f = open("jadupitara_documents.json", "w")
    f.write(json.dumps(contents))
    f.close()
    english_documents = get_english_documents(contents)
    all_documents = get_all_documents(contents)

    # create index
    err, code = index_english_documents(english_documents, marqo_converse_index_name)
    print(err, code)
    err, code = index_all_documents(all_documents, marqo_discovery_index_name)
    print(err, code)

    print("============ DONE =============")

if __name__ == "__main__":
    main()