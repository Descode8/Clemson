from utilities import routes_utils
from utilities.embed_utils import generate_FAQ_embedding

# Generate FAQ Embeddings
#generate_FAQ_embedding()

# Run Witty AI Demo Application
if __name__ == '__main__':
    routes_utils.app.run(debug = True, host = '0.0.0.0')