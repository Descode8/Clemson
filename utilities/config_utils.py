import os, mysql.connector, mysql.connector.pooling
from openai import OpenAI
from werkzeug.security import generate_password_hash
from datetime import datetime

# Customer vars
current_date = datetime.now().strftime('"%A, %B %d, %Y"')
user_query: str = ''
userQueryCache: dict = {}
CLIENT_INDEX: str = 'summer2024'
DATA_CSV: str = 'summer2024.csv'#'demo.csv'
CSV_COLUMN_NAME: str = 'School Material'
DATA_EMBEDDING_CSV: str = 'summer2024_embeddings.csv'

# OpenAI API configuration
openai_api_key: str = os.getenv('OPENAI_API_KEY')
openai_org_key: str = os.getenv('ORG_KEY')
MODERATION_API_ENDPOINT: str = 'https://api.openai.com/v1/moderations'
EMBEDDING_MODEL: str = "text-embedding-3-small"
GPT_MODEL: str =  "gpt-4o" #"gpt-4-1106-preview" #"gpt-3.5-turbo-0125" #"gpt-4-turbo" 
NUM_OF_SIMILARITIES: int = 5
OUT_TOKEN_LIMIT: int = 150
IN_TOKEN_LIMIT: int = 100
TEMP_SET: int = 0

SYSTEM_INSTRUCTIONS: str = f"""
                            It is important that you know the current date of today which is {current_date}.
                            Interperet 'this week' as the week that {current_date} is in. 
                            Many questions will be based on the most current assignments.
                            Limit reponses to {OUT_TOKEN_LIMIT} tokens. 
                            Use bold letters and unordered lists for a better user experience.
                            Put a newline before and after each list so that the list has space above and below it to stand out.\n
                            
                            "Weekly Schedule: Week 1: Part I: Web Application Basics Date: May 14 - 18 Topic: Syllabus + Course Intro, Understanding How the Web Works, User Interface Design Readings: Syllabus, SAMS Book Chapter 1, DMMT Book: Introduction Assignments: SAMS CH01 Quiz, DMMT Intro Quiz, Prog01-Web Host, VQ's, Syllabus Quiz"
                            "Weekly Schedule: Week 2: Part: I Web Application Basics Date: May 20 - 25 Topic: Structuring HTML and Using CSS, Understanding the CSS Box Model and Positioning, Don't Make Me Think Readings: SAMS Book Chapter 2, SAMS Book Chapter 3, DMMT Book: Chapter 1 Assignments: SAMS CH02 Quiz, SAMS CH03 Quiz, DMMT Ch01 Quiz, Prog02 - HTML & CSS, Prog03 - CSS Layout, VQ's"
                            "Weekly Schedule: Week 3: Part: II Getting Started with Dynamic Websites Date: May 27 - June 1 Topic: Introducing Javascript, Introducing PHP, How We Use the Web Readings: SAMS Book Chapter 4, SAMS Book Chapter 5, DMMT Book: Chapter 2 Assignments: SAMS CH04 Quiz, SAMS CH05 Quiz, DMMT Ch02 Quiz, Prog04 - Javascript Events, Prog05 - PHP HelloWorld, VQ's"
                            "Weekly Schedule: Week 4: Part: II Getting Started with Dynamic Websites Date: June 3 - 8 Topic: Understanding Dynamic Websites and HTML5 Applications, Javascript Fundamentals: Variables, Strings, Arrays, Billboard Design 101 Readings: SAMS Book Chapter 6, SAMS Book Chapter 7, DMMT Book: Chapter 3 Assignments: SAMS CH06 Quiz, SAMS CH07 Quiz, DMMT Ch03 Quiz, Prog06 - Moving Buttons, Prog07 - Javascript Sort, SAMS Exam 1 (chapters 1-5), VQ's"
                            "Weekly Schedule: Week 5: Part: II Getting Started with Dynamic Websites Date: June 10 - 15 Topic: Javascript Fundamentals: Functions, Objects, Flow Control, Javascript Event Handling, Animal, Vegetable or Mineral Readings: SAMS Book Chapter 8, SAMS Book Chapter 9, DMMT Book: Chapter 4 Assignments: SAMS CH08 Quiz, SAMS CH09 Quiz, DMMT Ch04 Quiz, Prog08 - Card Object, Prog09 - Keypress, VQ's, Program Exam 1"
                            "Weekly Schedule: Week 6: Part: Summer Break Date: June 17 - 22"
                            "Weekly Schedule: Week 7: Part: III Taking Your Web Applications to the Next Level Date: June 24 - 29 Topic: The Basics of jQuery, Omit Words, Street Signs and Breadcrumbs, Big Bang Theory Readings: SAMS Book Chapter 10, DMMT Book: Chapter 5, Chapter 6, Chapter 7 Assignments: SAMS CH10 Quiz, DMMT Ch05 Quiz, DMMT Ch06 Quiz, DMMT Ch07 Quiz, Prog10 - Same Menu, Prog11 - jQuery, jQuery Quiz, Ch10 Source Code Quiz"
                            "Weekly Schedule: Week 8: Part: III Taking Your Web Applications to the Next Level Date: July 1 - 6 Topic: AJAX: Remote Scripting, PHP Fundamentals: Variables, Strings, Arrays, The Farmer and Cowman, Usability Testing Readings: SAMS Book Chapter 11, SAMS Book Chapter 12, DMMT Book: Chapter 8, Chapter 9 Assignments: SAMS CH11 Quiz, SAMS CH12 Quiz, DMMT Ch08 Quiz, DMMT Ch09 Quiz, Ch11 Source Code Quiz, Prog12 - AJAX & PHP, Project 1"
                            "Weekly Schedule: Week 9: Part: III Taking Your Web Applications to the Next Level Date: July 8 - 13 Topic: PHP Fundamentals: Functions, Objects, Flow Control, Cookies & User Sessions, Web Forms Readings: SAMS Book Chapter 13, SAMS Book Chapter 14, SAMS Book Chapter 15 Assignments: SAMS CH13 Quiz, SAMS CH14 Quiz, SAMS CH15 Quiz, Prog13 - Ajax & Handlebars, Prog14 - PHP File I/O, SAMS Exam 2 (chapters 6-13)"
                            "Weekly Schedule: Week 10: Part: IV Integrating a Database into Your Application Date: July 15 - 20 Topic: Database Design, Basic SQL Commands Readings: SAMS Book Chapter 16, SAMS Book Chapter 17 Assignments: Project 2, Program Exam 2"
                            "Weekly Schedule: Week 11: Part: IV Integrating a Database into Your Application Date: July 22 - 27 Topic: MySQL & PHP, Mobile, Usability Readings: SAMS Book Chapter 18, DMMT Book: Chapter 10, Chapter 11 Assignments: Database Quiz, DMMT Ch10 Quiz, Prog15 - Usability"
                            "Weekly Schedule: Week 12: Part: IV Integrating a Database into Your Application Date: July 29 - Aug 3 Topic: Accessibility, Guide for the Perplexed Readings: DMMT Book: Chapter 12, Chapter 13 Assignments: Project 3"
                            "Weekly Schedule: Week 13: Part: Final Exam Section Date: Aug 5 Assignments: SAMS Final Exam, DMMT Final Exam"
                        """

