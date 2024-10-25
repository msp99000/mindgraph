import os
import json
import asyncio
from dotenv import load_dotenv
load_dotenv()
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import JSONLoader
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from itertools import islice

# Initialize the embedding model
embedding = AzureOpenAIEmbeddings(azure_deployment="upcoretext-embedding")

# Globals to store unique keys
seen_unique_keys = set()
vector_store_keys = set()

def read_files_in_directory(directory_path):
    """Read all files in a directory and return their paths."""
    file_paths = []
    try:
        for root, dirs, files in os.walk(directory_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_paths.append(file_path)
    except (FileNotFoundError, PermissionError) as e:
        print(f"Error accessing '{directory_path}': {e}")
    return file_paths

def load_json_documents(file_paths):
    """Load JSON documents from file paths."""
    all_docs = []
    for pathfile in file_paths:
        try:
            loader = JSONLoader(
                file_path=pathfile,
                jq_schema='.[].messages[]',
                text_content=False
            )
            docs = loader.load()
            all_docs.extend(docs)
        except (ValueError, Exception) as e:
            print(f"Error processing file {pathfile}: {e}")
    return all_docs

def check_unique_msg_json(docs):
    """Check for unique keys in the JSON documents."""
    for i in reversed(range(len(docs))):
        doc = docs[i]
        try:
            page_content = json.loads(doc.page_content)
            client_msg_id = page_content.get('client_msg_id', None)
            if client_msg_id and client_msg_id in seen_unique_keys:
                print(f"Duplicate found, removing Document {i+1} with unique key: {client_msg_id}")
                docs.pop(i)
            elif client_msg_id:
                seen_unique_keys.add(client_msg_id)
        except json.JSONDecodeError as e:
            print(f"Error parsing page_content for Document {i+1}: {e}")

def check_unique_msg_vector_store(db):
    """Extract unique keys from the existing vector store documents."""
    data = db.get()
    for i, doc_content in enumerate(data["documents"]):
        try:
            page_content = json.loads(doc_content)
            client_msg_id = page_content.get('client_msg_id', None)
            if client_msg_id:
                vector_store_keys.add(client_msg_id)
            else:
                print(f"Document {i+1} does not have a client_msg_id field.")
        except json.JSONDecodeError as e:
            print(f"Error parsing page_content for Document {i+1}: {e}")

def filter_unique_documents(docs):
    """Filter out documents that already exist in the vector store."""
    filtered_docs = []
    for doc in docs:
        try:
            page_content = json.loads(doc.page_content)
            unique_key = page_content.get('client_msg_id', None)
            if unique_key and unique_key not in vector_store_keys:
                filtered_docs.append(doc)
            elif not unique_key:
                filtered_docs.append(doc)
            else:
                print(f"Duplicate found, skipping Document with unique key: {unique_key}")
        except json.JSONDecodeError as e:
            print(f"Error parsing page_content: {e}")
    return filtered_docs

def split_into_batches(chunks, batch_size):
    """Split chunks into batches of specified size."""
    it = iter(chunks)
    return iter(lambda: list(islice(it, batch_size)), [])

async def log_existing_documents(existing_chunks, log_file):
    """Log existing documents that were not added to the vector./ store."""
    log_entries = [
        f"Unique Key: {chunk.metadata.get('client_msg_id')} - Not added (already exists)"
        for chunk in existing_chunks
    ]
    log_file.write('\n'.join(log_entries) + '\n')

async def process_batch(db, chunk_batch, batch_num, semaphore, log_file):
    """Process a batch of documents, adding new ones to the vector store."""
    async with semaphore:
        new_chunks = []
        existing_chunks = []
        for chunk in chunk_batch:
            unique_key = chunk.metadata.get('client_msg_id')
            if unique_key:
                existing_doc = db.get(where={"client_msg_id": unique_key})
                if not existing_doc['ids']:
                    new_chunks.append(chunk)
                else:
                    existing_chunks.append(chunk)
            else:
                new_chunks.append(chunk)
        
        if new_chunks:
            await db.aadd_documents(new_chunks)
            print(f"Batch {batch_num}: Added {len(new_chunks)} new documents.")

        if existing_chunks:
            await log_existing_documents(existing_chunks, log_file)

async def create_vector_store():
    """Main function to create or update the vector store."""
    try:
        print("Starting create_vector_store function")
        directory_path = './db'
        file_paths = read_files_in_directory(directory_path)
        
        if not file_paths:
            print(f"No files found in directory: {directory_path}")
            return False, "No files found in directory"

        print(f"Found {len(file_paths)} files in the directory")
        docs = load_json_documents(file_paths)
        if not docs:
            print("No documents were loaded from JSON files.")
            return False, "No documents loaded from JSON files"

        print(f"Loaded {len(docs)} documents from JSON files")
        check_unique_msg_json(docs)
        print(f"After removing duplicates, {len(docs)} documents remain")
        
        try:
            db = Chroma(persist_directory="UserVectordb", embedding_function=embedding)
            print("Chroma vector store initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Chroma: {str(e)}")
            return False, f"Failed to initialize Chroma: {str(e)}"

        check_unique_msg_vector_store(db)
        
        filtered_docs = filter_unique_documents(docs)
        if not filtered_docs:
            print("No new documents to process.")
            return True, "No new documents to process"

        print(f"{len(filtered_docs)} new documents to process")

        # Split filtered docs into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(filtered_docs)
        
        if not chunks:
            print("No chunks were created from the documents.")
            return True, "No chunks created from documents"

        print(f"Number of chunks created: {len(chunks)}")
        
        # Split chunks into batches and process
        chunk_batches = list(split_into_batches(chunks, batch_size=200))
        semaphore = asyncio.Semaphore(5)  # Limit concurrent tasks

        log_file_path = "not_added_entries.log"
        with open(log_file_path, 'w') as log_file:
            tasks = []
            for batch_num, chunk_batch in enumerate(chunk_batches, 1):
                task = asyncio.create_task(process_batch(db, chunk_batch, batch_num, semaphore, log_file))
                tasks.append(task)

            await asyncio.gather(*tasks)

        # Verify that documents were added
        updated_db_data = db.get()
        total_documents = len(updated_db_data['ids'])
        print(f"Total documents in DB: {total_documents}")

        return True, f"Vector store updated successfully. Total documents: {total_documents}"
    except Exception as e:
        print(f"Error in create_vector_store: {str(e)}")
        return False, f"Error in create_vector_store: {str(e)}"