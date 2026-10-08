"""Waived but billed: a charge an authorised person waived in their own words, billed anyway."""
from __future__ import annotations

from decimal import Decimal

from .. import terms
from ..world import Invoice, Line, World, charge_code, ev, norm_id, norm_label
from . import Candidate, dedupe, to_usd


def _month(ln: Line) -> str | None:
    if ln.refers_to_period and len(ln.refers_to_period) >= 7:
        return ln.refers_to_period[:7]
    return ln.pickup_printed.strftime("%Y-%m") if ln.pickup_printed else None


def _covered(inv: Invoice, ln: Line, wv: dict, months: list[str] | None = None) -> bool:
    code = charge_code(inv.contract, wv.get("charge", ""))
    same_charge = ln.code == code if code else norm_label(ln.label) == norm_label(wv.get("charge", ""))
    if not same_charge:
        return False
    if ln.shipment and ln.shipment in (wv.get("shipments") or []):
        return True
    if _month(ln) in (months if months is not None else (wv.get("months") or [])):
        return True
    named = wv.get("invoice_id")
    return bool(named) and norm_id(named) == inv.key and not wv.get("shipments") and not wv.get("months")


def _targets(w: World, wv: dict, months: list[str] | None = None, only: str | None = None):
    for copies in w.invoices.values():
        inv = copies[0]
        if only and inv.key != norm_id(only):
            continue
        lines = [ln for ln in inv.lines if _covered(inv, ln, wv, months)]
        if lines:
            yield inv, lines


def _candidate(inv: Invoice, lines: list[Line], evidence: list, verdict="finding", **kw) -> Candidate | None:
    amount = sum((ln.amount for ln in lines), Decimal(0))
    usd, fx_ev, _ = to_usd(amount, inv)
    if verdict == "finding" and (usd is None or usd <= 0):
        return None
    return Candidate(cls="waived_but_billed", verdict=verdict, invoice_id=inv.id,
                     contract_id=inv.contract.id if inv.contract else None,
                     amount=usd if verdict == "finding" else None,
                     native=amount if verdict == "finding" else None,
                     evidence=dedupe([ev(inv.doc, ln.item) for ln in lines] + evidence + fx_ev),
                     features={"pickup_source": "invoice", "judgment": True, "inr": inv.currency != "USD"}, **kw)


def _own_waivers(w: World, found: dict) -> None:
    for mail in w.emails:
        for wv in mail.facts.get("waivers", []):
            if wv.get("conditional") and wv.get("condition_met") != "yes":
                continue
            for inv, lines in _targets(w, wv):
                c = inv.contract
                day = mail.received_at.date()
                if c is None or not terms.authorised(w, c, mail.sender_email, mail.sender_name, "waivers", day):
                    continue
                learned = terms.authority_learned(w, c, mail.sender_name, "waivers", day)
                cand = _candidate(inv, lines, [ev(mail, wv), terms.schedule1_evidence(c, mail.sender_name),
                                               terms.rule_evidence(c, "waivers")],
                                  learned_at=learned, deciding_refs=[mail.ref, inv.doc.ref])
                if cand:
                    found[inv.key] = cand


def _quoted_only(w: World, found: dict) -> None:
    for mail in w.emails:
        for qw in mail.facts.get("quoted_waivers", []):
            for inv, lines in _targets(w, qw):
                if inv.key in found or inv.contract is None:
                    continue
                c = inv.contract
                author = qw.get("quoted_author_name") or ""
                if author and terms.authorised(w, c, qw.get("quoted_author_email") or "", author, "waivers", None):
                    holder = terms.contact(c, "waivers")
                    holder = next(({"person": r["person"], "party": r.get("party"), "role": r.get("title")}
                                   for r in c.schedule1 if r.get("person", "").lower() == author.lower()), holder)
                else:
                    holder = terms.key_account_manager(c)
                shipments = ", ".join(qw.get("shipments") or []) or ", ".join(qw.get("months") or [])
                name = f"original email from {author or 'the waiver author'} waiving the {qw.get('charge')} " \
                       f"on {shipments}".strip()
                found[inv.key] = _candidate(inv, lines, [ev(mail, qw)], verdict="cannot_determine",
                                            missing_doc={"name": name, "holder": holder},
                                            deciding_refs=[mail.ref, inv.doc.ref])


def _one_off_approvals(w: World, found: dict) -> None:
    for fb in w.feedback:
        if fb.get("decision") != "one_off_approval" or fb.get("finding_key", {}).get("class") != "waived_but_billed":
            continue
        months = fb.get("fact", {}).get("value", {}).get("months", [])
        person = fb.get("fact", {}).get("subject", {}).get("person", "")
        inv_id = fb["finding_key"]["invoice_id"]
        for mail in w.emails:
            if person and norm_label(mail.sender_name) != norm_label(person):
                continue
            for wv in mail.facts.get("waivers", []):
                for inv, lines in _targets(w, wv, months=months, only=inv_id):
                    lines = [ln for ln in lines if _month(ln) in months]
                    cand = _candidate(inv, lines, [ev(mail, wv)],
                                      learned_at={"feedback_item_id": fb["item_id"], "batch": fb.get("batch", "")},
                                      deciding_refs=[mail.ref, inv.doc.ref]) if lines else None
                    if cand:
                        found[inv.key] = cand


def run(w: World) -> list[Candidate]:
    found: dict[str, Candidate] = {}
    _own_waivers(w, found)
    _quoted_only(w, found)
    _one_off_approvals(w, found)
    return [c for c in found.values() if c]
