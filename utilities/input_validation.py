import re, logging
from utilities import config_utils
from transformers import GPT2Tokenizer

# SQL injection function
def sql_injection(user_query) -> bool:
    # List of SQL keywords
    sql_keywords = [
        "SELECT", "INSERT", "UPDATE", "DELETE", "FROM", "WHERE", "JOIN", "INNER JOIN",
        "LEFT JOIN", "RIGHT JOIN", "FULL JOIN", "GROUP BY", "ORDER BY", "HAVING", "UNION",
        "UNION ALL", "LIMIT", "OFFSET", "DISTINCT", "ALTER", "DROP", "CREATE", "INDEX",
        "TRIGGER", "VIEW", "IN", "BETWEEN", "LIKE", "CASE", "EXISTS", "NULL", "AND", "OR", "NOT"
    ]

    # Creating a regex pattern to detect SQL keywords
    # Join the keywords with '|', escape keywords with spaces, and add word boundaries (\b) to ensure full-word matching
    regex_pattern = r'\b(' + '|'.join(re.escape(keyword) for keyword in sql_keywords) + r')\b'

    # Compile the regex pattern with case-insensitive flag
    pattern = re.compile(regex_pattern, re.IGNORECASE)
    
    return pattern.search(user_query)
    
# Exceeded number of chars function
def check_tokens(user_query) -> bool:
    # Suppress warnings and reduce log verbosity
    logging.getLogger().setLevel(logging.ERROR)

    # Initialize the tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    
    # Count tokens
    token_count = len(tokenizer.encode(user_query))
    
    return token_count > config_utils.IN_TOKEN_LIMIT

# Code injection function   
def code_injection(user_query) -> bool:
    # List of code keywords
    code_keywords = [
        "import", "from", "def", "class", "for", "while", "if", "elif", "else", "try", "except",
        "finally", "raise", "assert", "return", "yield", "with", "as", "lambda", "global", "nonlocal",
        "del", "pass", "continue"
        ]