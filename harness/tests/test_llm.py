import time
from types import SimpleNamespace

from audit import llm

SCHEMA = {"type": "object", "properties": {"a": {"type": "integer"}}, "required": ["a"], "additionalProperties": False}


class FakeClient:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        stop, text = self.replies.pop(0)
        return SimpleNamespace(stop_reason=stop, content=[SimpleNamespace(type="text", text=text)],
                               usage=SimpleNamespace(input_tokens=10, output_tokens=5, cache_read_input_tokens=0),
                               model=kw["model"])


def use(monkeypatch, client):
    monkeypatch.setattr(llm, "_client", lambda: client)
    monkeypatch.setattr(llm, "DEV_CACHE", None)


def test_call_json_parses_and_caches(monkeypatch, tmp_path):
    fake = FakeClient([("end_turn", '{"a": 1}')])
    use(monkeypatch, fake)
    content = [{"type": "text", "text": "doc"}]
    assert llm.call_json("t", "sys", content, SCHEMA, state_dir=tmp_path) == {"a": 1}
    assert llm.call_json("t", "sys", content, SCHEMA, state_dir=tmp_path) == {"a": 1}
    assert len(fake.calls) == 1
    assert fake.calls[0]["output_config"]["format"]["schema"] == SCHEMA
    assert (tmp_path / "llm" / "usage.jsonl").read_text().count("\n") == 1


def test_refusal_retries_on_the_second_model_then_gives_none(monkeypatch, tmp_path):
    fake = FakeClient([("refusal", ""), ("refusal", "")])
    use(monkeypatch, fake)
    assert llm.call_json("t", "sys", [{"type": "text", "text": "x"}], SCHEMA, state_dir=tmp_path) is None
    assert [c["model"] for c in fake.calls] == [llm.MODEL, llm.FALLBACK_MODEL]


def test_bad_json_gives_none(monkeypatch, tmp_path):
    use(monkeypatch, FakeClient([("end_turn", "not json"), ("end_turn", "still not")]))
    assert llm.call_json("t", "sys", [{"type": "text", "text": "y"}], SCHEMA, state_dir=tmp_path) is None


def test_run_parallel_skips_work_after_the_deadline():
    started = []

    def job(i):
        def run():
            started.append(i)
            return i
        return run

    assert llm.run_parallel([job(1), job(2)], workers=2, deadline=time.monotonic() + 60) == [1, 2]
    assert llm.run_parallel([job(3)], workers=1, deadline=time.monotonic() - 1) == [None]
    assert started == [1, 2]


class BrokenThenOk(FakeClient):
    def create(self, **kw):
        self.calls.append(kw)
        if len(self.calls) == 1:
            raise RuntimeError("connection reset")
        return super().create(**kw) if False else SimpleNamespace(
            stop_reason="end_turn", content=[SimpleNamespace(type="text", text='{"a": 2}')],
            usage=SimpleNamespace(input_tokens=1, output_tokens=1, cache_read_input_tokens=0), model=kw["model"])


def test_an_exception_from_the_first_model_falls_back_instead_of_crashing(monkeypatch, tmp_path):
    fake = BrokenThenOk([])
    use(monkeypatch, fake)
    assert llm.call_json("t", "sys", [{"type": "text", "text": "z"}], SCHEMA, state_dir=tmp_path) == {"a": 2}
    assert [c["model"] for c in fake.calls] == [llm.MODEL, llm.FALLBACK_MODEL]
