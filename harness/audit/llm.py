"""One JSON-schema model call, cached on disk by content hash.

Claude is the provider whenever ANTHROPIC_API_KEY is set, which the grader always does. For local development
without an Anthropic key, AWS_BEARER_TOKEN_BEDROCK sends the same Claude requests through Amazon Bedrock, and
OPENAI_API_KEY falls back to OpenAI.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MODEL = "claude-opus-5-5"
FALLBACK_MODEL = "claude-sonnet-5-5"
SMALL_MODEL = "claude-haiku-5-5"
REQUEST_TIMEOUT_S = 240
MIN_CALL_S = 30
OPENAI_MODELS = {MODEL: "gpt-5.5", FALLBACK_MODEL: "gpt-5.5", SMALL_MODEL: "gpt-5.4-mini"}
BEDROCK_MODELS = {MODEL: "anthropic.claude-opus-5-5", FALLBACK_MODEL: "anthropic.claude-opus-5-5",
                  SMALL_MODEL: "anthropic.claude-opus-5-5"}

_REPO = Path(__file__).resolve().parents[2]
DEV_CACHE: Path | None = _REPO / ".work" / "llm_cache" if (_REPO / ".work").is_dir() else None

_shared = None
_shared_openai = None
_shared_bedrock = None


def provider() -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
        return "bedrock"
    return "openai" if os.environ.get("OPENAI_API_KEY") else "anthropic"


def _bedrock_client():
    global _shared_bedrock
    if _shared_bedrock is None:
        from anthropic import AnthropicBedrockMantle
        _shared_bedrock = AnthropicBedrockMantle(aws_region=os.environ.get("AWS_REGION", "us-east-1"),
                                                 max_retries=2, timeout=REQUEST_TIMEOUT_S)
    return _shared_bedrock


def _client():
    global _shared
    if _shared is None:
        import anthropic
        _shared = anthropic.Anthropic(max_retries=2, timeout=REQUEST_TIMEOUT_S)
    return _shared


def _openai_client():
    global _shared_openai
    if _shared_openai is None:
        import openai
        _shared_openai = openai.OpenAI(max_retries=2, timeout=REQUEST_TIMEOUT_S)
    return _shared_openai


def _openai_content(content: list) -> list:
    out = []
    for b in content:
        if b.get("type") == "image":
            src = b["source"]
            out.append({"type": "image_url", "image_url": {"url": f"data:{src['media_type']};base64,{src['data']}"}})
        else:
            out.append({"type": "text", "text": b["text"]})
    return out


def _key(system: str, content: list, schema: dict, effort: str) -> str:
    """Same document, prompt and schema -> same key, whichever provider answered (so `make grade`, which passes
    only the Anthropic variables, can replay a local run from the dev cache)."""
    blob = json.dumps([system, content, schema, effort], sort_keys=True)
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
    tokens_in = getattr(u, "input_tokens", None) or getattr(u, "prompt_tokens", 0)
    tokens_out = getattr(u, "output_tokens", None) or getattr(u, "completion_tokens", 0)
    row = {"task": task, "model": resp.model, "in": tokens_in, "out": tokens_out,
           "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0, "s": round(seconds, 1)}
    log = state_dir / "llm" / "usage.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a") as f:
        f.write(json.dumps(row) + "\n")


def _with_timeout(client, timeout: float | None):
    return client.with_options(timeout=timeout) if timeout and hasattr(client, "with_options") else client


def _json_in(text: str):
    """The JSON object in a reply that may wrap it in prose or a code fence."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        value = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _ask(model: str, system: str, content: list, schema: dict, max_tokens: int, effort: str, task: str,
         state_dir: Path, timeout: float | None = None):
    client = _with_timeout(_bedrock_client() if provider() == "bedrock" else _client(), timeout)
    t0 = time.monotonic()
    try:
        resp = client.messages.create(
            model=model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": content}],
            output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
        )
    except Exception as e:
        if getattr(e, "status_code", None) != 400:
            raise
        # The API refused the request shape (for example a schema it cannot compile): ask for plain JSON instead.
        print(f"llm {task}: structured output refused ({e}); asking for plain JSON", file=sys.stderr)
        plain = content + [{"type": "text", "text": "Return only one JSON object, with no other text, that matches "
                                                    f"this JSON schema:\n{json.dumps(schema)}"}]
        resp = client.messages.create(model=model, max_tokens=max_tokens, system=system,
                                      messages=[{"role": "user", "content": plain}],
                                      output_config={"effort": effort})
    _log_usage(state_dir, task, resp, time.monotonic() - t0)
    if resp.stop_reason == "refusal":
        return None
    text = next((b.text for b in resp.content if getattr(b, "type", "") == "text"), "")
    return _json_in(text)


def _ask_openai(model: str, system: str, content: list, schema: dict, max_tokens: int, effort: str, task: str,
                state_dir: Path, timeout: float | None = None):
    t0 = time.monotonic()
    resp = _with_timeout(_openai_client(), timeout).chat.completions.create(
        model=model, max_completion_tokens=max_tokens, reasoning_effort=effort,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": _openai_content(content)}],
        response_format={"type": "json_schema", "json_schema": {"name": task, "schema": schema, "strict": True}},
    )
    _log_usage(state_dir, task, resp, time.monotonic() - t0)
    msg = resp.choices[0].message
    if getattr(msg, "refusal", None) or not msg.content:
        return None
    try:
        return json.loads(msg.content)
    except json.JSONDecodeError:
        return None


def call_json(task: str, system: str, content: list, schema: dict, *, state_dir: Path, max_tokens: int = 16000,
              effort: str = "low", model: str = MODEL, deadline: float | None = None) -> dict | None:
    """-> the parsed JSON object, or None when both models refuse, return unparseable text, or the deadline
    (time.monotonic()) leaves too little time for a call."""
    state_dir = Path(state_dir)
    which = provider()
    ask = _ask_openai if which == "openai" else _ask
    names = {"openai": OPENAI_MODELS, "bedrock": BEDROCK_MODELS}.get(which, {})
    models = [names.get(m, m) for m in (model, FALLBACK_MODEL)]
    key = _key(system, content, schema, effort)
    paths = [state_dir / "llm" / f"{key}.json"] + ([DEV_CACHE / f"{key}.json"] if DEV_CACHE else [])
    hit = _read(paths)
    if hit is not None:
        if not (state_dir / "llm" / f"{key}.json").is_file():
            _write(paths[:1], hit)
        return hit["value"]
    value = None
    for m in dict.fromkeys(models):
        left = deadline - time.monotonic() if deadline else None
        if left is not None and left < MIN_CALL_S:
            print(f"llm {task}: skipped, {left:.0f} s left before the command deadline", file=sys.stderr)
            break
        timeout = min(REQUEST_TIMEOUT_S, left - 5) if left is not None else None
        try:
            value = ask(m, system, content, schema, max_tokens, effort, task, state_dir, timeout)
        except Exception as e:  # noqa: BLE001  the SDK already retried; one failed document must not stop the batch
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
