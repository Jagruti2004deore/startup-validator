import pytest

from app.llm_utils import (
    DailyLimitError, _call_with_wait, _is_daily_limit, _retry_after,
)


class FakeResult:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    """Returns or raises its outcomes in order; the last one repeats."""
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def invoke(self, prompt):
        self.calls += 1
        outcome = self.outcomes.pop(0) if len(self.outcomes) > 1 else self.outcomes[0]
        if isinstance(outcome, Exception):
            raise outcome
        return FakeResult(outcome)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    """Tests must not really wait."""
    monkeypatch.setattr("app.llm_utils.time.sleep", lambda seconds: None)


# ---------- reading the error text ----------
def test_retry_after_seconds():
    assert _retry_after(Exception("Please try again in 13.392s. Need more tokens?")) == 13.392


def test_retry_after_minutes_and_seconds():
    assert _retry_after(Exception("Please try again in 1m30s.")) == 90


def test_retry_after_milliseconds():
    assert _retry_after(Exception("Please try again in 250ms.")) == 0.25


def test_retry_after_missing():
    assert _retry_after(Exception("something else went wrong")) is None


def test_daily_limit_is_detected():
    daily = Exception("Rate limit reached ... on tokens per day (TPD): Limit 200000, Used 199185")
    minute = Exception("Rate limit reached ... on tokens per minute (TPM): Limit 8000, Used 7000")
    assert _is_daily_limit(daily) is True
    assert _is_daily_limit(minute) is False


# ---------- what the retry loop does ----------
def test_long_daily_limit_stops_at_once():
    error = Exception("Error code: 429 ... tokens per day (TPD) ... Please try again in 2h5m10s.")
    llm = FakeLLM([error])
    with pytest.raises(DailyLimitError):
        _call_with_wait(llm, "hello")
    assert llm.calls == 1


def test_per_minute_limit_is_waited_out():
    error = Exception("Error code: 429 ... tokens per minute (TPM) ... Please try again in 2s.")
    llm = FakeLLM([error, "ok"])
    assert _call_with_wait(llm, "hello") == "ok"
    assert llm.calls == 2


def test_daily_limit_with_short_hint_gives_up_after_four_tries():
    error = Exception("Error code: 429 ... tokens per day (TPD) ... Please try again in 13.392s.")
    llm = FakeLLM([error])
    with pytest.raises(DailyLimitError):
        _call_with_wait(llm, "hello")
    assert llm.calls == 4


def test_other_errors_are_not_retried():
    llm = FakeLLM([ValueError("boom")])
    with pytest.raises(ValueError):
        _call_with_wait(llm, "hello")
    assert llm.calls == 1