# System Parameters
instruction_Header: str = 'Follow these instructions and answer with data below\n'
data_Header: str = '\n\nAnswer the question using this data\n'
user_Question_Header: str = '\n\nAnswer this question\n'
system_instruction_trail: str = 'Based on this information only, answer the user\'s question.'

# Store customer credentials for authentication purposes in the Flask application
CUSTOMER_ID = 'demo@witty.ai'
PASSWORD = 'witty'

# User email/password in Flask POST matches the chatbot DB
customers: dict = {
    CUSTOMER_ID: generate_password_hash(PASSWORD)
}

# Database configuration
db_password: str = os.getenv('DB_PASS')
db_host: str = '127.0.0.1'
db_user: str = 'root'
db_database: str = 'chatbot'

# Establish database connection pool
dbconfig: dict = {
    "host": db_host,
    "user": db_user,
    "password": db_password,
    "database": db_database
}
cnxpool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name = "SQLPool",
    pool_size = 32,
    **dbconfig
)

# Pinecone API configuration
pinecone_api_key: str = os.getenv('PINECONE_API_KEY')
client: OpenAI = OpenAI(
    organization = openai_org_key,
    api_key = openai_api_key
)

# Check for required configuration
if not all([openai_api_key, openai_org_key, pinecone_api_key, db_host, db_user, db_password, db_database]):
    raise ValueError("Required API keys or database credentials are not set in environment variables.")
