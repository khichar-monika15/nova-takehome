from datetime import date
from decimal import Decimal

from audit import terms
from audit.world import build
from fixtures import clause, email, msa

AS_OF = date(2032, 12, 31)


def notice(sender, lane="AAA-BBB", start="2032-01-10", end="2032-12-31", rate="3.03", received="2032-01-05"):
    row = {"is_minimum": False, "min_kg": "100", "max_kg": "299.5", "rate": rate, "currency": "USD",
           **clause(f"{lane} 100-299.5 kg: {rate} USD", 1)}
    n = {"contract_id": "C-1", "reference": None, "lane": lane, "effective_from": start, "effective_to": end,
         "rows": [row], **clause("Under clause 3.5 we give notice of the following rates", 1)}
    return email(f"batch_01/0{abs(hash(sender)) % 90 + 10}.eml", f"{received}T10:00:00+00:00", sender,
                 intent="rate_notice", rate_notices=[n])


def amendment(rate="2.88", effective="2032-01-01", cites=None, lanes=("AAA-BBB",)):
    a = msa(received="2032-01-02T09:00:00+00:00", doc_type="amendment", amendment_ref="C-1/AMD-1",
            effective_date=effective,
            amendment_changes=[{"kind": "rates", "lanes": list(lanes), "effective_from": effective,
                                "effective_to": None, "all_periods": True, "cites_document": cites,
                                "cited_document_attached": cites is None, **clause("1. Annex A rates replaced", 1)}])
    a["ref"] = "batch_01/0002.eml#AMD-1.pdf"
    rows = [] if cites else [{"lane": "AAA-BBB", "is_minimum": False, "min_kg": "100", "max_kg": "299.5",
                              "rates": [{"period_label": "all", "rate": rate}], "effective_from": effective,
                              "effective_to": None, **clause(f"AAA-BBB 100-299.5 kg {rate} USD", 1)}]
    a["facts"]["rates"] = {"currency": "USD", "periods": [], "rows": rows}
    a["facts"]["tables"] = {"fuel": [], "accessorials": [], "aliases": [], "fx": [], "fx_update_rule": None}
    return a


RAE = ("Rae Rates", "rae@carrier.example")
KIM = ("Kim Key", "kim@carrier.example")


def rate(records, kg="113", pickup=date(2032, 3, 1), feedback=None):
    w = build(records, AS_OF, feedback)
    return terms.rate(w, w.contracts["C-1"], "AAA-BBB", Decimal(kg), pickup)


def test_msa_band_and_period():
    assert rate([msa()]).value == Decimal("6.01")
    assert rate([msa()], pickup=date(2032, 7, 1)).value == Decimal("6.16")
    assert rate([msa()], kg="44").value == Decimal("7.73")


def test_after_the_last_period_the_last_period_rate_applies():
    assert rate([msa()], pickup=date(2033, 2, 1)).value == Decimal("6.16")


def test_amendment_beats_the_msa():
    assert rate([msa(), amendment()]).value == Decimal("2.88")


def test_authorised_notice_beats_the_msa():
    assert rate([msa(), notice(RAE)]).value == Decimal("3.03")


def test_unauthorised_notice_is_ignored():
    got = rate([msa(), notice(KIM)])
    assert got.value == Decimal("6.01") and got.conflict is None


def test_authorised_notice_and_amendment_in_force_together_are_a_conflict():
    got = rate([msa(), amendment(), notice(RAE)])
    assert got.conflict is not None
    assert sorted(v for v, _ in got.conflict) == [Decimal("2.88"), Decimal("3.03")]


def test_missing_cited_attachment_gives_missing_doc_with_rates_holder():
    got = rate([msa(), amendment(cites="Annex A rev 2")])
    assert got.missing_doc == {"name": "Annex A rev 2", "holder": {"person": "Rae Rates", "party": "CAR-US",
                                                                   "role": "Pricing Manager"}}


def test_feedback_rate_accepted_makes_the_named_notice_count_inside_its_scope():
    fb = [{"item_id": "fb-1", "batch": "batch_01", "decision": "close",
           "finding_key": {"invoice_id": "X", "class": "overcharge"},
           "fact": {"type": "rate_accepted", "subject": {"contract_id": "C-1", "lane": "AAA-BBB"},
                    "value": {"source": "rate notice", "sent_by": "Kim Key", "sent_on": "2032-01-05",
                              "effective_from": "2032-01-10", "effective_to": "2032-12-31"}},
           "scope": {"kind": "standing", "applies_to": {"contract_id": "C-1", "lane": "AAA-BBB"},
                     "valid_from": "2032-01-10", "valid_to": "2032-12-31"}}]
    got = rate([msa(), notice(KIM)], feedback=fb)
    assert got.value == Decimal("3.03")
    assert got.learned_at == {"feedback_item_id": "fb-1", "batch": "batch_01"}


def test_authorised_person_lookup():
    w = build([msa()], AS_OF)
    c = w.contracts["C-1"]
    assert terms.authorised(w, c, "rae@carrier.example", "Rae Rates", "rates", date(2032, 3, 1))
    assert not terms.authorised(w, c, "kim@carrier.example", "Kim Key", "rates", date(2032, 3, 1))
    assert terms.authorised(w, c, "", "Wes Waiver", "waivers", date(2032, 3, 1))


def test_fuel_pct_by_pickup_month():
    w = build([msa()], AS_OF)
    assert terms.fuel_pct(w.contracts["C-1"], date(2031, 12, 25))[0] == Decimal("20.16")
