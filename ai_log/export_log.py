"""Export this Claude Code session (and its subagents) to markdown for ai_log/, with API keys removed.

    .venv/bin/python -I ai_log/export_log.py <session.jsonl> ai_log
"""
import json
import re
import sys
from pathlib import Path

KEY = re.compile(r"sk-(?:proj|ant|live|admin)[A-Za-z0-9_\-]{8,}")
RESULT_CHARS = 1500
INPUT_CHARS = 2500


def scrub(s: str) -> str:
    return KEY.sub("[API KEY REMOVED]", s)


def clip(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n] + f"\n... [{len(s) - n} more characters]"


def block_text(content) -> str:
    if isinstance(content, str):
        return content
    out = []
    for b in content or []:
        if isinstance(b, dict) and b.get("type") == "text":
            out.append(b.get("text", ""))
        elif isinstance(b, dict) and b.get("type") == "image":
            out.append("[image]")
    return "\n".join(out)


def render(path: Path, title: str) -> str:
    note = (f"Source: `{path.name}`. Tool results are cut to {RESULT_CHARS} characters, tool inputs to "
            f"{INPUT_CHARS}. API keys are replaced with a marker. Nothing else is removed.")
    out = [f"# {title}", "", note, ""]
    for line in path.read_text().splitlines():
        d = json.loads(line)
        t, ts = d.get("type"), (d.get("timestamp") or "")[:19].replace("T", " ")
        if t == "queue-operation" and d.get("operation") == "enqueue" and d.get("content"):
            out += [f"## User (sent while Claude was working) {ts}", "", str(d["content"]), ""]
            continue
        msg = d.get("message") or {}
        content = msg.get("content")
        if t == "user" and not d.get("isMeta"):
            if isinstance(content, str):
                out += [f"## User {ts}", "", content, ""]
            elif isinstance(content, list):
                for b in content:
                    if b.get("type") == "tool_result":
                        text = block_text(b.get("content"))
                        out += ["<details><summary>tool result</summary>", "", "```", clip(text, RESULT_CHARS),
                                "```", "</details>", ""]
                    elif b.get("type") == "text" and not d.get("isMeta"):
                        out += [f"## User {ts}", "", b.get("text", ""), ""]
        elif t == "assistant" and isinstance(content, list):
            for b in content:
                if b.get("type") == "text" and b.get("text", "").strip():
                    out += [f"## Claude {ts}", "", b["text"], ""]
                elif b.get("type") == "thinking" and b.get("thinking", "").strip():
                    out += ["<details><summary>Claude thinking</summary>", "", b["thinking"], "</details>", ""]
                elif b.get("type") == "tool_use":
                    inp = json.dumps(b.get("input", {}), indent=1)
                    out += [f"**Tool call: {b.get('name')}**", "", "```json", clip(inp, INPUT_CHARS), "```", ""]
    return scrub("\n".join(out))


if __name__ == "__main__":
    session, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "session.md").write_text(render(session, "Main session"))
    sub = session.with_suffix("") / "subagents"
    for f in sorted(sub.glob("agent-*.jsonl")) if sub.is_dir() else []:
        meta = f.with_suffix(".meta.json")
        desc = json.loads(meta.read_text()).get("description", f.stem) if meta.is_file() else f.stem
        (out_dir / f"subagent-{f.stem.removeprefix('agent-')}.md").write_text(render(f, f"Subagent: {desc}"))
    left = [p.name for p in out_dir.glob("*.md") if KEY.search(p.read_text())]
    print(f"wrote {len(list(out_dir.glob('*.md')))} files; files still holding a key: {left}")
