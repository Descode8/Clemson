from typing import List
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.security import check_password_hash
import time, secrets
from utilities import config_utils, input_validation, openai_utils, mysql_utils, pinecone_utils, input_validation

# Create a Flask application instance
app = Flask(__name__)

# Flask requires a secret key to be set for session management.
secret_key = secrets.token_hex(16)  
mock_api_key = secrets.token_hex(32)
app.secret_key = secret_key

# Route to handle user login; initial and essential for proceeding (get proper info) | this is only a test function for now...
@app.route('/login', methods = ['GET', 'POST'])
def login_admin() -> str:
    """
    Summary:
        This route handles both GET and POST requests.
        For a GET request, it renders the login form.
        For a POST request (when the user submits the form), it retrieves the username and password from the form data.
        It checks if the provided credentials are valid by comparing the password hash with the stored hash for the given username.
        If the login is successful, it sets up the session, inserts a new customer into the database if they don't exist, and redirects to the /chat_log route.
        If the login fails, it renders the login page again with an error message.
    
    Args:
        None (GET request) or
        form['username'] (str): username address entered by the user.
        form['password'] (str): Password entered by the user.
    
    Returns:
        str: Rendered HTML template for the login page with appropriate response (success or error message).
    
    Render Condition:
        Always renders the login page.
    """
    if request.method == 'POST':
        # Retrieve the entered customer ID and password from the form data in login.html
        entered_customer_id = request.form['username']
        entered_password = request.form['password']
        
        # Retrieves the hashed password associated with the entered customer ID from the config_utils dictionary
        stored_password_hash = config_utils.customers.get(entered_customer_id)
        
        # Check if the entered customer ID matches any of the stored customer IDs
        if entered_customer_id not in config_utils.customers:
            # Render the login page again with an error message for invalid customer ID
            return render_template('login.html', error ="Invalid customer ID")
        
        # Check if the entered password matches the stored hashed password
        login_successful = stored_password_hash and check_password_hash(stored_password_hash, entered_password)
        
        if login_successful:
            # If login is successful, set the customer ID in the session and redirect to the chat_log route
            session['system_param_sent'] = 0
            session['customer_id'] = entered_customer_id
            return redirect(url_for('chat_log'))
        else:
            # If login is not successful due to incorrect password, render the login page again with an error message
            return render_template('login.html', error="Invalid password")
    else:
        # Render the login form for GET requests
        return render_template('login.html', admin = True)


# @app.route('/chat_log', methods = ['GET'])
# def chat_log() -> str:
#     """"
#     Summary:
#         This route handles GET requests to fetch and display chat logs for the logged-in customer.
    
#     Args:
#         None
    
#     Returns:
#         str: Rendered HTML template for the chat log page with fetched chat logs.
    
#     Render Condition:
#         Renders the chat log page when the user navigates to it.
#     """
#     # Query the insert_user_chat_interactions table to fetch the data
#     chat_logs: List[dict] = mysql_utils.get_chat_log(config_utils.CUSTOMER_ID)
#     # Render a template and pass the fetched data to it
#     return render_template('log.html', chat_logs = chat_logs)

@app.route('/chat_log', methods = ['GET'])
def chat_log() -> str:

    page = request.args.get('page', 1, type = int)
    per_page = request.args.get('per_page', 10, type = int)
    total, chat_logs = mysql_utils.get_paginated_chat_log(page, per_page)
    return render_template('log.html', chat_logs = chat_logs, total = total, page = page, per_page = per_page)

