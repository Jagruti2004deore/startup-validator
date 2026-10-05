import os
from dotenv import load_dotenv

load_dotenv(override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")  # used from Phase 3
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")      # optional, only if we pick OpenAI embeddings

MODEL_NAME = "openai/gpt-oss-120b"
PINECONE_INDEX_NAME = "startup-validator"

DB_PATH = "validator.db"

# agent limits (we tune these later)
MAX_LOOPS = 2               # how many times the Critic can send work back
NUM_QUERIES = 3             # search queries per round
RESULTS_PER_QUERY = 3       # web results per query
MAX_CHARS_PER_SOURCE = 500  # keeps prompts small, avoids rate limits

if not GROQ_API_KEY or not TAVILY_API_KEY:
    raise ValueError("Missing GROQ_API_KEY or TAVILY_API_KEY. Check your .env file.")