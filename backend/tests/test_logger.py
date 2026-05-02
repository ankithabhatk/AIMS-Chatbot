"""Tests: structured logger — log_event, compute_confidence, analytics helpers."""
import app.services.logger as lg

_DICT_CHUNK  = lambda score: {"content": "MBA fee is ₹8.5 lakhs.", "score": score}
_TUPLE_CHUNK = lambda score: ("MBA fee is ₹8.5 lakhs.", score, "https://aims.ac.in", "MBA")


def setup_function():
    with lg._lock:
        lg._in_memory.clear()


# ── compute_confidence ────────────────────────────────────────────

def test_confidence_from_dict_scores():
    chunks = [_DICT_CHUNK(0.9), _DICT_CHUNK(0.7)]
    assert lg.compute_confidence(chunks) == round((0.9 + 0.7) / 2, 4)


def test_confidence_from_tuple_scores():
    chunks = [_TUPLE_CHUNK(0.8), _TUPLE_CHUNK(0.6)]
    assert lg.compute_confidence(chunks) == round((0.8 + 0.6) / 2, 4)


def test_confidence_heuristic_no_scores():
    chunks = [{"content": "text"}] * 3
    assert lg.compute_confidence(chunks) == round(3 / 5.0, 4)


def test_confidence_empty():
    assert lg.compute_confidence([]) == 0.0


def test_confidence_capped_at_one():
    chunks = [_DICT_CHUNK(1.0)] * 10
    assert lg.compute_confidence(chunks) <= 1.0


# ── log_event ─────────────────────────────────────────────────────

def test_log_event_stored_in_memory():
    lg.log_event(
        session_id="s1",
        query="What is MBA fee?",
        rewritten_query="What is the MBA fee at AIMS?",
        intent="fees",
        chunks=[_DICT_CHUNK(0.85)],
        confidence=0.85,
        response="The MBA fee is ₹8.5 lakhs.",
    )
    logs = lg.get_recent_logs(10)
    assert len(logs) == 1
    r = logs[0]
    assert r["query"] == "What is MBA fee?"
    assert r["session_id"] == "s1"
    assert r["intent"] == "fees"
    assert r["confidence"] == 0.85
    assert len(r["retrieved_chunks"]) == 1


def test_log_event_trims_long_response():
    lg.log_event(
        session_id="s2",
        query="q",
        response="A" * 600,
    )
    r = lg.get_recent_logs(1)[0]
    assert len(r["response"]) <= 402  # 400 + "…"


def test_log_event_trims_chunk_text():
    long_chunk = {"content": "X" * 300, "score": 0.8}
    lg.log_event(session_id="s3", query="q", chunks=[long_chunk])
    r = lg.get_recent_logs(1)[0]
    assert len(r["retrieved_chunks"][0]) <= 202


def test_log_event_max_3_chunks():
    chunks = [_DICT_CHUNK(0.9)] * 6
    lg.log_event(session_id="s4", query="q", chunks=chunks)
    r = lg.get_recent_logs(1)[0]
    assert len(r["retrieved_chunks"]) == 3


def test_log_event_disabled(monkeypatch):
    monkeypatch.setattr(lg, "ENABLE_LOGGING", False)
    before = len(lg.get_recent_logs(100))
    lg.log_event(session_id="sx", query="should not appear")
    assert len(lg.get_recent_logs(100)) == before


# ── Analytics helpers ─────────────────────────────────────────────

def test_get_avg_confidence():
    lg.log_event(session_id="a1", query="q1", confidence=0.8)
    lg.log_event(session_id="a2", query="q2", confidence=0.6)
    avg = lg.get_avg_confidence()
    assert abs(avg - 0.7) < 0.001


def test_get_avg_confidence_empty():
    assert lg.get_avg_confidence() == 0.0


def test_get_low_confidence_queries():
    lg.log_event(session_id="b1", query="low q", confidence=0.2)
    lg.log_event(session_id="b2", query="high q", confidence=0.9)
    low = lg.get_low_confidence_queries(threshold=0.4)
    assert all(r["confidence"] < 0.4 for r in low)
    queries = [r["query"] for r in low]
    assert "low q" in queries
    assert "high q" not in queries


def test_get_recent_logs_limit():
    for i in range(10):
        lg.log_event(session_id=f"r{i}", query=f"q{i}")
    assert len(lg.get_recent_logs(5)) == 5


# ── response_time_ms ──────────────────────────────────────────────

def test_log_event_records_response_time():
    lg.log_event(session_id="t1", query="q", response_time_ms=142)
    r = lg.get_recent_logs(1)[0]
    assert r["response_time_ms"] == 142


def test_log_event_response_time_none_by_default():
    lg.log_event(session_id="t2", query="q")
    r = lg.get_recent_logs(1)[0]
    assert r["response_time_ms"] is None


# ── error field ───────────────────────────────────────────────────

def test_log_event_records_error():
    lg.log_event(session_id="e1", query="q", error="NullPointerException")
    r = lg.get_recent_logs(1)[0]
    assert r.get("error") == "NullPointerException"


def test_log_event_no_error_key_when_none():
    lg.log_event(session_id="e2", query="q")
    r = lg.get_recent_logs(1)[0]
    assert "error" not in r


# ── scores list ───────────────────────────────────────────────────

def test_log_event_includes_scores_dict():
    chunks = [_DICT_CHUNK(0.91), _DICT_CHUNK(0.87), _DICT_CHUNK(0.83)]
    lg.log_event(session_id="sc1", query="q", chunks=chunks)
    r = lg.get_recent_logs(1)[0]
    assert r["scores"] == [0.91, 0.87, 0.83]


def test_log_event_includes_scores_tuple():
    chunks = [_TUPLE_CHUNK(0.9), _TUPLE_CHUNK(0.7)]
    lg.log_event(session_id="sc2", query="q", chunks=chunks)
    r = lg.get_recent_logs(1)[0]
    assert r["scores"] == [0.9, 0.7]


def test_log_event_scores_limited_to_3():
    chunks = [_DICT_CHUNK(float(s)) for s in [0.9, 0.8, 0.7, 0.6, 0.5]]
    lg.log_event(session_id="sc3", query="q", chunks=chunks)
    r = lg.get_recent_logs(1)[0]
    assert len(r["scores"]) == 3


# ── compute_confidence clamping ───────────────────────────────────

def test_confidence_clamps_above_1():
    chunks = [_DICT_CHUNK(1.5), _DICT_CHUNK(2.0)]
    assert lg.compute_confidence(chunks) == 1.0


def test_confidence_clamps_below_0():
    chunks = [_DICT_CHUNK(-0.5)]
    assert lg.compute_confidence(chunks) == 0.0


def test_confidence_exact_avg():
    chunks = [_DICT_CHUNK(0.91), _DICT_CHUNK(0.87), _DICT_CHUNK(0.83)]
    expected = round((0.91 + 0.87 + 0.83) / 3, 4)
    assert lg.compute_confidence(chunks) == expected
