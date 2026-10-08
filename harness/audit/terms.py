"""Stage 2b: which term is in force on a pickup date, from which source, and who holds a missing document."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from .money import parse_date
from .world import Contract, Doc, World, dec, ev


@dataclass
class RateAnswer:
    value: Decimal | None = None
    minimum: Decimal | None = None
    evidence: list[dict] = field(default_factory=list)
    source: str = "msa"
    conflict: list[tuple[Decimal, list[dict]]] | None = None
    missing_doc: dict | None = None
    learned_at: dict | None = None


# ---- Schedule 1 authority --------------------------------------------------------------------------------------------
def _same_person(row: dict, email: str, name: str) -> bool:
    if email and (row.get("email") or "").lower() == email.lower():
        return True
    return bool(name) and " ".join(row.get("person", "").lower().split()) == " ".join(name.lower().split())


def _feedback_items(w: World, fact_type: str) -> list[dict]:
    return [f for f in w.feedback if f.get("fact", {}).get("type") == fact_type]


def _in_scope(fb: dict, day: date | None, **filters) -> bool:
    scope = fb.get("scope", {})
    applies = scope.get("applies_to", {})
    for k, v in applies.items():
        if k in filters and str(filters[k]).strip().lower() != str(v).strip().lower():
            return False
        if k not in filters:
            return False
    start, end = parse_date(scope.get("valid_from")), parse_date(scope.get("valid_to"))
    return not (day is not None and ((start and day < start) or (end and day > end)))


def authorised(w: World, c: Contract, email: str, name: str, category: str, day: date | None) -> bool:
    if any(_same_person(r, email, name) and category in r.get("categories", []) for r in c.schedule1):
        return True
    for fb in _feedback_items(w, "sender_authority"):
        person = fb["fact"].get("subject", {}).get("person", "")
        cats = fb["fact"].get("value", {}).get("categories", [])
        if category in cats and _same_person({"person": person}, "", name) and \
                _in_scope(fb, day, contract_id=c.id, person=person, category=category):
            return True
    return False


def authority_learned(w: World, c: Contract, name: str, category: str, day: date | None) -> dict | None:
    """The feedback item that granted this authority, when Schedule 1 itself does not."""
    if any(_same_person(r, "", name) and category in r.get("categories", []) for r in c.schedule1):
        return None
    for fb in _feedback_items(w, "sender_authority"):
        person = fb["fact"].get("subject", {}).get("person", "")
        if _same_person({"person": person}, "", name) and _in_scope(fb, day, contract_id=c.id, person=person,
                                                                    category=category):
            return {"feedback_item_id": fb["item_id"], "batch": fb.get("batch", "")}
    return None


def carrier_party(c: Contract) -> str | None:
    p = c.terms.get("parties") or {}
    if p.get("carrier_code"):
        return p["carrier_code"]
    shipper = p.get("shipper_code")
    parties = [r.get("party") for r in c.schedule1 if r.get("party") and r.get("party") != shipper]
    return parties[0] if parties else None


def contact(c: Contract, category: str, party: str | None = None) -> dict | None:
    party = party or carrier_party(c)
    for r in c.schedule1:
        if category in r.get("categories", []) and (party is None or r.get("party") == party):
            return {"person": r["person"], "party": r.get("party"), "role": r.get("title")}
    return None


def key_account_manager(c: Contract, party: str | None = None) -> dict | None:
    party = party or carrier_party(c)
    for r in c.schedule1:
        if r.get("party") == party and "key account" in (r.get("title") or "").lower():
            return {"person": r["person"], "party": r.get("party"), "role": r.get("title")}
    return contact(c, "notices", party)


def schedule1_evidence(c: Contract, person: str) -> dict | None:
    row = next((r for r in c.schedule1 if _same_person(r, "", person)), None)
    return ev(c.msa, row) if c.msa and row else None


# ---- rates -------------------------------------------------------------------------------------------------------------
def _band_rows(rows: list[dict], lane: str, kg: Decimal):
    band = minimum = None
    for r in rows:
        if r.get("lane") != lane:
            continue
        if r.get("is_minimum"):
            minimum = r
            continue
        lo, hi = dec(r.get("min_kg")) or Decimal(0), dec(r.get("max_kg"))
        if lo <= kg and (hi is None or kg <= hi):
            band = r
    return band, minimum


def _rate_of(row: dict | None, label: str | None) -> Decimal | None:
    if not row:
        return None
    rates = row.get("rates", [])
    hit = next((x for x in rates if label and x.get("period_label") == label), None)
    hit = hit or (rates[0] if len(rates) == 1 else None)
    return dec(hit["rate"]) if hit else None


def period_label(c: Contract, pickup: date) -> str | None:
    periods = [(parse_date(p.get("start")), parse_date(p.get("end")), p["label"]) for p in c.rates.get("periods", [])]
    periods = [p for p in periods if p[0]]
    if not periods:
        return None
    periods.sort()
    for start, end, label in periods:
        if start <= pickup and (end is None or pickup <= end):
            return label
    return periods[-1][2] if pickup > periods[-1][0] else periods[0][2]


def _amendment_effective(a: Doc) -> date | None:
    return parse_date(a.facts.get("terms", {}).get("effective_date"))


def _signed_amendment_answers(c: Contract, lane: str, kg: Decimal, pickup: date):
    """[(effective_from, kind, payload)] for each amendment change on this lane in force on the pickup date."""
    out = []
    for a in c.amendments:
        t = a.facts.get("terms", {})
        if not t.get("signed_by_both", True):
            continue
        for row in a.facts.get("rates", {}).get("rows", []):
            if row.get("lane") != lane:
                continue
            start = parse_date(row.get("effective_from")) or _amendment_effective(a)
            end = parse_date(row.get("effective_to"))
            if start and start <= pickup and (end is None or pickup <= end):
                out.append((start, "rate", (a, row)))
        for ch in t.get("amendment_changes", []):
            if ch.get("cites_document") and not ch.get("cited_document_attached") and lane in ch.get("lanes", []):
                start = parse_date(ch.get("effective_from")) or _amendment_effective(a)
                end = parse_date(ch.get("effective_to"))
                if start and start <= pickup and (end is None or pickup <= end):
                    out.append((start, "missing", (a, ch)))
    return out


def _notice_rows(w: World, c: Contract, lane: str, kg: Decimal, pickup: date):
    """Authorised rate notices (or ones a person accepted in feedback) in force for this lane and pickup."""
    out = []
    for d, n in c.notices:
        if n.get("lane") != lane:
            continue
        start, end = parse_date(n.get("effective_from")), parse_date(n.get("effective_to"))
        if not start or pickup < start or (end and pickup > end):
            continue
        learned = None
        if not authorised(w, c, d.sender_email, d.sender_name, "rates", start):
            learned = _accepted_by_feedback(w, c, d, lane, pickup)
            if not learned:
                continue
        band, minimum = _band_rows(n.get("rows", []), lane, kg) if any(r.get("lane") for r in n.get("rows", [])) \
            else _band_rows([{**r, "lane": lane} for r in n.get("rows", [])], lane, kg)
        if band:
            out.append((start, d, n, band, minimum, learned))
    return out


def _accepted_by_feedback(w: World, c: Contract, d: Doc, lane: str, pickup: date) -> dict | None:
    for fb in _feedback_items(w, "rate_accepted"):
        value = fb["fact"].get("value", {})
        if not _in_scope(fb, pickup, contract_id=c.id, lane=lane):
            continue
        sent_on = parse_date(value.get("sent_on"))
        if value.get("sent_by") and not _same_person({"person": value["sent_by"]}, "", d.sender_name):
            continue
        if sent_on and d.received_at.date() != sent_on:
            continue
        return {"feedback_item_id": fb["item_id"], "batch": fb.get("batch", "")}
    return None


def _precedence_choice(w: World, c: Contract, lane: str, pickup: date) -> tuple[str, dict] | None:
    for fb in _feedback_items(w, "precedence"):
        if _in_scope(fb, pickup, contract_id=c.id, lane=lane):
            use = fb["fact"].get("value", {}).get("use", "")
            return ("notice" if "notice" in use else "amendment"), {"feedback_item_id": fb["item_id"],
                                                                     "batch": fb.get("batch", "")}
    return None


def rate(w: World, c: Contract, lane: str, kg: Decimal, pickup: date) -> RateAnswer:
    ans = RateAnswer()
    label = period_label(c, pickup)
    band, minimum = _band_rows(c.rates.get("rows", []), lane, kg)
    if band:
        ans.value, ans.minimum = _rate_of(band, label), _rate_of(minimum, label)
        ans.evidence = [e for e in (ev(c.msa, band), ev(c.msa, (c.terms.get("rules") or {}).get("pricing_date")))
                        if e]
    amended = sorted(_signed_amendment_answers(c, lane, kg, pickup), key=lambda x: x[0])
    if amended and amended[-1][1] == "missing":
        a, change = amended[-1][2]
        ans.missing_doc = {"name": change["cites_document"], "holder": contact(c, "rates") or key_account_manager(c)}
        ans.evidence = [e for e in (ev(a, change),) if e]
        ans.value, ans.source = None, "amendment"
        return ans
    amd_value = None
    amd_rows = [x for x in amended if x[1] == "rate"]
    if amd_rows:
        a = amd_rows[-1][2][0]
        a_band, a_min = _band_rows(a.facts.get("rates", {}).get("rows", []), lane, kg)
        if a_band:
            amd_value = (_rate_of(a_band, None), [e for e in (ev(a, a_band),) if e])
        if a_min:
            ans.minimum = _rate_of(a_min, None)
    notices = sorted(_notice_rows(w, c, lane, kg, pickup), key=lambda x: x[0])
    note_value = None
    if notices:
        _, d, n, nband, nmin, learned = notices[-1]
        note_value = (dec(nband.get("rate")), [e for e in (ev(d, nband), ev(d, n)) if e])
        if learned:
            ans.learned_at = learned
        if nmin:
            ans.minimum = dec(nmin.get("rate"))
    if amd_value and note_value and amd_value[0] != note_value[0]:
        choice = _precedence_choice(w, c, lane, pickup)
        if choice:
            pick, learned = choice
            ans.value, ans.evidence = (note_value if pick == "notice" else amd_value)
            ans.source, ans.learned_at = pick, learned
            return ans
        ans.conflict = [amd_value, note_value]
        ans.source = "conflict"
        return ans
    if note_value:
        ans.value, ans.evidence, ans.source = note_value[0], note_value[1], "notice"
    elif amd_value:
        ans.value, ans.evidence, ans.source = amd_value[0], amd_value[1], "amendment"
    return ans


# ---- other terms -------------------------------------------------------------------------------------------------------
def _latest_table_row(c: Contract, table: str, pred, pickup: date):
    """The row from the MSA, or from the latest signed amendment in force on the pickup date that has one."""
    found = None
    for row in c.tables.get(table, []):
        if pred(row):
            found = (c.msa, row)
    for a in sorted(c.amendments, key=lambda a: _amendment_effective(a) or date.min):
        eff = _amendment_effective(a)
        if eff and eff > pickup:
            continue
        for row in a.facts.get("tables", {}).get(table, []):
            if pred(row):
                found = (a, row)
    return found


def fuel_pct(c: Contract, pickup: date) -> tuple[Decimal | None, list[dict]]:
    month = pickup.strftime("%Y-%m")
    hit = _latest_table_row(c, "fuel", lambda r: r.get("month") == month, pickup)
    if not hit:
        return None, []
    d, row = hit
    return dec(row.get("pct")), [e for e in (ev(d, row),) if e]


def accessorial(c: Contract, code: str, pickup: date) -> tuple[dict | None, list[dict]]:
    hit = _latest_table_row(c, "accessorials", lambda r: r.get("code") == code, pickup)
    if not hit:
        return None, []
    d, row = hit
    return row, [e for e in (ev(d, row),) if e]


def fx_rate(c: Contract, month: str) -> tuple[Decimal | None, list[dict]]:
    for d in [c.msa] + list(c.amendments):
        if d is None:
            continue
        for row in d.facts.get("tables", {}).get("fx", []):
            if row.get("month") == month:
                return dec(row.get("inr_per_usd")), [e for e in (ev(d, row),) if e]
    return None, []


def rule_evidence(c: Contract, name: str) -> dict | None:
    return ev(c.msa, (c.terms.get("rules") or {}).get(name)) if c.msa else None
