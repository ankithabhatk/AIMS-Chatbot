"""Tests: prompt_builder context injection, fallback, dedup, ranking, validation, UX."""
from app.services.llm.prompt_builder import (
    build_context, build_messages, is_fallback_answer, validate_answer,
    apply_grounding_prefix, next_fallback,
    FALLBACK_ANSWER, GROUNDING_PREFIX, PARTIAL_PREFIX, _FALLBACK_VARIANTS, _MAX_CHUNKS,
    _sentence_safe_trim, _fallback_counter,
)
import app.services.llm.prompt_builder as pb

_CHUNK_DICT = lambda h, c: {"heading": h, "content": c}
_CHUNK_TUPLE = lambda h, c: (c, 0.85, "https://aims.ac.in", h)

MBA_FEE_CHUNK = _CHUNK_DICT("MBA Fees", "The total MBA fee at AIMS is ₹8.5 lakhs for 2 years.")
EMPTY_CHUNK   = _CHUNK_DICT("", "")
LONG_CHUNK    = _CHUNK_DICT("Hostel", "A" * 500)


def test_build_context_dict_chunks():
    ctx = build_context([MBA_FEE_CHUNK])
    assert "MBA" in ctx or "8.5" in ctx


def test_build_context_tuple_chunks():
    ctx = build_context([_CHUNK_TUPLE("MBA Fees", "Fee is ₹8.5 lakhs.")])
    assert "8.5" in ctx


def test_build_context_trims_long_chunk():
    ctx = build_context([LONG_CHUNK])
    assert len(ctx) < 500


def test_build_context_skips_empty():
    ctx = build_context([EMPTY_CHUNK])
    assert ctx == ""


def test_build_context_deduplicates():
    duplicate = [MBA_FEE_CHUNK, MBA_FEE_CHUNK, MBA_FEE_CHUNK]
    ctx = build_context(duplicate)
    assert ctx.count("MBA") <= 2  # heading appears once per unique chunk


def test_build_context_max_chunks():
    chunks = [_CHUNK_DICT(f"H{i}", f"Content {i} info.") for i in range(10)]
    ctx = build_context(chunks)
    parts = [p for p in ctx.split("\n\n") if p]
    assert len(parts) <= _MAX_CHUNKS


def test_build_messages_structure():
    msgs = build_messages("What is MBA fee?", [MBA_FEE_CHUNK])
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"
    assert "8.5" in msgs[1]["content"] or "MBA" in msgs[1]["content"]
    assert "What is MBA fee?" in msgs[1]["content"]


def test_build_messages_empty_chunks():
    msgs = build_messages("What is MBA fee?", [])
    assert "No relevant information" in msgs[1]["content"]


def test_system_prompt_contains_fallback_instruction():
    msgs = build_messages("query", [MBA_FEE_CHUNK])
    system = msgs[0]["content"]
    assert "primarily" in system
    assert "context" in system.lower()


def test_is_fallback_answer_canonical():
    assert is_fallback_answer(FALLBACK_ANSWER) is True
    assert is_fallback_answer("The MBA fee is ₹8.5 lakhs.") is False
    assert is_fallback_answer("") is False


def test_is_fallback_answer_all_variants():
    for v in _FALLBACK_VARIANTS:
        assert is_fallback_answer(v) is True, f"Variant not detected: {v}"


# ── Sentence-safe trim ────────────────────────────────────────────

def test_sentence_safe_trim_cuts_at_dot():
    sentence = "AIMS offers MBA programs. "
    text = sentence * 20  # 520 chars — well over 380
    result = _sentence_safe_trim(text, 380)
    assert result.endswith(".")
    assert len(result) <= 380


def test_sentence_safe_trim_short_passthrough():
    text = "Short text."
    assert _sentence_safe_trim(text, 380) == text


def test_sentence_safe_trim_no_dot_uses_space():
    text = "A" * 200 + " " + "B" * 200
    result = _sentence_safe_trim(text, 380)
    assert len(result) <= 382  # ≤380 + "…"


# ── Ranking labels ────────────────────────────────────────────────

def test_context_has_ranking_labels():
    chunks = [
        _CHUNK_DICT("MBA Fees", "Fee is ₹8.5 lakhs."),
        _CHUNK_DICT("Hostel", "Hostel available on campus."),
    ]
    ctx = build_context(chunks)
    assert "[1] Most relevant" in ctx
    assert "[2] Next relevant" in ctx


