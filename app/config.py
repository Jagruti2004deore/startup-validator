import os
from dotenv import load_dotenv

load_dotenv(override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # optional, not needed with Pinecone embeddings

# set MODEL_NAME in .env to switch models without editing code
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")
PINECONE_INDEX_NAME = "startup-validator"
DB_PATH = "validator.db"

# ---------- Pinecone memory (Phase 3) ----------
PINECONE_NAMESPACE = "founder"          # separates real memory from test data
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"           # the free plan supports this region
EMBED_MODEL = "llama-text-embed-v2"
EMBED_DIM = 1024

# ---------- Research limits (Phases 1 and 4) ----------
MAX_LOOPS = 2               # how many times the Critic can send work back
NUM_QUERIES = 3
RESULTS_PER_QUERY = 3       # web results per query
MAX_CHARS_PER_SOURCE = 500  # keeps prompts small, avoids rate limits
MAX_SOURCES_TOTAL = 30      # stop collecting after this many sources
MAX_PER_DOMAIN = 2          # no single website can dominate
GAP_ROUND_MAX_QUERIES = 4   # queries in a re-research round
MIN_MEMORY_SCORE = 0.3      # ignore past notes less similar than this (tune from Phase 3 scores)

# sites we never want as sources
EXCLUDE_DOMAINS = ["youtube.com", "facebook.com", "instagram.com",
                   "tiktok.com", "pinterest.com", "quora.com", "reddit.com"]

# ---------- Analyst (Phase 5) ----------
ANALYST_BATCH_SIZE = 10     # sources read per LLM call
MAX_CLAIMS_PER_BATCH = 8

# ---------- Critic (Phase 6) ----------
# how many verified claims each angle needs before it counts as covered
MIN_VERIFIED = {
    "competitor": 3,
    "pricing": 2,
    "market_size": 1,
    "demand_signal": 1,
    "recent_activity": 1,
    "failure_or_risk": 1,
}
MAX_SOURCES_PER_CLAIM = 3

# ---------- Scoring (Phase 7) ----------
MIN_EVIDENCE_FOR_VERDICT = 4   # fewer verified checklist items than this = "Unclear"
CROWDED_MEDIUM = 3             # distinct competitors: 3 or more = medium
CROWDED_HIGH = 7               # 7 or more = high

# ---------- API (Phase 10) ----------
APP_API_KEY = os.getenv("APP_API_KEY", "")                  # empty = no key needed (local use)
MAX_RUNS_PER_DAY = int(os.getenv("MAX_RUNS_PER_DAY", "20"))
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:8501",
).split(",")

if not GROQ_API_KEY or not TAVILY_API_KEY:
    raise ValueError("Missing GROQ_API_KEY or TAVILY_API_KEY. Check your .env file.")