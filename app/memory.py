import time
import uuid
from datetime import datetime

from pinecone import Pinecone, ServerlessSpec
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app import db
from app.config import (
    PINECONE_API_KEY, PINECONE_INDEX_NAME, PINECONE_NAMESPACE,
    PINECONE_CLOUD, PINECONE_REGION, EMBED_MODEL, EMBED_DIM,
)

_pc = None
_index = None

# Long notes are cut into overlapping pieces so each piece keeps its meaning
_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)


# ---------- helpers ----------
def _get(obj, key):
    """Read a field whether the SDK returns an object or a dictionary."""
    try:
        return obj[key]
    except Exception:
        return getattr(obj, key, None)


def _client() -> Pinecone:
    global _pc
    if _pc is None:
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is missing. Check your .env file.")
        _pc = Pinecone(api_key=PINECONE_API_KEY)
    return _pc


def _is_ready(pc: Pinecone, name: str) -> bool:
    status = pc.describe_index(name).status
    ready = _get(status, "ready")
    return bool(ready)


def get_index():
    """Return the Pinecone index. Create it the first time (takes about 30 seconds)."""
    global _index
    if _index is not None:
        return _index

    pc = _client()
    existing = [i.name for i in pc.list_indexes()]
    if PINECONE_INDEX_NAME not in existing:
        print(f"Creating Pinecone index '{PINECONE_INDEX_NAME}' (dimension {EMBED_DIM})...")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
        )
        while not _is_ready(pc, PINECONE_INDEX_NAME):
            time.sleep(2)
        print("Index is ready.")
    _index = pc.Index(PINECONE_INDEX_NAME)
    return _index


def embed_texts(texts: list, input_type: str) -> list:
    """Turn texts into vectors. input_type is 'passage' to store, 'query' to search."""
    pc = _client()
    vectors = []
    for start in range(0, len(texts), 90):          # the model accepts small batches
        batch = texts[start:start + 90]
        result = pc.inference.embed(
            model=EMBED_MODEL,
            inputs=batch,
            parameters={"input_type": input_type, "truncate": "END"},
        )
        items = getattr(result, "data", result)
        for item in items:
            values = _get(item, "values")
            vectors.append(list(values))
    return vectors


# ---------- store ----------
def add_note(text: str, namespace: str = PINECONE_NAMESPACE, save_to_db: bool = True) -> int:
    """Save a founder note. Returns how many chunks were stored in Pinecone."""
    text = text.strip()
    if not text:
        raise ValueError("Note is empty.")

    note_id = uuid.uuid4().hex[:8]
    chunks = _splitter.split_text(text) or [text]
    vectors = embed_texts(chunks, "passage")
    created = datetime.now().isoformat(timespec="seconds")

    records = [
        {
            "id": f"note-{note_id}-{i}",
            "values": vec,
            "metadata": {"text": chunk, "type": "note", "created_at": created},
        }
        for i, (chunk, vec) in enumerate(zip(chunks, vectors))
    ]
    get_index().upsert(vectors=records, namespace=namespace)

    if save_to_db:
        db.add_note(text, pinecone_id=f"note-{note_id}")
    return len(records)


def save_report_summary(run_id: str, idea_text: str, verdict: str, summary: str,
                        namespace: str = PINECONE_NAMESPACE) -> None:
    """Store a finished run, so the agent can recall it next time."""
    text = f"Past validation. Idea: {idea_text}\nVerdict: {verdict}\nSummary: {summary}"
    vec = embed_texts([text], "passage")[0]
    get_index().upsert(
        vectors=[{
            "id": f"report-{run_id}",
            "values": vec,
            "metadata": {"text": text[:3000], "type": "report",
                         "created_at": datetime.now().isoformat(timespec="seconds")},
        }],
        namespace=namespace,
    )


# ---------- recall ----------
def search_memory(query: str, top_k: int = 3, min_score: float = 0.0,
                  namespace: str = PINECONE_NAMESPACE) -> list:
    """Find the closest past notes and reports. Returns [{text, score, type}]."""
    qvec = embed_texts([query], "query")[0]
    res = get_index().query(
        vector=qvec, top_k=top_k, include_metadata=True, namespace=namespace
    )
    matches = _get(res, "matches") or []
    found = []
    for m in matches:
        score = _get(m, "score") or 0.0
        meta = _get(m, "metadata") or {}
        if score >= min_score:
            found.append({
                "text": meta.get("text", ""),
                "score": round(float(score), 3),
                "type": meta.get("type", "note"),
            })
    return found


def clear_namespace(namespace: str) -> None:
    """Delete everything in one namespace. Used to clean up test data."""
    try:
        get_index().delete(delete_all=True, namespace=namespace)
    except Exception:
        pass  # the namespace was already empty or did not exist