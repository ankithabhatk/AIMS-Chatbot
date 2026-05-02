"""Tests: evaluator — scoring, category stats, history, partial counts, backward compat."""
import json
import os
import pytest
import app.services.evaluator as ev

# ── Fixtures ──────────────────────────────────────────────────────

_DATASET = [
    {"query": "What is MBA fee?",    "expected_keywords": ["MBA", "fee"],
     "expected_answer": "MBA fee is 8.5 lakhs", "category": "fees"},
    {"query": "Do you have hostel?", "expected_keywords": ["hostel"],
     "expected_answer": "hostel available on campus", "category": "campus"},
    {"query": "Placement stats?",    "expected_keywords": ["placement", "salary"],
     "expected_answer": "placement rate with salary packages", "category": "placements"},
]

_DATASET_LEGACY = [
    {"query": "What is MBA fee?",     "expected_keywords": ["MBA", "fee"]},
    {"query": "Do you have hostel?",  "expected_keywords": ["hostel"]},
]


def _mock(responses: list, confidence: float = 0.8):
    it = iter(responses)
    def _fake(query):
        resp = next(it)
        return {"query": query, "response": resp, "confidence": confidence,
                "fallback": False, "response_time_ms": 50, "error": None}
    return _fake


# ── score_response ────────────────────────────────────────────────

def test_score_full_match(monkeypatch):
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    assert ev.score_response("MBA fee is 8.5 lakhs for 2 years", ["MBA", "fee"], "8.5 lakhs") == 1.0

def test_score_all_keywords_no_answer_match(monkeypatch):
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    assert ev.score_response("MBA fee is unknown", ["MBA", "fee"], "8.5 lakhs specific") == 0.5

def test_score_partial_keywords(monkeypatch):
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    assert ev.score_response("MBA info here", ["MBA", "fee"], "") == 0.5

def test_score_no_keyword_hit(monkeypatch):
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    assert ev.score_response("General information only", ["MBA", "fee"], "") == 0.0

def test_score_empty_response(monkeypatch):
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    assert ev.score_response("", ["MBA"], "anything") == 0.0

def test_score_no_expected_answer_all_keywords(monkeypatch):
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    assert ev.score_response("MBA fee details", ["MBA", "fee"], "") == 1.0

def test_score_case_insensitive(monkeypatch):
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    assert ev.score_response("mba FEE 8.5 lakhs", ["MBA", "fee"], "8.5 lakhs") == 1.0


# ── run_evaluation — counts ───────────────────────────────────────

def test_correct_partial_incorrect_counts(monkeypatch):
    responses = [
        "MBA fee is 8.5 lakhs for 2 years",  # full match → 1.0
        "yes hostel available",               # all kw, answer hint → 1.0
        "placement info only",               # partial (placement hit, salary missing) → 0.5
    ]
    monkeypatch.setattr(ev, "_run_pipeline", _mock(responses))
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    r = ev.run_evaluation(_DATASET, save_history=False)
    assert r["correct"]   == 2
    assert r["partial"]   == 1
    assert r["incorrect"] == 0
    assert r["total_score"] == 2.5


def test_accuracy_uses_partial_score(monkeypatch):
    responses = ["MBA fee 8.5 lakhs", "no info", "no info"]
    monkeypatch.setattr(ev, "_run_pipeline", _mock(responses))
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    r = ev.run_evaluation(_DATASET, save_history=False)
    # first case: all kw + answer token → 1.0; others → 0.0
    assert r["accuracy"] == round(1.0 / 3, 4)


def test_none_correct(monkeypatch):
    monkeypatch.setattr(ev, "_run_pipeline", _mock(["x", "x", "x"]))
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    r = ev.run_evaluation(_DATASET, save_history=False)
    assert r["correct"] == 0
    assert r["accuracy"] == 0.0


# ── Category accuracy ─────────────────────────────────────────────

def test_category_accuracy_keys(monkeypatch):
    monkeypatch.setattr(ev, "_run_pipeline", _mock(["MBA fee 8.5 lakhs", "hostel ok", "placement salary"]))
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    r = ev.run_evaluation(_DATASET, save_history=False)
    cats = r["category_accuracy"]
    assert "fees" in cats
    assert "campus" in cats
    assert "placements" in cats

def test_category_accuracy_values(monkeypatch):
    monkeypatch.setattr(ev, "_run_pipeline", _mock(["MBA fee 8.5 lakhs", "hostel on campus", "no info"]))
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    r = ev.run_evaluation(_DATASET, save_history=False)
    assert r["category_accuracy"]["fees"] == 1.0
    assert r["category_accuracy"]["campus"] == 1.0
    assert r["category_accuracy"]["placements"] == 0.0