def test_context_heading_in_label():
    ctx = build_context([MBA_FEE_CHUNK])
    assert "MBA Fees" in ctx


# ── validate_answer ───────────────────────────────────────────────

def test_validate_empty_returns_fallback():
    assert is_fallback_answer(validate_answer(""))
    assert is_fallback_answer(validate_answer("   "))


def test_validate_too_short_returns_fallback():
    assert is_fallback_answer(validate_answer("OK"))


def test_validate_vague_it_depends_returns_fallback():
    assert is_fallback_answer(validate_answer("It depends on the program you choose."))


def test_validate_vague_not_sure_returns_fallback():
    assert is_fallback_answer(validate_answer("I'm not sure about this topic at all."))


def test_validate_good_answer_passes():
    answer = "The MBA fee at AIMS is ₹8.5 lakhs for 2 years."
    assert validate_answer(answer) == answer


# ── apply_grounding_prefix ────────────────────────────────────────

def test_grounding_prefix_added_to_good_answer():
    answer = "MBA fee is ₹8.5 lakhs."
    result = apply_grounding_prefix(answer)
    assert result.startswith(GROUNDING_PREFIX)


def test_grounding_prefix_not_added_to_fallback():
    result = apply_grounding_prefix(FALLBACK_ANSWER)
    assert not result.startswith(GROUNDING_PREFIX)


def test_grounding_prefix_not_duplicated():
    prefixed = GROUNDING_PREFIX + "MBA fee is ₹8.5 lakhs."
    result = apply_grounding_prefix(prefixed)
    assert result.count(GROUNDING_PREFIX) == 1


# ── System prompt relaxed constraint ─────────────────────────────

def test_system_prompt_relaxed_not_only():
    msgs = build_messages("query", [MBA_FEE_CHUNK])
    system = msgs[0]["content"]
    assert "primarily" in system
    assert "ONLY" not in system


# ── Fallback rotation ─────────────────────────────────────────────

def test_next_fallback_rotates():
    pb._fallback_counter = 0
    v0 = next_fallback()
    v1 = next_fallback()
    v2 = next_fallback()
    v3 = next_fallback()
    assert v0 == _FALLBACK_VARIANTS[0]
    assert v1 == _FALLBACK_VARIANTS[1]
    assert v2 == _FALLBACK_VARIANTS[2]
    assert v3 == _FALLBACK_VARIANTS[0]  # wraps


def test_validate_triggers_rotation():
    pb._fallback_counter = 0
    r0 = validate_answer("")          # triggers variant 0
    r1 = validate_answer("OK")        # triggers variant 1 (< 20 chars)
    assert is_fallback_answer(r0)
    assert is_fallback_answer(r1)
    assert r0 != r1                   # different variants


# ── Expanded vague phrase detection ──────────────────────────────

def test_validate_not_clearly_specified():
    assert is_fallback_answer(validate_answer("That is not clearly specified in the docs."))


def test_validate_not_mentioned():
    assert is_fallback_answer(validate_answer("This is not mentioned anywhere in context."))


def test_validate_no_information_available():
    assert is_fallback_answer(validate_answer("No information available for this query."))


def test_validate_cannot_be_determined():
    assert is_fallback_answer(validate_answer("This cannot be determined from the data."))


def test_validate_unclear_from_context():
    assert is_fallback_answer(validate_answer("This is unclear from context provided here."))


# ── Partial prefix ────────────────────────────────────────────────

def test_partial_prefix_for_hedged_answer():
    answer = "The fee may vary depending on the program selected."
    result = apply_grounding_prefix(answer)
    assert result.startswith(PARTIAL_PREFIX)


def test_strong_prefix_for_direct_answer():
    answer = "The MBA fee at AIMS is ₹8.5 lakhs for 2 years."
    result = apply_grounding_prefix(answer)
    assert result.startswith(GROUNDING_PREFIX)


def test_apply_prefix_idempotent_partial():
    answer = PARTIAL_PREFIX + "Fee might vary."
    assert apply_grounding_prefix(answer) == answer


def test_apply_prefix_idempotent_strong():
    answer = GROUNDING_PREFIX + "Fee is ₹8.5 lakhs."
    assert apply_grounding_prefix(answer) == answer
