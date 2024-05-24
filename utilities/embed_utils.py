from utilities import config_utils, pinecone_utils
from typing import List
import pandas as pd, json, requests

def generate_user_query_embedding(user_query: str) -> List[float]:
    """
    Generate embedding for user query using OpenAI API.

    Args:
    - user_query (str): User's query text.

    Returns:
    - List[float]: Embedding vector for the user query.
    """
    headers: dict = {
        'Content-Type': 'application/json',  
        'Authorization': f'Bearer {config_utils.openai_api_key}'
    }
    
    data: dict = {
        'input': user_query,  
        'model': config_utils.EMBEDDING_MODEL  
    }
    
    with requests.Session() as session:  
        response = session.post(  
            'https://api.openai.com/v1/embeddings',  
            headers = headers,  
            data = json.dumps(data)  
        )
    
    response.raise_for_status()  
    
    embeddings: List[float] = response.json()['data'][0]['embedding']  
    return [float(num) for num in embeddings]  


def generate_FAQ_embedding() -> None:
    """
    Generates embeddings for frequently asked questions (FAQs) using an embedding model specified in the configuration.
    Reads a CSV file containing FAQs, sends each FAQ to the OpenAI API to generate embeddings, and saves the resulting 
    embeddings alongside the original FAQs in a new CSV file named 'config_utils.DATA_EMBEDDING_CSV'.
    
    Args: 
        - None
    Returns:
        - None
    """
    # Read the FAQs CSV file into a DataFrame
    df: pd.DataFrame = pd.read_csv(config_utils.DATA_CSV)
    
    # Define headers for the HTTP request to the OpenAI API
    headers: dict = {
        'Content-Type': 'application/json',  
        'Authorization': f'Bearer {config_utils.openai_api_key}'  
    }
    
    # Create a list of dictionaries containing each FAQ and the specified embedding model
    data_list: List[dict] = [{'input': faq_text, 'model': config_utils.EMBEDDING_MODEL} for faq_text in df.iloc[:, 0]]
    
    # Send HTTP POST requests to the OpenAI API to generate embeddings for each FAQ
    with requests.Session() as session:  
        responses = [session.post(  
            'https://api.openai.com/v1/embeddings',  
            headers = headers,  
            data = json.dumps(data)  
            ) for data in data_list
        ]
    
    # Check for any errors in the HTTP responses
    for response in responses:  
        response.raise_for_status()  
    
    # Extract the embedding vectors from the JSON responses and convert them to strings
    new_embeddings: List[str] = [
        json.dumps([float(num) for num in response.json()['data'][0]['embedding']])  
        for response in responses  
    ]
    
    # Add the embedding vectors to the DataFrame
    df['Embedding_Vector'] = new_embeddings  
    
    # Save the DataFrame to a new CSV file
    df.to_csv(config_utils.DATA_EMBEDDING_CSV , index = False)
    
    # Upsert the new embeddings into the Pinecone index
    pinecone_utils.upsert_data()
