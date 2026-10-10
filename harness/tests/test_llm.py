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
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)
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


class FakeOpenAI:
    def __init__(self, text='{"a": 3}', refusal=None):
        self.calls = []
        self.text, self.refusal = text, refusal
        self.chat = SimpleNamespace(completions=self)

    def create(self, **kw):
        self.calls.append(kw)
        msg = SimpleNamespace(content=self.text, refusal=self.refusal)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg, finish_reason="stop")], model=kw["model"],
                               usage=SimpleNamespace(prompt_tokens=7, completion_tokens=3))


def test_provider_prefers_anthropic_and_falls_back_to_openai(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)
    assert llm.provider() == "anthropic"
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert llm.provider() == "openai"


def test_openai_call_uses_strict_json_schema_and_converts_images(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)
    fake = FakeOpenAI()
    monkeypatch.setattr(llm, "_openai_client", lambda: fake)
    monkeypatch.setattr(llm, "DEV_CACHE", None)
    content = [{"type": "text", "text": "page"},
               {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "QUJD"}}]
    assert llm.call_json("invoice", "sys", content, SCHEMA, state_dir=tmp_path) == {"a": 3}
    kw = fake.calls[0]
    assert kw["model"] == llm.OPENAI_MODELS[llm.MODEL]
    assert kw["response_format"]["json_schema"]["strict"] is True
    assert kw["response_format"]["json_schema"]["schema"] == SCHEMA
    assert kw["messages"][0] == {"role": "system", "content": "sys"}
    assert kw["messages"][1]["content"][1] == {"type": "image_url", "image_url": {"url": "data:image/png;base64,QUJD"}}


def test_openai_refusal_gives_none(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)
    monkeypatch.setattr(llm, "_openai_client", lambda: FakeOpenAI(text=None, refusal="no"))
    monkeypatch.setattr(llm, "DEV_CACHE", None)
    assert llm.call_json("t", "sys", [{"type": "text", "text": "r"}], SCHEMA, state_dir=tmp_path) is None


def test_dev_cache_written_by_one_provider_is_read_by_the_other(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "DEV_CACHE", tmp_path / "dev")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)
    monkeypatch.setattr(llm, "_openai_client", lambda: FakeOpenAI(text='{"a": 9}'))
    content = [{"type": "text", "text": "same document"}]
    assert llm.call_json("t", "sys", content, SCHEMA, state_dir=tmp_path / "s1") == {"a": 9}
    monkeypatch.delenv("OPENAI_API_KEY")
    monkeypatch.setattr(llm, "_client", lambda: (_ for _ in ()).throw(AssertionError("no network expected")))
    assert llm.call_json("t", "sys", content, SCHEMA, state_dir=tmp_path / "s2") == {"a": 9}



class RejectsSchema(FakeClient):
    def create(self, **kw):
        self.calls.append(kw)
        if "format" in kw.get("output_config", {}):
            err = RuntimeError("Schema is too complex for compilation")
            err.status_code = 400
            raise err
        return SimpleNamespace(stop_reason="end_turn", model=kw["model"],
                               content=[SimpleNamespace(type="text", text='Here it is:\n```json\n{"a": 5}\n```')],
                               usage=SimpleNamespace(input_tokens=1, output_tokens=1, cache_read_input_tokens=0))


def test_a_rejected_schema_falls_back_to_plain_json_in_the_prompt(monkeypatch, tmp_path):
    fake = RejectsSchema([])
    use(monkeypatch, fake)
    assert llm.call_json("t", "sys", [{"type": "text", "text": "q"}], SCHEMA, state_dir=tmp_path) == {"a": 5}
    plain = fake.calls[-1]
    assert "format" not in plain.get("output_config", {})
    assert '"required": ["a"]' in plain["messages"][0]["content"][-1]["text"]


def test_no_call_is_started_when_the_deadline_is_too_close(monkeypatch, tmp_path):
    fake = FakeClient([("end_turn", '{"a": 1}')])
    use(monkeypatch, fake)
    assert llm.call_json("t", "sys", [{"type": "text", "text": "late"}], SCHEMA, state_dir=tmp_path,
                         deadline=time.monotonic() + 5) is None
    assert fake.calls == []


def test_bedrock_is_used_when_only_a_bedrock_key_exists_and_maps_models_to_opus(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "b")
    assert llm.provider() == "bedrock"
    fake = FakeClient([("end_turn", '{"a": 4}')])
    monkeypatch.setattr(llm, "_bedrock_client", lambda: fake)
    monkeypatch.setattr(llm, "DEV_CACHE", None)
    assert llm.call_json("t", "sys", [{"type": "text", "text": "b"}], SCHEMA, state_dir=tmp_path,
                         model=llm.SMALL_MODEL) == {"a": 4}
    assert fake.calls[0]["model"] == "anthropic.claude-opus-5-5"
    assert fake.calls[0]["output_config"]["format"]["schema"] == SCHEMA
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    assert llm.provider() == "anthropic"


class FailsUnlessOpus(FakeClient):
    def create(self, **kw):
        self.calls.append(kw)
        if kw["model"] != llm.MODEL:
            err = RuntimeError("model not found")
            err.status_code = 404
            raise err
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text='{"a": 6}')],
                               usage=SimpleNamespace(input_tokens=1, output_tokens=1, cache_read_input_tokens=0),
                               model=kw["model"])


def test_a_call_on_the_mid_model_falls_back_to_opus_last(monkeypatch, tmp_path):
    fake = FailsUnlessOpus([])
    use(monkeypatch, fake)
    assert llm.call_json("classify", "sys", [{"type": "text", "text": "c"}], SCHEMA, state_dir=tmp_path,
                         model=llm.FALLBACK_MODEL) == {"a": 6}
    assert [c["model"] for c in fake.calls] == [llm.FALLBACK_MODEL, llm.MODEL]


def test_every_retry_of_a_call_fits_before_the_deadline(monkeypatch, tmp_path):
    class TimedClient(FakeClient):
        def with_options(self, **kw):
            self.options = kw
            return self
    fake = TimedClient([("end_turn", '{"a": 1}')])
    use(monkeypatch, fake)
    llm.call_json("t", "sys", [{"type": "text", "text": "x"}], SCHEMA, state_dir=tmp_path,
                  deadline=time.monotonic() + 305)
    assert fake.options["timeout"] * (llm.MAX_RETRIES + 1) <= 305
