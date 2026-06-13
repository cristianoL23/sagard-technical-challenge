import pytest

from src.llm_client import parse_llm_json


def test_parse_llm_json_accepts_plain_object():
    assert parse_llm_json('{"company_short_name": "NovaCloud"}') == {
        "company_short_name": "NovaCloud"
    }


def test_parse_llm_json_accepts_plain_array():
    assert parse_llm_json('[{"metric_name": "revenue", "value": 1}]') == [
        {"metric_name": "revenue", "value": 1}
    ]


def test_parse_llm_json_strips_json_markdown_fence():
    raw = '```json\n{"year": 2025}\n```'
    assert parse_llm_json(raw) == {"year": 2025}


def test_parse_llm_json_strips_unlabeled_markdown_fence():
    raw = '```\n[{"value": 42}]\n```'
    assert parse_llm_json(raw) == [{"value": 42}]


def test_parse_llm_json_rejects_invalid_json():
    with pytest.raises(ValueError):
        parse_llm_json("not json")