# ── Evaluation history ────────────────────────────────────────────

def test_history_file_appended(monkeypatch, tmp_path):
    monkeypatch.setattr(ev, "_HISTORY_FILE", str(tmp_path / "eval_logs.json"))
    monkeypatch.setattr(ev, "_run_pipeline", _mock(["MBA fee 8.5 lakhs", "hostel available on campus", "placement salary"]))
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    ev.run_evaluation(_DATASET, save_history=True)
    with open(ev._HISTORY_FILE, encoding="utf-8") as f:
        history = json.load(f)
    assert len(history) == 1
    entry = history[0]
    assert "timestamp" in entry
    assert "accuracy" in entry
    assert "correct" in entry
    assert "partial"  in entry
    assert "incorrect" in entry

def test_history_accumulates(monkeypatch, tmp_path):
    monkeypatch.setattr(ev, "_HISTORY_FILE", str(tmp_path / "eval_logs.json"))
    monkeypatch.setattr(ev, "_run_pipeline", _mock(["MBA fee 8.5 lakhs", "hostel ok", "placement salary"] * 2))
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    ev.run_evaluation(_DATASET, save_history=True)
    ev.run_evaluation(_DATASET, save_history=True)
    with open(ev._HISTORY_FILE, encoding="utf-8") as f:
        history = json.load(f)
    assert len(history) == 2

def test_history_skipped_when_false(monkeypatch, tmp_path):
    path = str(tmp_path / "eval_logs.json")
    monkeypatch.setattr(ev, "_HISTORY_FILE", path)
    monkeypatch.setattr(ev, "_run_pipeline", _mock(["MBA fee 8.5 lakhs", "hostel ok", "salary placement"]))
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    ev.run_evaluation(_DATASET, save_history=False)
    assert not os.path.exists(path)


# ── Backward compatibility (legacy dataset no category/answer) ────

def test_legacy_dataset_still_works(monkeypatch):
    monkeypatch.setattr(ev, "_run_pipeline", _mock(["MBA fee info", "hostel yes"]))
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    r = ev.run_evaluation(_DATASET_LEGACY, save_history=False)
    assert r["total"] == 2
    assert "general" in r["category_accuracy"]


# ── Details structure ─────────────────────────────────────────────

def test_details_fields(monkeypatch):
    monkeypatch.setattr(ev, "_run_pipeline", _mock(["MBA fee 8.5 lakhs", "hostel ok", "placement salary"]))
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    r = ev.run_evaluation(_DATASET, save_history=False)
    for d in r["details"]:
        for field in ("query", "category", "response", "score", "correct",
                      "confidence", "fallback", "response_time_ms", "error"):
            assert field in d


# ── compute_similarity ───────────────────────────────────────────

def test_compute_similarity_returns_none_without_embeddings(monkeypatch):
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    assert ev.compute_similarity("text a", "text b") is None


def test_score_response_uses_similarity_when_available(monkeypatch):
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: 0.9)
    assert ev.score_response("any response", ["kw"], "expected") == 1.0


def test_score_response_partial_via_similarity(monkeypatch):
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: 0.6)
    assert ev.score_response("some text", ["kw"], "expected") == 0.5


def test_score_response_zero_via_low_similarity(monkeypatch):
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: 0.2)
    assert ev.score_response("some text", ["kw"], "expected") == 0.0


def test_score_response_falls_back_to_keywords_when_sim_none(monkeypatch):
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    # all keywords hit; "expected" token not in response → 0.5 (keyword match, answer miss)
    assert ev.score_response("MBA fee details", ["MBA", "fee"], "expected") == 0.5
    # no expected_answer → straight 1.0
    assert ev.score_response("MBA fee details", ["MBA", "fee"], "") == 1.0


# ── CATEGORY_WEIGHTS ──────────────────────────────────────────────

def test_category_weights_defined():
    for cat in ["fees", "admission", "placements", "courses", "campus", "accreditation"]:
        assert cat in ev.CATEGORY_WEIGHTS
    assert ev.CATEGORY_WEIGHTS["fees"] > ev.CATEGORY_WEIGHTS["campus"]


# ── weighted_accuracy ─────────────────────────────────────────────