# Route to enter Witty Ai UI
@app.route('/chat', methods = ['POST'])
def chat() -> str:
    """
    Summary:
        This route handles POST requests for user chat interaction.
        It processes user queries, performs moderation and prompt injection checks, generates system parameters, interacts with the GPT model, and logs interactions in the database.
    Args:
        None
    
    Returns:
        str: JSON response containing the chatbot's response to the user query.
    
    Render Condition:
        Does not render any HTML page. Instead, returns JSON response for chat interaction.
    """
    # Get the user query from the request AND other variables for insert_chat_interactions
    config_utils.user_query = request.json.get('message')   
    customer_id = config_utils.CUSTOMER_ID
    user_ip_address = request.remote_addr
    request_timestamp = time.time()
    instructions = config_utils.SYSTEM_INSTRUCTIONS
    
    # # Check for SQL injection
    # if input_validation.sql_injection(config_utils.user_query):   
    #     response_timestamp = time.time()
    #     topic = "Malicious Input"
    #     message = "Malicious input detected. Request cannot be processed."
    #     mysql_utils.insert_user_chat_interactions(customer_id, user_ip_address, topic, instructions, config_utils.user_query, message, request_timestamp, response_timestamp)
    #     return jsonify({'response': message})
    # # Ensure token limit is valid
    # if input_validation.check_tokens(config_utils.user_query):
    #     response_timestamp = time.time()
    #     topic = "Exceeded Token Limit"
    #     message = (
    #                 "Your input is too long. Please shorten your query to under 200 characters and try again. "
    #                 "If necessary, consider breaking your input into multiple smaller queries."
    #     )
    #     mysql_utils.insert_user_chat_interactions(customer_id, user_ip_address, topic, instructions, config_utils.user_query, message, request_timestamp, response_timestamp)
    #     return jsonify({'response': message})
    # Perform moderation check
    prompt_not_flagged, moderation_message = openai_utils.moderate_prompt(config_utils.user_query)
    if not prompt_not_flagged:
        # Obtain instructions from MySQL database
        #instructions = mysql_utils.get_system_instructions(config_utils.customer_id) ---> to get instructions from MySQL DB
        response_timestamp = time.time()
        topic = "Flagged for Moderation"
        mysql_utils.insert_user_chat_interactions(customer_id, user_ip_address, topic, instructions, config_utils.user_query, moderation_message, request_timestamp, response_timestamp)
        return jsonify({'response': moderation_message})

    # Perform prompt injection check
    injection_status = openai_utils.check_prompt_injection(config_utils.user_query)
    if injection_status == 'Y':
        # Obtain instructions from MySQL database
        response_timestamp = time.time()
        topic = "Prompt Injection Detected"
        message = 'Prompt injection detected. Request cannot be processed.'
        mysql_utils.insert_user_chat_interactions(customer_id, user_ip_address, topic, instructions, config_utils.user_query, message, request_timestamp, response_timestamp)
        return jsonify({'response': message})
    
    # Obtain similarity strings from Pinecone index
    similarities = pinecone_utils.get_str_similarities()
    
    # Obtain instructions from MySQL database
    instructions = config_utils.SYSTEM_INSTRUCTIONS
    
    # Concatenate all components to form system_param
    #system_param = ' '.join(similarities) + ' ' + instructions + ' ' + config_utils.system_instruction_trail
    system_param = config_utils.instruction_Header + instructions +  config_utils.data_Header + ' '.join(similarities) + config_utils.user_Question_Header  + config_utils.user_query
    
    # Call openai_utils.chat_with_gpt with the user query and system_param
    response = openai_utils.chat_with_gpt(config_utils.user_query, system_param)
    
    response_timestamp = time.time()
    
    # Logic to give the unrelated response a topic to push to the log
    unrelated_response = 'My expertise is in providing information related to the Florida Department of Financial Services. Please ask another question.'
    if response == unrelated_response:
        topic = "Unrelated"
    else: 
        topic = pinecone_utils.get_topic(similarities[0].split(":")[0])
    
    if customer_id == 'demo@witty.ai':
        topic = "Witty AI Demo"
        
    #print(f"Topic: {topic}")
    # Log in insert_user_chat_interactions table
    mysql_utils.insert_user_chat_interactions(customer_id, user_ip_address, topic, instructions, config_utils.user_query, response, request_timestamp, response_timestamp)
    
    return jsonify({'response': response})

# Route to serve the frontend
@app.route('/', methods = ['GET'])
def chat_bot() -> None:
    """
    Summary:
        This route serves the frontend chatbot interface.
    
    Args:
        None
    
    Returns:
        None
    
    Render Condition:
        Renders the chatbot interface when the user navigates to it.
    """
    return render_template('chatbot.html')

