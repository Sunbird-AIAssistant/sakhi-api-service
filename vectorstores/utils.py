
import json
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple
)
import os
import marqo
from langchain.docstore.document import Document
from langchain.vectorstores.marqo import Marqo

class BaseVectorStore:
    """Base class for vector store implementations."""
    SPLIT_LENGTH: int = 1
    SPLIT_OVERLAP: int = 0
    BATCH_SIZE: int = 50
    def __init__(self):
        """
        Initializes the base vector store object.

        Args:
            db_url: The URL of the database where the vector store resides.
            collection_name: The name of the collection within the database.
        """
        pass

    def get_client(self):
        """
        Returns the client object used to interact with the vector store.

        This method should be overridden by subclasses to implement their specific client retrieval logic.

        Returns:
            The client object used to interact with the vector store.
        """
        raise NotImplementedError

    def init_client(self):
        """
        Initializes the client object used to interact with the vector store.

        This method should be overridden by subclasses to implement their specific client initialization logic.

        Raises:
            NotImplementedError: This method is not implemented in the base class.
        """
        raise NotImplementedError

    def chunk_list(self, document: List, batch_size: int) -> List[List]:
        """
        Returns a list of batch sized chunks from the provided document list.

        Args:
            document: The list of documents to be chunked.
            batch_size: The size of each chunk.

        Returns:
            A list of lists, where each inner list represents a batch of documents.
        """
        return [document[i: i + batch_size] for i in range(0, len(document), batch_size)]

    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Adds a list of documents to the vector store.

        This method should be overridden by subclasses to implement their specific logic for adding documents.

        Args:
            documents: A list of documents to be added.

        Returns:
            A list of document IDs for the added documents.
        """
        raise NotImplementedError

    def similarity_search_with_score(self, query: str, collection_name: str, k: int = 20) -> List[Tuple[Document, float]]:
        """
        Performs a similarity search on the vector store and returns documents with their scores.

        This method should be overridden by subclasses to implement their specific logic for similarity search.

        Args:
            query: The query string to search for.
            collection_name: The name of the collection within the vector store to search in.
            k: The maximum number of documents to fetch from the vector store (default: 20).

        Returns:
            A list of tuples, where each tuple contains a document and its corresponding score.
        """
        raise NotImplementedError

class MarqoVectorStore(BaseVectorStore):
    TENSOR_FIELDS: str = ["text"]
    client: marqo.Client
    def __init__(self, fresh_collection: bool = False):
        self.client_url = os.getenv("VECTOR_STORE_ENDPOINT")
        self.collection_name = os.getenv("VECTOR_COLLECTION_NAME")
        self.embedding_model = os.getenv("EMBEDDING_MODEL")
        self.index_settings = {
            "index_defaults": {
                "treat_urls_and_pointers_as_images": False,
                "model": self.embedding_model,
                "normalize_embeddings": True,
                "text_preprocessing": {
                    "split_length": self.SPLIT_LENGTH,
                    "split_overlap":self.SPLIT_OVERLAP,
                    "split_method": "sentence"
                }
            }
        }
        self.fresh_collection = fresh_collection

        if not self.client_url:
            raise ValueError("Missing environment variable VECTOR_STORE_ENDPOINT.")

        if not self.collection_name:
            raise ValueError("Missing environment variable VECTOR_COLLECTION_NAME.")
        
        if not self.embedding_model:
            raise ValueError("Missing environment variable EMBEDDING_MODEL.")

        self.init_client()
    
    def get_client(self) -> marqo.Client:
        return self.client
    
    def init_client(self):
        self.client = marqo.Client(url=self.client_url)
        if self.fresh_collection:
            try:
                self.client.index(self.collection_name).delete()
                print("Existing Index successfully deleted.")
            except:
                print("Index does not exist. Creating new index...")

            self.client.create_index(
                self.collection_name, settings_dict=self.index_settings)
            print(f"Index {self.collection_name} created.")

    def add_documents(self, documents = List[Document]) -> List[str]:
        docs: List[Dict[str, str]] = []
        ids = []
        for d in documents:
            doc = {
                "text": d.page_content,
                "metadata": json.dumps(d.metadata) if d.metadata else json.dumps({}),
            }
            docs.append(doc)
        chunks = list(self.chunk_list(docs, self.BATCH_SIZE))
        for chunk in chunks:
            response = self.client.index(self.collection_name).add_documents(
                documents=chunk, client_batch_size=self.BATCH_SIZE, tensor_fields=self.TENSOR_FIELDS)
            if response[0]["errors"]:
                err_msg = (
                    f"Error in upload for documents in index range"
                    f"check Marqo logs."
                )
                raise RuntimeError(err_msg)
            ids += [item["_id"] for item in response[0]["items"]]
            
        return ids

    def similarity_search_with_score(self, query: str, collection_name: str, k :int = 20) -> List[Tuple[Document, float]]:
        docsearch = Marqo(self.client, index_name=collection_name, searchable_attributes=["text"])
        documents = docsearch.similarity_search_with_score(query, k)
        return documents
