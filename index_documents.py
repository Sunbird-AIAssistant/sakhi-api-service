from llama_index import SimpleDirectoryReader
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.marqo import Marqo
import marqo
import argparse

def load_documents(folder_path):
    source_chunks = []
    sources = SimpleDirectoryReader(input_dir=folder_path,recursive=True).load_data()
    splitter = RecursiveCharacterTextSplitter(chunk_size=4 * 1024, chunk_overlap=200)
    for source in sources:
        for chunk in splitter.split_text(source.text):
            source_chunks.append(Document(page_content=chunk, metadata={
                "page_label": source.metadata.get("page_label"),
                "file_name": source.metadata.get("file_name"),
                "file_path": source.metadata.get("file_path"),
                "file_type": source.metadata.get("file_type")
            }))
    return source_chunks

def index_documents(documents, index_name):
    try:
        add_documents_settings = { "auto_refresh": True, "client_batch_size" : 50 }
        Marqo.from_documents(documents, index_name=index_name, add_documents_settings = add_documents_settings)
        error_message = None
        status_code = 200
    except Exception as e:
        error_message = str(e.__context__) + " and " + e.__str__()
        status_code = 500
    return error_message, status_code

def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--marqo_url',
                        type=str, 
                        required=True,
                        help='Endpoint URL of marqo',
                        )
    parser.add_argument('--index_name',
                        type=str, 
                        required=True,
                        help='Name of marqo index',
                        )
    parser.add_argument('--folder_path',
                        type=str, 
                        required=True,
                        help='Path to the folder',
                        default="input_data"
                        )

    args = parser.parse_args()

    MARQO_URL = args.marqo_url
    MARQO_INDEX_NAME = args.index_name
    FOLDER_PATH = args.folder_path

    # Initialize Marqo instance
    marqo_client = marqo.Client(url=MARQO_URL)
    try:
        marqo_client.index(MARQO_INDEX_NAME).delete()
        print("Existing Index successfully deleted.")
    except:
        print("Index does not exist. Creating new index")

    marqo_client.create_index(MARQO_INDEX_NAME)
    print(f"Index {MARQO_INDEX_NAME} created.")

    print("Loading documents...")
    documents = load_documents(FOLDER_PATH)

    print("Total Documents ===>", len(documents))
    
    f = open("indexed_documents.txt", "w")
    f.write(str(documents))
    f.close()
    
    print(f"Indexing documents...")
    err, code = index_documents(documents, MARQO_INDEX_NAME)
    print(err, code)
   

    print("============ INDEX DONE =============")

if __name__ == "__main__":
    main()



# RUN

#python3 index_documents.py --marqo_url=http://0.0.0.0:8882 --index_name=sakhi_activity --folder_path=input_data