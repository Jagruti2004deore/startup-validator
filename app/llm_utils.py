import json
import re
import time

from langchain_groq import ChatGroq
from pydantic import BaseModel

from app.config import GROQ_API_KEY, MODEL_NAME

DAILY_MESSAGE = (
    "The free daily token allowance for this Groq model is used up. "
    "Try again later, or set MODEL_NAME in .env to another model such as openai/gpt-oss-20b."
)


class DailyLimitError(RuntimeError):
    """The daily token allowance is used up. Waiting a minute will not help."""


def _is_rate_limit(error: Exception) -> bool:
    text = str(error).lower()
    return "429" in text or "rate limit" in text or "too many requests" in text


def _is_daily_limit(error: Exception) -> bool:
    text = str(error).lower()
    return "per day" in text or "(tpd)" in text or "(rpd)" in text


def _retry_after(error: Exception):
    """Seconds Groq asks us to wait ('try again in 13.392s', '1m30s', '250ms'), or None."""
    match = re.search(r"try again in\s+([0-9hms.]+)", str(error))
    if not match:
        return None
    seconds = {"ms": 0.001, "s": 1, "m": 60, "h": 3600}
    total, found = 0.0, False
    for value, unit in re.findall(r"(\d+(?:\.\d+)?)(ms|h|m|s)", match.group(1)):
        total += float(value) * seconds[unit]
        found = True
    return total if found else None


def _call_with_wait(llm, prompt: str, tries: int = 4) -> str:
    """Call the LLM. Per-minute limits are waited out. A daily limit stops the run."""
    for attempt in range(tries):
        try:
            return llm.invoke(prompt).content
        except Exception as e:
            if not _is_rate_limit(e):
                raise
            suggested = _retry_after(e)
            daily = _is_daily_limit(e)

            # a daily limit with a long wait cannot be fixed by waiting a minute
            if daily and (suggested is None or suggested > 120):
                raise DailyLimitError(DAILY_MESSAGE) from e

            # out of attempts
            if attempt == tries - 1:
                if daily:
                    raise DailyLimitError(DAILY_MESSAGE) from e
                raise

            wait = min(suggested + 1, 120) if suggested is not None else 20 * (attempt + 1)
            print(f"  (rate limit hit, waiting {wait:.0f}s - please do not stop)")
            time.sleep(wait)


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