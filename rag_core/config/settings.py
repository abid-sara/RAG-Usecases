import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables
envpath = find_dotenv()
load_dotenv(envpath)

# API Configuration
API_KEY = os.environ.get('GEMINI_API_KEY', '')
MODEL_NAME = os.getenv('MODEL_NAME', 'gemini-1.5-flash')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_MODEL_NAME="gemini-2.0-flash"

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
JWT_TOKEN=os.environ.get('JWT_TOKEN', '')

# Search Configuration
TOP_N_RESULTS = int(os.getenv('TOP_N_RESULTS', 10))

SATIM_VECTOR_DB_PATH = os.getenv('SATIM_VECTOR_DB_PATH', 'data/vector_db_satim.faiss')
INTL_VECTOR_DB_PATH = os.getenv('INTL_VECTOR_DB_PATH', 'data/vector_db_international.faiss')

SATIM_DATA_PATH = os.getenv('SATIM_DATA_PATH', 'data/satim_chunks_cleaned.json')
INTL_DATA_PATH = os.getenv('INTL_DATA_PATH', 'data/pci_dss_chunks.json')


# Search Method Configuration
DEFAULT_SEARCH_METHOD = os.getenv('DEFAULT_SEARCH_METHOD', 'hybrid')

# Hybrid Search Configuration
TFIDF_WEIGHT = float(os.getenv('TFIDF_WEIGHT', 0.3))
BM25_WEIGHT = float(os.getenv('BM25_WEIGHT', 0.3))
EMBEDDING_WEIGHT = float(os.getenv('EMBEDDING_WEIGHT', 0.4))
EMBEDDING_MODEL = os.getenv('ENGLISH_EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')

# Flask Configuration
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'gemini')  

# DeepSeek Configuration
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'http://10.80.11.107:11434')
DEEPSEEK_MODEL_NAME = os.getenv('DEEPSEEK_MODEL_NAME', 'deepseek-r1:70b')

# Common LLM Settings
TEMPERATURE = float(os.getenv('TEMPERATURE', 0.7))
MAX_TOKENS = int(os.getenv('MAX_TOKENS', 2048))

MAX_CONVERSATION_LENGTH = 20  # Maximum number of messages to keep in history
CONVERSATION_EXPIRY_TIME = 3600  # Conversation expires after 1 hour of inactivity (in seconds)
