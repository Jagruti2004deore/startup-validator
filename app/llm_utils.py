from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY, MODEL_NAME

import json
import re
import time
from pydantic import BaseModel


def _is_rate_limit(error: Exception) -> bool:
    text = str(error).lower()
    return "429" in text or "rate limit" in text or "too many requests" in text


def _call_with_wait(llm, prompt: str, tries: int = 4) -> str:
    """Call the LLM. If Groq says 'too many requests', wait and try again."""
    for attempt in range(tries):
        try:
            return llm.invoke(prompt).content
        except Exception as e:
            if _is_rate_limit(e) and attempt < tries - 1:
                wait = 20 * (attempt + 1)
                print(f"  (rate limit hit, waiting {wait}s - please do not stop)")
                time.sleep(wait)
                continue
            raise


def ask_text(llm, prompt: str) -> str:
    """Plain text answer, with rate-limit waiting."""
    return _call_with_wait(llm, prompt)


def ask_structured(llm, prompt: str, model: type[BaseModel], tries: int = 3):
    """Ask the LLM a question and get back a filled-in Pydantic form."""
    schema = json.dumps(model.model_json_schema())
    full_prompt = (
        f"{prompt}\n\n"
        f"Respond with ONLY valid JSON that matches this schema. "
        f"No explanation, no markdown fences.\n{schema}"
    )
    last_error = None
    for _ in range(tries):
        text = _call_with_wait(llm, full_prompt)
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            return model.model_validate_json(match.group(0))
        except Exception as e:
            last_error = e  # bad JSON, so ask again
    raise ValueError(f"LLM did not return valid JSON after {tries} tries: {last_error}")

_llm = None


def get_llm():
    """One shared LLM object. max_retries=0 because we handle rate limits ourselves."""
    global _llm
    if _llm is None:
        _llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY, max_retries=0)
    return _llm