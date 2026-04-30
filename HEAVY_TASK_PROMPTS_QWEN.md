# HEAVY TASK PROMPTS - Copy & Paste Ready

Use these prompts to delegate work to Qwen 2.5 Coder 7B (fast) or Qwen 2.5 Coder 32B (deep reasoning).

---

## For Qwen 2.5 Coder 7B (Fast Execution)

Use when you need quick implementation, parallel tasks, rapid iteration.

---

### Prompt 1: Contradiction Detection Implementation

```
Implement a contradiction detection module for a conversational AI system.

Requirements:
- Input: previous profile state + new signals
- Detect contradictions across:
  * interests (like vs hate)
  * constraints (good vs bad)
  * goals (job vs entrepreneurship)

Output: structured contradictions with:
  {
    "type": "interest_conflict",
    "previous": "coding",
    "current": "hate coding",
    "severity": 0.85
  }

Then modify update_confidence_score():
- Apply penalty when contradiction exists
- Penalty must be proportional (e.g., -0.15 per contradiction)
- Maintain bounded delta constraint (±0.3)
- Ensure deterministic behavior

Constraints:
- NO randomness
- Production-ready code
- Full docstrings with examples
- Severity calculation logic included

Do NOT modify tone or decision layers. Return clean, production-ready code.
```

---

### Prompt 2: Robust Signal Extraction Implementation

```
Improve signal extraction for a chatbot to handle messy user input.

Requirements:
- Handle slang, informal language, broken grammar
- Extract multiple signals from a single sentence
- Detect:
  * ambiguity
  * weak clarity
  * strong clarity
  * goals
  * constraints

Input examples:
- "idk bro maybe coding but I suck at math lol"
- "money fast but don't wanna study"
- "coding maybe... or business idk"

Output: structured signals
{
  "type": "interest",
  "value": "coding",
  "confidence": 0.80,
  "clarity": "weak"
}

Requirements:
- Fuzzy matching (handle typos)
- Multi-signal extraction per sentence
- Confidence weighting per signal
- No ML models, rule-based only
- Deterministic results

Constraints:
- Keep deterministic
- No external ML libraries
- Full clarity detection logic
- Production-grade

Return production-ready code with examples and tests.
```

---

### Prompt 3: Integration of Both Systems

```
Create an integration module that combines contradiction detection + signal extraction.

The workflow should be:
1. Extract signals from messy user input
2. Compare against profile history
3. Detect contradictions
4. Apply confidence penalties
5. Generate system notes for tone layer

Input:
- User query (messy text)
- Student profile (current state)
- Profile history (past states)

Output:
{
  "signals": [...],
  "contradictions": [...],
  "confidence_update": {
    "old_confidence": 0.85,
    "new_confidence": 0.70,
    "penalty": 0.15,
    "is_stable": false
  },
  "profile_update": {...},
  "system_notes": [...]
}

Create main function:
  process_user_input_with_contradiction_detection(
    query, student_profile, profile_history
  ) → integration result

Include:
- Complete workflow example
- Test cases with real messy inputs
- Production integration points
- Performance notes

Code should be production-ready, fully documented.
```

---

## For Qwen 2.5 Coder 32B (Deep Reasoning)

Use when you need complex design, architectural decisions, optimization.

---

### Prompt 1: Contradiction Handling System Design

```
Design and implement a comprehensive contradiction handling system for a multi-turn conversational advisor.

Focus on these aspects:

1. Contradiction Detection Architecture:
   - Semantic contradiction detection across turns
   - Classify contradiction types:
     * direct contradiction (like/hate)
     * goal conflict (money vs passion)
     * constraint inconsistency
     * preference reversal

2. Severity Calculation:
   - How do you measure contradiction strength?
   - Account for:
     * confidence levels (both statements)
     * signal clarity
     * time between statements
     * domain specificity

3. Confidence Evolution Integration:
   - Design bounded penalty system (max ±0.3)
   - Ensure monotonic decrease (don't increase on contradiction)
   - How do users recover confidence?
   - Penalty decay vs immediate penalty

4. System Stability Under Stress:
   - Handle multiple contradictions per turn
   - Handle repeated contradictions (user keeps changing mind)
   - Prevent oscillation (confidence bouncing up/down)
   - Fallback behavior for ambiguous cases

5. Tone & Response Integration:
   - How should system acknowledge contradictions?
   - Should explicit mentions happen immediately or delayed?
   - How does contradiction affect recommendation confidence?
   - Examples of tone changes

Deliverables:
- Clean architecture with defined data structures
- Contradiction tracking mechanism
- Penalty calculation algorithm
- Confidence decay model
- System stability analysis
- Production code examples
- Behavior examples under 5 test cases

Do NOT touch decision logic or tone layer — only confidence engine design.

Output: comprehensive design document + clean code + test examples.
```

---

### Prompt 2: Robust Signal Extraction Architecture

