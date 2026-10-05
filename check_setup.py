from langchain_groq import ChatGroq
from tavily import TavilyClient
from pinecone import Pinecone

from app.config import GROQ_API_KEY, TAVILY_API_KEY, PINECONE_API_KEY, MODEL_NAME

# 1. Groq
llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY, max_retries=0)
print("GROQ SAYS:", llm.invoke("Say hello in one short sentence.").content)

# 2. Tavily
tavily = TavilyClient(api_key=TAVILY_API_KEY)
results = tavily.search("startup idea validation tools", max_results=3)
print("\nTAVILY FOUND:")
for r in results["results"]:
    print("-", r["title"])

# 3. Pinecone
if not PINECONE_API_KEY:
    print("\nPINECONE: no key found in .env")
else:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    print("\nPINECONE OK. Index count:", len(list(pc.list_indexes())))