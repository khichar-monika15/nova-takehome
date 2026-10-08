"""One JSON-schema call to Claude, cached on disk by content hash."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MODEL = "claude-opus-5-5"
FALLBACK_MODEL = "claude-sonnet-5-5"
SMALL_MODEL = "claude-haiku-5-5"
REQUEST_TIMEOUT_S = 300

_REPO = Path(__file__).resolve().parents[2]
DEV_CACHE: Path | None = _REPO / ".work" / "llm_cache" if (_REPO / ".work").is_dir() else None

_shared = None


def _client():
    global _shared
    if _shared is None:
        import anthropic
        _shared = anthropic.Anthropic(max_retries=2, timeout=REQUEST_TIMEOUT_S)
    return _shared


def _key(model: str, system: str, content: list, schema: dict, effort: str) -> str:
    blob = json.dumps([model, system, content, schema, effort], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def _read(paths: list[Path]):
    for p in paths:
        if p.is_file():
            return json.loads(p.read_text())
    return None


def _write(paths: list[Path], value) -> None:
    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(value))
        tmp.replace(p)


def _log_usage(state_dir: Path, task: str, resp, seconds: float) -> None:
    u = resp.usage
    row = {"task": task, "model": resp.model, "in": u.input_tokens, "out": u.output_tokens,
           "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0, "s": round(seconds, 1)}
    log = state_dir / "llm" / "usage.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a") as f:
        f.write(json.dumps(row) + "\n")


def _ask(model: str, system: str, content: list, schema: dict, max_tokens: int, effort: str, task: str,
         state_dir: Path):
    t0 = time.monotonic()
    resp = _client().messages.create(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": content}],
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
    )
    _log_usage(state_dir, task, resp, time.monotonic() - t0)
    if resp.stop_reason == "refusal":
        return None
    text = next((b.text for b in resp.content if getattr(b, "type", "") == "text"), "")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def call_json(task: str, system: str, content: list, schema: dict, *, state_dir: Path, max_tokens: int = 16000,
              effort: str = "low", model: str = MODEL) -> dict | None:
    """-> the parsed JSON object, or None when both models refuse or return unparseable text."""
    state_dir = Path(state_dir)
    key = _key(model, system, content, schema, effort)
    paths = [state_dir / "llm" / f"{key}.json"] + ([DEV_CACHE / f"{key}.json"] if DEV_CACHE else [])
    hit = _read(paths)
    if hit is not None:
        if not (state_dir / "llm" / f"{key}.json").is_file():
            _write(paths[:1], hit)
        return hit["value"]
    value = None
    for m in dict.fromkeys((model, FALLBACK_MODEL)):
        try:
            value = _ask(m, system, content, schema, max_tokens, effort, task, state_dir)
        except Exception as e:  # the SDK already retried; one failed document must not stop the batch
            print(f"llm {task}: {m} failed: {type(e).__name__}: {e}", file=sys.stderr)
            value = None
        if value is not None:
            break
    if value is not None:
        _write(paths, {"task": task, "value": value})
    return value


def run_parallel(fns: list, *, workers: int = 8, deadline: float) -> list:
    """Run each zero-argument function in a thread pool; work not started by the deadline returns None."""
    def guarded(fn):
        if time.monotonic() > deadline:
            return None
        return fn()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(guarded, fns))
