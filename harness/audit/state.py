"""The state folder: one JSON file per document, plus feedback and report history."""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path


def doc_path(state_dir: Path, ref: str) -> Path:
    return Path(state_dir) / "docs" / f"{hashlib.sha1(ref.encode()).hexdigest()}.json"


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=1, default=str))
    tmp.replace(path)


def read_json(path: Path, default=None):
    return json.loads(path.read_text()) if path.is_file() else default


def all_docs(state_dir: Path) -> list[dict]:
    folder = Path(state_dir) / "docs"
    return [json.loads(p.read_text()) for p in sorted(folder.glob("*.json"))] if folder.is_dir() else []


def load_docs(state_dir: Path, as_of: date) -> list[dict]:
    """Documents received by the end of as_of (UTC), in received order."""
    docs = [d for d in all_docs(state_dir) if datetime.fromisoformat(d["received_at"]).date() <= as_of]
    return sorted(docs, key=lambda d: (d["received_at"], d["ref"]))
