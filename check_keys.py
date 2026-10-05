from app.config import GROQ_API_KEY, TAVILY_API_KEY, PINECONE_API_KEY

for name, key in [("GROQ", GROQ_API_KEY), ("TAVILY", TAVILY_API_KEY), ("PINECONE", PINECONE_API_KEY)]:
    if not key:
        print(name, "-> MISSING")
        continue
    print(name, "-> length:", len(key),
          "| starts with:", key[:4],
          "| has space:", " " in key,
          "| has quote:", '"' in key or "'" in key)