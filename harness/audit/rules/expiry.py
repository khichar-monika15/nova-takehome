"""Expiry: a contract whose end, or non-renewal notice deadline, falls in the next 60 days."""
from __future__ import annotations

from datetime import timedelta

from ..money import parse_date
from ..world import Contract, World, dec, ev
from . import Candidate, dedupe

WINDOW_DAYS = 60


def _end(w: World, c: Contract):
    end, evidence = parse_date(c.terms.get("end_date")), [ev(c.msa, c.terms.get("term"))]
    for a in c.amendments:
        t = a.facts.get("terms", {})
        if t.get("signed_by_both", True) and t.get("doc_type") in ("extension", "amendment") and t.get("end_date"):
            new = parse_date(t["end_date"])
            if new and (end is None or new > end):
                end, evidence = new, [ev(a, t.get("term"))]
    for mail in w.emails:
        for ch in mail.facts.get("contract_changes", []):
            if ch.get("change") == "extension" and ch.get("signed_by_both") and \
                    (ch.get("contract_id") or "").upper() in ("", c.id):
                new = parse_date(ch.get("new_end_date"))
                if new and (end is None or new > end):
                    end, evidence = new, [ev(mail, ch)]
    return end, evidence


def run(w: World) -> list[Candidate]:
    out = []
    for c in w.contracts.values():
        if c.msa is None:
            continue
        end, evidence = _end(w, c)
        if end is None:
            continue
        deadline = end
        if c.terms.get("auto_renews"):
            days = dec(c.terms.get("non_renewal_notice_days"))
            if days is None:
                continue
            deadline = end - timedelta(days=int(days))
            evidence.append(ev(c.msa, c.terms.get("renewal")))
        if 0 <= (deadline - w.as_of).days <= WINDOW_DAYS:
            out.append(Candidate(cls="expiry", verdict="finding", contract_id=c.id, deadline=deadline,
                                 evidence=dedupe(evidence), deciding_refs=[c.msa.ref],
                                 features={"pickup_source": "tracking", "judgment": False, "inr": False}))
    return out
