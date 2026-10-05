import re
import unicodedata
from datetime import date


def today_note() -> str:
    """Tell the LLM today's date so it does not guess the year."""
    return f"Today's date is {date.today().strftime('%B %d, %Y')}.\n\n"


def clean_text(text: str) -> str:
    """Fix odd invisible characters that glue words together."""
    text = "".join(" " if unicodedata.category(c) == "Zs" else c for c in text)
    text = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff]", " ", text)
    text = re.sub(r"[\u2010-\u2012\u2212]", "-", text)
    text = re.sub(r"(?<=\S)[ \t]{2,}(?=\S)", " ", text)
    return text