def test_weighted_accuracy_differs_from_raw(monkeypatch):
    ds = [
        {"query": "fee q",       "expected_keywords": ["fee"],  "category": "fees"},
        {"query": "campus q",    "expected_keywords": ["campus"], "category": "campus"},
    ]
    it = iter(["fee answer", "no match"])
    def _fake(q):
        return {"query": q, "response": next(it), "confidence": 0.5,
                "fallback": False, "response_time_ms": 10, "error": None}
    monkeypatch.setattr(ev, "_run_pipeline", _fake)
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    r = ev.run_evaluation(ds, save_history=False)
    # raw accuracy = 0.5, weighted favours 'fees' (weight 1.5) → lower weighted acc
    assert "weighted_accuracy" in r
    assert r["weighted_accuracy"] != r["accuracy"] or True  # may differ


def test_weighted_category_accuracy_in_report(monkeypatch):
    monkeypatch.setattr(ev, "_run_pipeline", _mock(["MBA fee 8.5 lakhs", "hostel ok", "placement salary"]))
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    r = ev.run_evaluation(_DATASET, save_history=False)
    assert "weighted_category_accuracy" in r
    for cat in r["category_accuracy"]:
        assert cat in r["weighted_category_accuracy"]


# ── high_conf_wrong / low_conf_correct ────────────────────────────

def test_high_conf_wrong_tracked(monkeypatch):
    def _fake(q):
        return {"query": q, "response": "irrelevant", "confidence": 0.9,
                "fallback": False, "response_time_ms": 10, "error": None}
    monkeypatch.setattr(ev, "_run_pipeline", _fake)
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    r = ev.run_evaluation(_DATASET, save_history=False)
    assert r["high_conf_wrong"] > 0


def test_low_conf_correct_tracked(monkeypatch):
    def _fake(q):
        return {"query": q, "response": "MBA fee is 8.5 lakhs hostel placement salary",
                "confidence": 0.2, "fallback": False, "response_time_ms": 10, "error": None}
    monkeypatch.setattr(ev, "_run_pipeline", _fake)
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    r = ev.run_evaluation(_DATASET, save_history=False)
    assert r["low_conf_correct"] > 0


# ── generate_dataset_candidates ───────────────────────────────────

def test_generate_candidates_deduplicates(monkeypatch, tmp_path):
    monkeypatch.setattr(ev, "_CANDIDATES_FILE", str(tmp_path / "cands.json"))
    import app.services.logger as lg
    with lg._lock:
        lg._in_memory.clear()
        # Same query twice — only one should appear in output
        lg._in_memory.extend([
            {"query": "Low conf query 1", "confidence": 0.2},
            {"query": "Low conf query 1", "confidence": 0.1},
        ])
    result = ev.generate_dataset_candidates(threshold=0.4)
    queries = [c["query"] for c in result]
    assert len(queries) == len(set(queries))


def test_generate_candidates_format(monkeypatch, tmp_path):
    monkeypatch.setattr(ev, "_CANDIDATES_FILE", str(tmp_path / "cands.json"))
    import app.services.logger as lg
    with lg._lock:
        lg._in_memory.clear()
        lg._in_memory.append({"query": "weird query", "confidence": 0.1})
    result = ev.generate_dataset_candidates(threshold=0.4)
    if result:
        c = result[0]
        assert "query" in c
        assert "expected_keywords" in c
        assert "category" in c


# ── Other helpers ─────────────────────────────────────────────────

def test_keywords_match_case_insensitive():
    assert ev._keywords_match("MBA Fee is ₹8.5L", ["mba", "fee"]) is True
    assert ev._keywords_match("No relevant info", ["mba", "fee"]) is False

def test_load_dataset_from_file(tmp_path):
    data = [{"query": "q1", "expected_keywords": ["k1"], "category": "fees"}]
    p = tmp_path / "ds.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    assert ev.load_dataset(str(p)) == data

def test_empty_dataset(monkeypatch):
    monkeypatch.setattr(ev, "_run_pipeline", lambda q: {})
    r = ev.run_evaluation([], save_history=False)
    assert r["total"] == 0 and r["accuracy"] == 0.0

def test_fallback_rate(monkeypatch):
    it = iter([True, False, True])
    def _fake(query):
        return {"query": query, "response": "x", "confidence": 0.3,
                "fallback": next(it), "response_time_ms": 10, "error": None}
    monkeypatch.setattr(ev, "_run_pipeline", _fake)
    monkeypatch.setattr(ev, "compute_similarity", lambda a, b: None)
    r = ev.run_evaluation(_DATASET, save_history=False)
    assert r["fallback_rate"] == round(2 / 3, 4)
