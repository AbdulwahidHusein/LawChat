import os
import glob
import json
from typing import List, Dict, Any
from datetime import datetime

import openai
from pinecone import Pinecone
import PyPDF2
from tqdm.auto import tqdm

# Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")  # Set in environment or replace with your OpenAI API key
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")  # Set in environment or replace with your Pinecone API key
PINECONE_INDEX_NAME = "test-index"
PINECONE_HOST = "https://test-index-t9390q6.svc.aped-4627-b74a.pinecone.io"
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
TRACKING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "processed_files.json")

# Create the docs directory if it doesn't exist
if not os.path.exists(DOCS_DIR):
    os.makedirs(DOCS_DIR)
    print(f"Created directory: {DOCS_DIR}")

CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI embedding model
BATCH_SIZE = 50  # Number of embeddings to create/upsert in one batch

def load_processed_files() -> Dict[str, Dict[str, Any]]:
    """Load the list of already processed files from the tracking file."""
    if os.path.exists(TRACKING_FILE):
        try:
            with open(TRACKING_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error reading tracking file. Starting with empty tracking.")
            return {}
    return {}

def save_processed_files(processed_files: Dict[str, Dict[str, Any]]):
    """Save the list of processed files to the tracking file."""
    with open(TRACKING_FILE, 'w') as f:
        json.dump(processed_files, f, indent=2)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + " "
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def chunk_text(text: str, filename: str) -> List[Dict[str, Any]]:
    """Split text into chunks with metadata."""
    chunks = []
    for i in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP):
        chunk_text = text[i:i + CHUNK_SIZE]
        if len(chunk_text) < 50:  # Skip very small chunks
            continue
        
        chunk_data = {
            "text": chunk_text,
            "metadata": {
                "source": filename,
                "chunk_index": len(chunks),
                "char_start": i,
                "char_end": i + len(chunk_text)
            }
        }
        chunks.append(chunk_data)
    return chunks

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Get OpenAI embeddings for multiple texts in a batch."""
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(
        input=texts,
        model=EMBEDDING_MODEL
    )
    return [data.embedding for data in response.data]

def prepare_batches(items: List[Dict[str, Any]], batch_size: int):
    """Prepare batches for processing."""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

def file_has_changed(file_path: str, processed_files: Dict[str, Dict[str, Any]]) -> bool:
    """Check if a file has changed since it was last processed."""
    filename = os.path.basename(file_path)
    file_stats = os.stat(file_path)
    file_size = file_stats.st_size
    file_mtime = file_stats.st_mtime
    
    if filename in processed_files:
        # Check if file size or modification time has changed
        if (file_size == processed_files[filename]["size"] and 
            file_mtime == processed_files[filename]["mtime"]):
            return False
    
    return True

def main():
    """Process all PDF files in the docs directory and upsert to Pinecone."""
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is required. Set the OPENAI_API_KEY environment variable.")
    
    if not PINECONE_API_KEY:
        raise ValueError("Pinecone API key is required. Set the PINECONE_API_KEY environment variable.")
    
    # Load the list of already processed files
    processed_files = load_processed_files()
    
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(host=PINECONE_HOST)
    
    # Get index statistics before processing
    before_stats = index.describe_index_stats()
    print(f"Pinecone index '{PINECONE_INDEX_NAME}' currently contains {before_stats.total_vector_count} vectors")
    
    # Get all PDF files in the docs directory
    pdf_files = glob.glob(os.path.join(DOCS_DIR, "*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {DOCS_DIR}")
    
    if not pdf_files:
        print(f"No PDF files found in {DOCS_DIR}")
        return
    
    # Filter out already processed files that haven't changed
    files_to_process = []
    skipped_files = []
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        if filename in processed_files and not file_has_changed(pdf_path, processed_files):
            skipped_files.append(filename)
        else:
            files_to_process.append(pdf_path)
    
    if skipped_files:
        print(f"Skipping {len(skipped_files)} already processed files: {', '.join(skipped_files)}")
    
    if not files_to_process:
        print("No new or modified files to process. Exiting.")
        return
    
    print(f"Processing {len(files_to_process)} new or modified files")
    
    all_chunks = []
    processed_file_data = {}
    
    # Step 1: Extract text and create chunks
    for pdf_path in tqdm(files_to_process, desc="Processing PDFs"):
        filename = os.path.basename(pdf_path)
        text = extract_text_from_pdf(pdf_path)
        if text:
            chunks = chunk_text(text, filename)
            all_chunks.extend(chunks)
            print(f"Extracted {len(chunks)} chunks from {filename}")
            
            # Update processed files tracking
            file_stats = os.stat(pdf_path)
            processed_file_data[filename] = {
                "size": file_stats.st_size,
                "mtime": file_stats.st_mtime,
                "chunks": len(chunks),
                "processed_at": datetime.now().isoformat(),
                "vector_count": len(chunks),
            }
    
    print(f"Total chunks created: {len(all_chunks)}")
    
    if not all_chunks:
        print("No chunks were created. Exiting.")
        return
    
    # Step 2: Generate embeddings and upsert to Pinecone in batches
    total_upserted = 0
    for batch_index, batch in enumerate(prepare_batches(all_chunks, BATCH_SIZE)):
        try:
            # Create embeddings for the batch
            texts = [item["text"] for item in batch]
            ids = [f"doc_{item['metadata']['source']}_{item['metadata']['chunk_index']}" for item in batch]
            
            print(f"Generating embeddings for batch {batch_index + 1}/{len(all_chunks) // BATCH_SIZE + 1}...")
            embeddings = get_embeddings(texts)
            
            # Prepare records for Pinecone
            records = [
                {
                    "id": ids[i],
                    "values": embeddings[i],
                    "metadata": {
                        "text": batch[i]["text"],
                        "source": batch[i]["metadata"]["source"],
                        "chunk_index": batch[i]["metadata"]["chunk_index"],
                        "char_start": batch[i]["metadata"]["char_start"],
                        "char_end": batch[i]["metadata"]["char_end"]
                    }
                }
                for i in range(len(batch))
            ]
            
            # Upsert to Pinecone
            upsert_response = index.upsert(vectors=records)
            total_upserted += len(records)
            print(f"Upserted batch {batch_index + 1} ({len(records)} records) to Pinecone")
            
        except Exception as e:
            print(f"Error processing batch {batch_index + 1}: {e}")
    
    # Save the updated processed files tracking
    processed_files.update(processed_file_data)
    save_processed_files(processed_files)
    
    # Get stats after processing
    after_stats = index.describe_index_stats()
    print(f"Processing complete. Upserted {total_upserted} vectors.")
    print(f"Pinecone index now contains {after_stats.total_vector_count} vectors")
    print(f"Processed file tracking updated. {len(processed_file_data)} new files tracked.")

if __name__ == "__main__":
    main() 