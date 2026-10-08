"""Read one batch folder into documents, using the grader's own text layer."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path

GRADER = Path(__file__).resolve().parents[2] / "grader"
if str(GRADER) not in sys.path:
    sys.path.insert(0, str(GRADER))

import extract as gx  # noqa: E402  (grader/extract.py: the text the grader checks quotes against)


@dataclass
class Doc:
    ref: str
    email_ref: str
    name: str
    kind_hint: str
    received_at: datetime
    sender_name: str
    sender_email: str
    subject: str
    pages: list[str]
    is_scan: bool
    data: bytes = field(repr=False, default=b"")


def _ext(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def read_batch(batch_dir: Path) -> list[Doc]:
    batch_dir = Path(batch_dir)
    docs: list[Doc] = []
    for f in sorted(batch_dir.glob("*.eml")):
        raw = f.read_bytes()
        msg = gx.parse_eml(raw)
        email_ref = f"{batch_dir.name}/{f.name}"
        sender_name, sender_email = parseaddr(str(msg["From"]))
        received = parsedate_to_datetime(str(msg["Date"])).astimezone(timezone.utc)
        subject = str(msg["Subject"] or "")
        common = dict(email_ref=email_ref, received_at=received, sender_name=sender_name,
                      sender_email=sender_email.lower(), subject=subject)
        docs.append(Doc(ref=email_ref, name=f.name, kind_hint="email", pages=gx.pages_of(raw, "eml"),
                        is_scan=False, data=raw, **common))
        for name, data in gx.attachments(raw):
            ext = _ext(name)
            if ext not in ("pdf", "xlsx"):
                continue
            scan = ext == "pdf" and gx.pdf_is_image_only(data)
            docs.append(Doc(ref=f"{email_ref}#{name}", name=name, kind_hint=ext, pages=gx.pages_of(data, ext),
                            is_scan=scan, data=data, **common))
    return docs


def page_png(pdf_bytes: bytes, page_no: int, dpi: int = 150) -> bytes:
    import pymupdf
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        return doc[page_no - 1].get_pixmap(dpi=dpi).tobytes("png")
