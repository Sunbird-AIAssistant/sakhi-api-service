import os
import shutil
import argparse
from typing import ( Dict, List)
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from llama_index import SimpleDirectoryReader
from env_manager import vectorstore_class
import asyncio
from logger import logger
import pandas as pd
# import tenacity
from aiohttp import ClientSession

DEFAULT_MAX_RETRIES = 3 # Retry up to 3 times
DEFAULT_WAIT_RETRIES = 2 # Wait 2 seconds between retries

def document_loader(csv_records: List[Dict]) -> List[Document]:
    """Loads documents from file paths specified in CSV records.

    Args:
        csv_records (List[Dict]): A list of dictionaries containing document information (filepath).

    Returns:
        List[Document]: A list of Document objects loaded from the specified files.
    """

    input_files = [record.get('filepath') for record in csv_records]
    return SimpleDirectoryReader(
        input_files=input_files, recursive=True).load_data() # show_progress=True 


def split_documents(records: List[Dict], documents: List[Document], chunk_size: int = 4000, chunk_overlap = 200) -> List[Document]:
    """Splits documents into chunks with overlap, adding metadata.

    Args:
        records (List[Dict]): A list of dictionaries containing document information (filename, fileurl).
        documents (List[Document]): A list of Document objects.
        chunk_size (int, optional): Maximum size of chunks. Defaults to 4000.
        chunk_overlap (int, optional): Overlap in characters between chunks. Defaults to 200.

    Returns:
        List[Document]: A list of Document objects with split content and enriched metadata.
    """

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    file_url_map : dict = {item['filename']: item['fileurl'] for item in records}

    splited_documents = []
    for document in documents:
        for chunk in text_splitter.split_text(document.text):
            splited_documents.append(Document(page_content=chunk, metadata={
                "page_label": document.metadata.get("page_label"),
                "file_name": document.metadata.get("file_name"),
                # "file_path": document.metadata.get("file_path"),
                "file_type": document.metadata.get("file_type"),
                "file_url": file_url_map.get(document.metadata.get("file_name"), '')
            }))
    return splited_documents


def transform_documents():
    pass


def load_and_split_documents(records: List[Dict], chunk_size: int, chunk_overlap: int) -> List[Document]:
    """Loads documents from records and splits them into chunks.

    Args:
        records: List of dictionaries containing document information.
        chunk_size: Size of each document chunk.
        chunk_overlap: Number of documents to overlap between chunks.

    Returns:
        A list of document chunks.
    """

    documents = document_loader(records)
    splitted_documents = split_documents(records, documents, chunk_size, chunk_overlap)
    return splitted_documents


# Function to download a single file with retries using tenacity
# @tenacity.retry(
#     wait=tenacity.wait_fixed(DEFAULT_WAIT_RETRIES),  # Wait 2 seconds between retries
#     stop=tenacity.stop_after_attempt(DEFAULT_MAX_RETRIES)  # Retry up to 3 times
# )
async def download_file(record: Dict[str, str], session: ClientSession):
    """
    Downloads a single file from the given URL with retries on errors.

    Args:
        record (Dict[str, str]): A dictionary containing file information.
        session (aiohttp.ClientSession): An aiohttp ClientSession object.

    Raises:
        tenacity.RetryError: If the download fails after all retries.
    """

    filepath = record.get('filepath')
    try:
        async with session.get(record.get('fileurl')) as response:
            response.raise_for_status()  # Raise an exception for non-200 status codes
            content = await response.read()
            with open(filepath, 'wb') as f:
                f.write(content)
            logger.info(f"Downloaded: {filepath}")
    except Exception as e:
        logger.error(f"Download failed for {filepath}: {e}")
        logger.info(f"Download failed for {filepath}. So skipping this file")
        pass
        # raise  # Re-raise the exception to stop execution


# Function to download files asynchronously
async def download_files_async(records: List[Dict[str, str]]):
    """
    Downloads files asynchronously from URLs

    Args:
        records (str): records containing filename-URL pairs.

    Raises:
        Exception: Re-raises any exceptions encountered during download.
    """
    tasks = []
    async with ClientSession() as session:
        for record in records:
            task = asyncio.create_task(download_file(record, session))
            tasks.append(task)
        await asyncio.gather(*tasks)


async def indexer_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv_path',
                        type=str,
                        required=True,
                        help='Path to the CSV file'
                        )
    parser.add_argument('--chunk_size',
                        type=int,
                        required=False,
                        help='documents chunk size',
                        default=1024
                        )
    parser.add_argument('--chunk_overlap',
                        type=int,
                        required=False,
                        help='documents chunk size',
                        default=200
                        )
    parser.add_argument('--fresh_index',
                        action='store_true',
                        help='Is the indexing fresh'
                        )
    
    args = parser.parse_args()
    CSV_PATH = args.csv_path
    FRESH_INDEX = args.fresh_index
    CHUNK_SIZE = args.chunk_size
    CHUNK_OVERLAP = args.chunk_overlap
    DOWNLOAD_DIR = 'documents'

    try:
        # Delete the directory and its contents (if it exists)
        shutil.rmtree(DOWNLOAD_DIR, ignore_errors=True)  # ignore_errors to avoid issues with non-existent directories
        
        # Create a new directory at the specified path
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        print(f"Directory '{DOWNLOAD_DIR}' created successfully!")
    except OSError as e:
        print(f"Error creating directory: {e}")

    # Read data from CSV File
    df = pd.read_csv(CSV_PATH)  # Use pandas to read the CSV file
    df['filepath']  = [ os.path.join(DOWNLOAD_DIR, row['filename']) for idx, row in df.iterrows()]
    records = df.fillna('').to_dict('records')
    logger.info(f"Total files :: => {len(records)}")

    # Function to download files asynchronously
    await download_files_async(records)

    logger.info("Loading documents...")
    documents = load_and_split_documents(records, CHUNK_SIZE, CHUNK_OVERLAP)
    print(documents)
    logger.info(f"Total documents :: => {len(documents)}")
    
    logger.info("Adding documents...")
    results = vectorstore_class.add_documents(documents, FRESH_INDEX)
    # logger.info("results =======>", results)

if __name__ == "__main__":
    try:
        asyncio.run(indexer_main())
        logger.info("Index completed successfully!")
    except Exception as e:
        logger.error(f"An error occurred: {e}")