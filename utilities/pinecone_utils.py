from utilities import config_utils, embed_utils
from pinecone import Pinecone
from typing import List
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests
from requests.exceptions import ChunkedEncodingError

# Initialize Pinecone Client & upsert data
pc = Pinecone(api_key=config_utils.pinecone_api_key)
index = pc.Index(config_utils.CLIENT_INDEX)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), retry=(retry_if_exception_type(ChunkedEncodingError) | retry_if_exception_type(requests.exceptions.RequestException)))
def post_request(session, url, data, headers):
    response = session.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response

def generate_FAQ_embedding():
    session = requests.Session()
    df = pd.read_csv(config_utils.DATA_EMBEDDING_CSV)
    responses = [post_request(session, "your_api_url", {"text": row[config_utils.CSV_COLUMN_NAME]}, {"Authorization": f"Bearer {config_utils.your_api_key}"}) for _, row in df.iterrows()]
    return responses

def upsert_data() -> None:
    """
    Upsert embedding vectors into the Pinecone index with associated metadata.
    
    Reads embedding vectors from a CSV file, prepares them for upsert, 
    converts them to lists, associates metadata (original text) with each vector,
    and finally upserts them into the Pinecone index.
    """
    # Load the .csv file into a DataFrame
    df = pd.read_csv(config_utils.DATA_EMBEDDING_CSV)

    # Prepare the vectors and metadata for upsert
    vectors_with_metadata = []
    for idx, row in df.iterrows():
        id: str = str(idx)
        # Remove the square brackets and then split the string into a list of strings
        embedding_vector: List[float] = row['Embedding_Vector'][1:-1].split(',')
        # Convert each string in the list to a float
        embedding_vector = [float(x) for x in embedding_vector]
        original_text: str = row[config_utils.CSV_COLUMN_NAME]
        
        vectors_with_metadata.append({
            "id": id,
            "values": embedding_vector,
            "metadata": {"original_text": original_text}
        })

    # Function to estimate the size of each vector and its metadata
    def get_vector_size(vector):
        return sum(len(str(v)) for v in vector["values"]) + len(vector["metadata"]["original_text"])

    # Define the maximum size of each chunk (in bytes)
    max_chunk_size = 4 * 1024 * 1024  # 4 MB
    current_chunk = []
    current_chunk_size = 0

    # Split the data into chunks
    for vector in vectors_with_metadata:
        vector_size = get_vector_size(vector)
        if current_chunk_size + vector_size > max_chunk_size:
            # If adding this vector exceeds the max chunk size, upsert the current chunk and start a new one
            index.upsert(vectors=current_chunk)
            current_chunk = [vector]
            current_chunk_size = vector_size
        else:
            # Otherwise, add the vector to the current chunk
            current_chunk.append(vector)
            current_chunk_size += vector_size

    # Upsert the last chunk if it's not empty
    if current_chunk:
        index.upsert(vectors=current_chunk)

# Call the function to upsert data
upsert_data()

def get_str_similarities() -> List[str]:
    """
    Get the original texts of similar vectors from the Pinecone index.

    Generates embedding vectors for the user query, queries the Pinecone index
    for similar vectors, and returns a list of strings representing the original
    texts associated with the similar vectors.
    """
    user_query_vectors: List[float] = embed_utils.generate_user_query_embedding(config_utils.user_query)

    query_result = index.query(
        vector=user_query_vectors,  # The vector being compared to stored vectors in the Pinecone index
        top_k=config_utils.NUM_OF_SIMILARITIES,
        include_metadata=True  # Ensuring metadata is included in the query results
    )

    # Extract the original texts from the metadata of similar vectors
    original_texts: List[str] = [match.get("metadata", {}).get("original_text", "") for match in query_result.get("matches", [])]

    return original_texts

def get_topic(topic: str) -> str:
    return topic  # Return the topic (you might want to implement more logic here)
