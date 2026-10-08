import pytest

from audit import schemas

FORBIDDEN = {"minimum", "maximum", "minLength", "maxLength", "minItems", "maxItems", "pattern", "$ref"}


def walk(node, path="$"):
    if isinstance(node, dict):
        bad = FORBIDDEN & node.keys()
        assert not bad, f"{path} uses {bad}"
        if node.get("type") == "object" or "properties" in node:
            assert node.get("additionalProperties") is False, f"{path} is not closed"
            assert set(node.get("required", [])) == set(node["properties"]), f"{path} has optional fields"
        for k, v in node.items():
            walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, f"{path}[{i}]")


@pytest.mark.parametrize("name", sorted(schemas.ALL))
def test_schema_fits_structured_output_limits(name):
    walk(schemas.ALL[name])


def test_every_kind_has_a_schema_and_a_prompt():
    from audit import prompts
    for kind in ("classify", "email", "contract_terms", "contract_rates", "contract_tables", "invoice", "awb",
                 "dgd", "table"):
        assert kind in schemas.ALL
        assert kind in prompts.TASK
