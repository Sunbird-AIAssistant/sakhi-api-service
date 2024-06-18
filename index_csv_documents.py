import argparse
from typing import (
    List
)
from langchain.docstore.document import Document
from langchain_community.document_loaders import DirectoryLoader, CSVLoader
from env_manager import vectorstore_class
from query_with_langchain import call_chat_model


def generate_summary(source_text: str) -> str:
    print("Source Text:: ", source_text)
    prompt = "Summarize the following text containing all passed information which is in the form of key-value pairs. Keep the values as-is in the summarised text:\n\n" + source_text
    response = call_chat_model(
        messages=[
            {"role": "system", "content": prompt}
        ])
    return response


def load_documents(folder_path: str) -> List[Document]:
    documents = []
    text_loader_kwargs = {"autodetect_encoding": True}
    loader = DirectoryLoader(folder_path, glob="**/*.csv", loader_cls=CSVLoader, loader_kwargs=text_loader_kwargs)
    sources = loader.load()
    for source in sources:
        summary = generate_summary(source.page_content.replace(u'\xa0', ' '))
        print("Row Summary:: ", summary)
        documents.append(Document(page_content=summary.encode('utf-8'), metadata={
            "page_label": source.metadata.get("row"),
            "file_name": source.metadata.get("source")
        }))
    return documents


def indexer_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder_path',
                        type=str,
                        required=True,
                        help='Path to the folder',
                        default="input_data"
                        )
    parser.add_argument('--fresh_index',
                        action='store_true',
                        help='Is the indexing fresh'
                        )

    args = parser.parse_args()

    FOLDER_PATH = args.folder_path
    FRESH_INDEX = args.fresh_index

    documents = load_documents(FOLDER_PATH)
    print("Total documents :: =>", len(documents))

    print("Adding documents...")
    results = vectorstore_class.add_documents(documents, FRESH_INDEX)
    print("results =======>", results)

    print("============ INDEX DONE =============")


if __name__ == "__main__":
    indexer_main()

# For Fresh collection
# python3 index_documents.py --folder_path=Documents --fresh_index

# For appending documents to existing collection
# python3 index_documents.py --folder_path=Documents
