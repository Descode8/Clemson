import mysql.connector, mysql.connector.pooling
from datetime import datetime
from utilities import config_utils

def insert_user_chat_interactions(interaction_id: int, user_ip_address: str, topic: str, system_request: str, request: str, response: str, request_timestamp: float, response_timestamp: float) -> None:
    """
    Insert chat interaction data into the database.

    Args:
    - interaction_id (int): Customer ID.
    - user_ip_address (str): User's IP address.
    - topic (str): Topic extracted from top most similar FAQ.
    - system_request (str): System's instructions.
    - request (str): User's request.
    - response (str): System's response.
    - request_timestamp (float): Timestamp of the request.
    - response_timestamp (float): Timestamp of the response.

    Returns:
    - None
    """
    try:
        connection = config_utils.cnxpool.get_connection()
        with connection:
            with connection.cursor() as cursor:
                sql = """
                INSERT INTO user_chat_interactions (
                    customer_id,
                    user_ip_address,
                    topic,
                    system_request,
                    request,
                    response,
                    request_timestamp,
                    response_timestamp
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                # Convert timestamps to datetime format
                request_timestamp = datetime.fromtimestamp(request_timestamp)
                response_timestamp = datetime.fromtimestamp(response_timestamp)

                interaction_data = (
                    interaction_id,           
                    user_ip_address, 
                    topic,  
                    system_request,    
                    request,          
                    response,         
                    request_timestamp,     
                    response_timestamp     
                )

                cursor.execute(sql, interaction_data)
                connection.commit()

    except mysql.connector.Error as e:
        print(f"Error while connecting to MySQL: {e}")

def get_system_instructions(customer_id: str) -> str:
    """
    Retrieve system instructions for a given customer ID from the database.

    Args:
    - customer_id (int): Customer ID.

    Returns:
    - str: System instructions for the customer.
    """
    try:
        connection = config_utils.cnxpool.get_connection()
        with connection:
            with connection.cursor() as cursor:
                sql = """
                SELECT system_instructions
                FROM customer
                WHERE customer_id = %s
                """
                cursor.execute(sql, (customer_id,))
                result = cursor.fetchone()
                return result[0] if result else None
    except mysql.connector.Error as e:
        print(f"Error while connecting to MySQL: {e}")
        
def get_chat_log(customer_id: str) -> list[dict]:
    try:
        connection = config_utils.cnxpool.get_connection()
        with connection:
            # Make sure to use a dictionary cursor here
            with connection.cursor(dictionary = True) as cursor:
                sql = """
                        SELECT *
                        FROM user_chat_interactions
                        WHERE customer_id = %s
                        """
                cursor.execute(sql, (customer_id,))
                # This will fetch rows as dictionaries
                chat_logs = cursor.fetchall()
                return chat_logs if chat_logs else []
    except mysql.connector.Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return []

def get_paginated_chat_log(page, per_page):
    """
    Fetch a paginated list of chat logs from the database using an established connection pool.

    Args:
    - page (int): Current page number.
    - per_page (int): Number of records per page.

    Returns:
    - total (int): Total number of chat logs.
    - chat_logs (list): List of chat logs for the current page.
    """
    try:
        # Get a connection from the connection pool
        connection = config_utils.cnxpool.get_connection()
        with connection:
            with connection.cursor(dictionary=True) as cursor:
                # Calculate the starting index
                start = (page - 1) * per_page

                # Retrieve the subset of chat logs
                cursor.execute("""
                    SELECT *
                    FROM user_chat_interactions
                    LIMIT %s OFFSET %s
                """, (per_page, start))
                chat_logs = cursor.fetchall()

                # Count the total number of entries
                cursor.execute("SELECT COUNT(*) FROM user_chat_interactions")
                total = cursor.fetchone()['COUNT(*)']

                return total, chat_logs

    except mysql.connector.Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return 0, []  # In case of an error, return empty data.