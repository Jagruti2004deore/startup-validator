import pytest
from fastapi.testclient import TestClient

from app import api, db
from app.llm_utils import DailyLimitError

IDEA = "A study-buddy app that matches college students in India into small groups."


def fake_validator(run_id, idea):
    """Stands in for the real agent: writes two events and finishes."""
    db.add_event(run_id, "intake", "fake step one")
    db.add_event(run_id, "finish", "fake step two")
    db.update_run(run_id, status="done", verdict="Promising", evidence_score=7, report_md="# Fake report")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(api, "APP_API_KEY", "")
    monkeypatch.setattr(api, "MAX_RUNS_PER_DAY", 100)
    monkeypatch.setattr(api, "run_validator", fake_validator)
    with TestClient(api.app) as test_client:
        yield test_client


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_short_idea_is_rejected(client):
    assert client.post("/validate", json={"idea": "too short"}).status_code == 422


def test_validate_runs_in_background_and_finishes(client):
    response = client.post("/validate", json={"idea": IDEA})
    assert response.status_code == 202
    run_id = response.json()["run_id"]
    status = client.get(f"/runs/{run_id}").json()
    assert status["status"] == "done"
    assert status["verdict"] == "Promising"
    assert [e["node"] for e in status["events"]] == ["intake", "finish"]


def test_events_can_be_fetched_after_an_id(client):
    run_id = client.post("/validate", json={"idea": IDEA}).json()["run_id"]
    events = client.get(f"/runs/{run_id}").json()["events"]
    later = client.get(f"/runs/{run_id}", params={"after": events[0]["id"]}).json()["events"]
    assert [e["node"] for e in later] == ["finish"]


def test_report_endpoint_returns_claims_and_sources(client):
    run_id = db.create_run(IDEA)
    db.save_sources(run_id, [{"url": "https://example.com/a", "title": "A", "content": "x"}])
    db.save_claims(
        run_id,
        [{"text": "Alpha offers groups", "category": "competitor", "source_ids": [1]}],
        [{"text": "Alpha charges $49", "category": "pricing", "source_ids": [1],
          "reason": "number_not_in_source: 49"}],
    )
    db.update_run(run_id, status="done", verdict="Promising", evidence_score=7, report_md="# R")
    data = client.get(f"/runs/{run_id}/report").json()
    assert data["report_md"] == "# R"
    assert [c["text"] for c in data["verified"]] == ["Alpha offers groups"]
    assert data["dropped"][0]["drop_reason"].startswith("number_not_in_source")
    assert data["sources"][0]["url"] == "https://example.com/a"


def test_report_for_unknown_run_is_404(client):
    assert client.get("/runs/doesnotexist/report").status_code == 404


def test_report_while_running_is_409(client):
    run_id = db.create_run(IDEA)  # a new run starts as 'running'
    assert client.get(f"/runs/{run_id}/report").status_code == 409


def test_only_one_run_at_a_time(client):
    db.create_run(IDEA)  # still running
    assert client.post("/validate", json={"idea": IDEA}).status_code == 409


def test_daily_budget_is_enforced(client, monkeypatch):
    monkeypatch.setattr(api, "MAX_RUNS_PER_DAY", 1)
    run_id = db.create_run(IDEA)
    db.update_run(run_id, status="done")
    assert client.post("/validate", json={"idea": IDEA}).status_code == 429


def test_api_key_is_required_when_set(client, monkeypatch):
    monkeypatch.setattr(api, "APP_API_KEY", "secret")
    assert client.get("/runs").status_code == 401
    assert client.get("/runs", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/runs", headers={"X-API-Key": "secret"}).status_code == 200
    assert client.get("/health").status_code == 200  # health never needs a key


def test_daily_token_limit_marks_the_run_failed(client, monkeypatch):
    def boom(run_id, idea):
        raise DailyLimitError("limit")

    monkeypatch.setattr(api, "run_validator", boom)
    run_id = client.post("/validate", json={"idea": IDEA}).json()["run_id"]
    status = client.get(f"/runs/{run_id}").json()
    assert status["status"] == "failed"
    assert any("limit" in e["message"].lower() for e in status["events"])


def test_stale_runs_are_failed_on_startup(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "stale.db"))
    db.init_db()
    run_id = db.create_run(IDEA)  # left 'running', as after a crash
    with TestClient(api.app):
        pass
    assert db.get_run(run_id)["status"] == "failed"


def test_notes_roundtrip(client, monkeypatch):
    monkeypatch.setattr(api, "add_note", lambda text: 2)  # no Pinecone call
    assert client.post("/notes", json={"text": "I dislike crowded markets"}).status_code == 201
    db.add_note("saved note")
    assert any(n["text"] == "saved note" for n in client.get("/notes").json())