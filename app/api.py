import hmac
import threading
from contextlib import asynccontextmanager
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from app import db
from app.config import ALLOWED_ORIGINS, APP_API_KEY, MAX_RUNS_PER_DAY, MODEL_NAME
from app.graph import run_validator
from app.llm_utils import DailyLimitError
from app.memory import add_note

_start_lock = threading.Lock()  # makes "check, then create the run" one step


# ---------------------------------------------------------------------------
# Small database helpers
# ---------------------------------------------------------------------------

def _running_count() -> int:
    with db.get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM runs WHERE status = 'running'").fetchone()[0]


def _runs_today() -> int:
    prefix = date.today().isoformat() + "%"
    with db.get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM runs WHERE created_at LIKE ?", (prefix,)
        ).fetchone()[0]


def _fail_stale_runs() -> int:
    """Runs left 'running' by a crash or restart can never finish. Mark them failed."""
    with db.get_conn() as conn:
        return conn.execute("UPDATE runs SET status = 'failed' WHERE status = 'running'").rowcount


def _mark_failed(run_id: str, message: str) -> None:
    db.update_run(run_id, status="failed")
    db.add_event(run_id, "system", message)


# ---------------------------------------------------------------------------
# The background job
# ---------------------------------------------------------------------------

def _run_job(run_id: str, idea: str) -> None:
    try:
        run_validator(run_id, idea)
    except DailyLimitError:
        _mark_failed(run_id, "The daily AI token limit is used up. Try again later.")
    except Exception as e:
        _mark_failed(run_id, f"The run stopped with an error: {str(e)[:150]}")


# ---------------------------------------------------------------------------
# App, security and input models
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    _fail_stale_runs()
    yield


app = FastAPI(
    title="Startup Idea Validator",
    version="1.0",
    description="Researcher, analyst and critic agents validate a startup idea "
                "and write a sourced, rule-scored report.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_key(x_api_key: str | None = Header(default=None)) -> None:
    """If APP_API_KEY is set, every request must send it in the X-API-Key header."""
    if APP_API_KEY and not hmac.compare_digest(x_api_key or "", APP_API_KEY):
        raise HTTPException(status_code=401, detail="Missing or wrong API key.")


class IdeaIn(BaseModel):
    idea: str = Field(min_length=15, max_length=1500,
                      description="Describe the startup idea in at least one full sentence.")

    @field_validator("idea", mode="before")
    @classmethod
    def strip_idea(cls, value):
        return value.strip() if isinstance(value, str) else value


class NoteIn(BaseModel):
    text: str = Field(min_length=5, max_length=4000)

    @field_validator("text", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


router = APIRouter(dependencies=[Depends(require_key)])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME}


@router.post("/validate", status_code=202)
def validate(body: IdeaIn, background: BackgroundTasks):
    with _start_lock:
        if _running_count() > 0:
            raise HTTPException(409, "A validation is already running. Wait for it to finish.")
        if _runs_today() >= MAX_RUNS_PER_DAY:
            raise HTTPException(
                429, f"The daily limit of {MAX_RUNS_PER_DAY} validations is reached. Try again tomorrow."
            )
        run_id = db.create_run(body.idea)
    background.add_task(_run_job, run_id, body.idea)
    return {"run_id": run_id, "status": "running"}


@router.get("/runs")
def list_runs(limit: int = Query(20, ge=1, le=100)):
    return db.list_runs(limit)


@router.get("/runs/{run_id}")
def run_status(run_id: str, after: int = Query(0, ge=0)):
    """Status plus the live events newer than event number `after`."""
    run = db.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found.")
    return {
        "run_id": run["id"],
        "idea": run["idea_text"],
        "status": run["status"],
        "verdict": run["verdict"],
        "evidence_score": run["evidence_score"],
        "created_at": run["created_at"],
        "events": db.get_events(run_id, after_id=after),
    }


@router.get("/runs/{run_id}/report")
def run_report(run_id: str):
    run = db.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found.")
    if run["status"] == "running":
        raise HTTPException(409, "The run is not finished yet.")
    claims = db.get_claims(run_id)
    return {
        "run_id": run["id"],
        "status": run["status"],
        "verdict": run["verdict"],
        "evidence_score": run["evidence_score"],
        "report_md": run["report_md"] or "",
        "verified": [c for c in claims if c["status"] == "verified"],
        "dropped": [c for c in claims if c["status"] == "dropped"],
        "sources": db.get_sources(run_id),
    }


@router.post("/notes", status_code=201)
def create_note(body: NoteIn):
    try:
        chunks = add_note(body.text)
    except Exception as e:
        raise HTTPException(502, f"Could not save the note to memory: {str(e)[:150]}")
    return {"saved": True, "chunks": chunks}


@router.get("/notes")
def list_notes():
    return db.list_notes()

@app.get("/", include_in_schema=False)
def root():
    return {"service": "Startup Idea Validator API", "docs": "/docs", "health": "/health"}


app.include_router(router)