```
Design a production-grade signal extraction system for real-world messy input.

Your system must handle:

1. Input Preprocessing:
   - Slang normalization strategy
   - Typo handling (fuzzy matching vs correction)
   - Grammar repair heuristics
   - Abbreviation expansion

2. Multi-Signal Extraction:
   - Algorithm for extracting multiple signals per sentence
   - Prevent over-extraction (false positives)
   - Handle compound signals ("coding AND finance")
   - Handle negations ("not coding")

3. Clarity Detection:
   - How do you measure user certainty from text?
   - Patterns that indicate weak signal:
     * hedging language ("maybe", "kinda")
     * negations ("I don't think")
     * question forms ("or should I?")
   - Patterns for strong signals

4. Confidence Weighting:
   - Combine source match strength + clarity signal
   - Fuzzy match confidence calculation
   - Multi-factor confidence scoring
   - When to trust vs when to be uncertain

5. Ambiguity Detection:
   - Metric for overall input clarity
   - Detect conflicting signals in same message
   - Identify when user is genuinely confused

6. No-ML Constraint:
   - How to achieve robustness without ML models?
   - Rule-based pattern matching
   - Heuristic algorithms
   - Knowledge engineering approach

7. Performance:
   - Ensure extraction runs in <50ms
   - Minimal memory footprint
   - No file I/O or network calls

Deliverables:
- Architecture document with decision justifications
- Signal extraction algorithm with pseudocode
- Fuzzy matching strategy
- Clarity detection rules
- Confidence calculation formula
- Production code with examples
- 5 real-world test cases with expected outputs
- Performance analysis

Output: comprehensive design + clean code + test suite.
```

---

### Prompt 3: System Pressure Testing & Stress Analysis

```
Design a comprehensive test suite and stress analysis for the contradiction + signal extraction system.

Your analysis should cover:

1. Contradiction Detection Stress Tests:
   - Multiple contradictions in short span
   - Conflicting signals at different confidence levels
   - Weak signals being contradicted by strong ones
   - User saying same thing 3 different ways
   - Complete goal reversal

   For each: expected system behavior, penalty application, tone adjustment

2. Signal Extraction Edge Cases:
   - Completely garbled input (multiple typos, no clear language)
   - Mixed languages (English + Hindi/local language)
   - Sarcasm and irony (user says opposite of what they mean)
   - Repetition (user says same thing multiple times)
   - Ambiguous statements that could mean 3 things

   For each: signal extraction attempt, confidence justification, ambiguity score

3. Integration Stress Tests:
   - User starts uncertain, becomes certain, becomes uncertain again
   - User contradicts themselves 3 turns in a row
   - High signal noise (many weak contradictory signals)
   - System should recommend despite contradictions
   - Confidence should never drop below 0.3

4. Stability Analysis:
   - Theoretical bounds on confidence (prove it stays in [0.3, 1.0])
   - Prove determinism (same input sequence = same output)
   - Reversibility (user can recover confidence)
   - No oscillation (confidence doesn't bounce)

5. Performance Under Load:
   - 100 consecutive messy inputs
   - Very long messages (1000+ words)
   - Deep conversation histories (50+ turns)
   - Profile with contradictions from past

   Measure: latency, memory, accuracy

6. Failure Modes:
   - What if profile history is corrupted?
   - What if user is completely confused?
   - What if signals are contradictory at source?
   - What if contradiction engine is off?

   For each: graceful fallback, user experience, error logging

Deliverables:
- Test suite with 20+ test cases
- Stress test results with metrics
- Theoretical stability proofs
- Performance analysis graphs
- Failure mode documentation
- Recommended thresholds/parameters
- Production readiness checklist

Output: comprehensive test analysis + metrics + recommendations.
```

---

## How to Use These Prompts

### For Qwen 7B (Fast Execution):
1. Copy one prompt at a time
2. Run with Qwen 7B
3. Get implementation in 2-3 minutes
4. Run all 3 in parallel for fastest delivery

### For Qwen 32B (Deep Reasoning):
1. Copy one prompt
2. Run with Qwen 32B (or high-memory 7B configuration)
3. Get deep analysis + design in 3-5 minutes
4. Use output for architecture decisions

### Recommended Workflow:

**Phase 1 (Parallel):**
- Qwen 7B Prompt 1 → Contradiction implementation
- Qwen 7B Prompt 2 → Signal extraction
- Qwen 32B Prompt 1 → Architecture review

**Phase 2 (Sequential):**
- Use Qwen 7B outputs as working code
- Use Qwen 32B analysis for validation
- Qwen 7B Prompt 3 → Final integration

**Phase 3 (Testing):**
- Qwen 32B Prompt 3 → Stress tests
- Run test suite on code
- Refine parameters based on results

---

## Parameter Tuning Prompts

If you need to optimize the system after initial implementation:

### Prompt: "Optimize for Production"

```
The contradiction engine and signal extractor are implemented.
Current parameters:
- Contradiction severity calculation: (opposite polarity) × (confidence product)
- Base penalty per contradiction: 0.15
- Max total penalty: 0.30
- Fuzzy match threshold: 0.75
- Clarity threshold for "weak": 0.60

Based on real usage data [INSERT YOUR METRICS]:
- False positive rate on contradictions: X%
- Missed contradictions: Y%
- Signal extraction precision: Z%
- Confidence penalty too aggressive/lenient: ?

Recommend optimal parameters with justification.
Include: formulas, thresholds, trade-offs, expected outcomes.
```

---

## Notes

- These prompts are optimized for **Qwen 2.5 Coder** family (7B, 32B)
- Qwen 7B: Fast, parallel-friendly, good for implementation
- Qwen 32B: Thorough, good for design and testing
- Both produce production-ready code
- Combine outputs for best results

---

## Usage Rights

These prompts can be:
- ✅ Used as-is for direct delegation
- ✅ Modified for your specific system
- ✅ Used to benchmark different models
- ✅ Shared with your team

They're optimized for:
- Clear problem statement
- Specific constraints
- Measurable outputs
- Production readiness
