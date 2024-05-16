from typing import (
    List,
    Tuple
)

from langchain.docstore.document import Document


class BaseVectorStore:
    """Base class for vector store implementations."""
    SPLIT_LENGTH: int = 1
    SPLIT_OVERLAP: int = 0
    BATCH_SIZE: int = 50

    def __init__(self):
        """
        Initializes the base vector store object.
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

    def add_documents(self, documents: List[Document], fresh_collection: bool = False) -> List[str]:
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
