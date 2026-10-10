"""ingest: read a batch folder and keep every document's facts on disk."""
from __future__ import annotations

import os
import time
from pathlib import Path

from . import state
from .docs import Doc, read_batch
from .facts import extract_doc
from .llm import run_parallel

BUDGET_S = 420
DEADLINE_S = 540
WORKERS = int(os.environ.get("NOVA_WORKERS", "12"))  # lower it for a rate-limited local key


def _record(doc: Doc, source: Path, result: dict) -> dict:
    return {"ref": doc.ref, "email_ref": doc.email_ref, "name": doc.name, "kind_hint": doc.kind_hint,
            "received_at": doc.received_at.isoformat(), "sender_name": doc.sender_name,
            "sender_email": doc.sender_email, "subject": doc.subject, "pages": doc.pages, "is_scan": doc.is_scan,
            "source": str(source), **result}


def _run(items: list[tuple[Doc, Path]], state_dir: Path, start_by: float, deadline: float) -> list[str]:
    def job(doc: Doc, source: Path):
        def run():
            rec = _record(doc, source, extract_doc(doc, state_dir, deadline))
            state.write_json(state.doc_path(state_dir, doc.ref), rec)
            return doc.ref
        return run

    for doc, source in items:  # a placeholder first, so a doc that never starts is still known and retried
        path = state.doc_path(state_dir, doc.ref)
        if not path.is_file():
            state.write_json(path, _record(doc, source, {"kind": None, "facts": {}, "ok": False}))
    return [r for r in run_parallel([job(d, s) for d, s in items], workers=WORKERS, deadline=start_by) if r]


def ingest(batch_dir, state_dir, budget_s: float = BUDGET_S, deadline_s: float = DEADLINE_S) -> list[str]:
    batch_dir, state_dir = Path(batch_dir).resolve(), Path(state_dir)
    todo = []
    for doc in read_batch(batch_dir):
        old = state.read_json(state.doc_path(state_dir, doc.ref))
        if not (old and old.get("ok")):
            todo.append((doc, batch_dir / doc.email_ref.split("/", 1)[1]))
    now = time.monotonic()
    return _run(todo, state_dir, now + budget_s, now + deadline_s)


def retry_failed(state_dir, budget_s: float = BUDGET_S, deadline_s: float = DEADLINE_S) -> list[str]:
    """Extract documents that failed or never started, re-reading them from their saved source email."""
    state_dir = Path(state_dir)
    todo = []
    for rec in state.all_docs(state_dir):
        source = Path(rec["source"])
        if rec.get("ok") or not source.is_file():
            continue
        for doc in read_batch(source.parent):
            if doc.ref == rec["ref"]:
                todo.append((doc, source))
    now = time.monotonic()
    return _run(todo, state_dir, now + budget_s, now + deadline_s)
