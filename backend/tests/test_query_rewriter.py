"""Tests for query rewriter — entity-aware, recency-first."""
from app.services.query_rewriter import (
    rewrite_query, _needs_rewrite, _heuristic_rewrite,
    _extract_entity, _extract_topic,
)

FAKE_SESSION = "test-session-999"


def test_clear_query_not_rewritten():
    needs, _ = _needs_rewrite("What is the MBA admission process at AIMS?")
    assert needs is False


def test_fees_with_entity():
    result = _heuristic_rewrite("and fees?", "fees", entity="MBA")
    assert "MBA" in result
    assert "fees" in result.lower()
    assert "AIMS College" in result


def test_fees_without_entity_fallback():
    result = _heuristic_rewrite("and fees?", "fees", entity=None)
    assert "fees" in result.lower()
    assert "AIMS College" in result


def test_no_topic_returns_original():
    result = _heuristic_rewrite("and that?", topic=None, entity=None)
    assert result == "and that?"


def test_entity_extraction():
    msgs = [{"role": "user", "content": "Tell me about MBA placements"}]
    assert _extract_entity(msgs) == "MBA"


def test_topic_recency_first():
    msgs = [
        {"role": "user",    "content": "hostel fees"},
        {"role": "assistant","content": "Hostel costs..."},
        {"role": "user",    "content": "what about placement?"},
    ]
    assert _extract_topic(msgs) == "placement"  # most recent wins


def test_pronoun_triggers_rewrite():
    needs, reason = _needs_rewrite("tell me about this")
    assert needs is True and reason == "pronoun"


def test_vague_phrase_triggers_rewrite():
    needs, reason = _needs_rewrite("what about hostel?")
    assert needs is True and reason == "vague_phrase"


def test_backward_compat():
    assert rewrite_query("fees") == "fees aims college"
    assert rewrite_query("") == ""


if __name__ == "__main__":
    print(_heuristic_rewrite("and fees?", "fees", "MBA"))
    print(_heuristic_rewrite("and hostel?", "hostel", "BBA"))
    print(_heuristic_rewrite("what about placement?", "placement", None))
