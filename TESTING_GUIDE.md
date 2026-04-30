# Testing Guide - 100 Student Questions

## Overview

This testing suite contains **100 real student questions** across 7 categories, designed to comprehensively test the AIMS chatbot system.

---

## Files Created

### 1. `student_questions_100.py`
- **100 questions dataset** organized by category
- Categories: Admission (20), Fees (15), Courses (15), Placements (15), Campus (10), Hostel (10), Exploratory (15)
- Each question mapped to its category for analysis

### 2. `terminal_qa_tester.py`
- **Interactive terminal testing tool**
- Multiple modes: interactive, batch testing, category-specific
- Color-coded output for easy reading
- Detailed analysis and reporting

### 3. `quick_test_sample.py`
- Quick 10-question sample test
- 2 questions from each major category
- Fast verification of system status

---

## Usage

### Interactive Mode (Recommended for Manual Testing)

```bash
python terminal_qa_tester.py
```

or

```bash
python terminal_qa_tester.py interactive
```

**Features:**
- Type any question and get instant response
- Type `test <number>` to test a specific question from the dataset (1-100)
- Type `list` to see all 100 questions
- Type `quit` or `exit` to exit

**Example Session:**
```
You: What are the fees for BCA?
Q: What are the fees for BCA?
Intent: fees | Confidence: 1.00 | ✅ HIGH CONF

Answer:
--------------------------------------------------------------------------------
BCA fee structure:
Annual fee: ₹30,000 - ₹60,000
Contact admissions for exact figures.
Contact: admission@theaims.ac.in
--------------------------------------------------------------------------------

You: test 25
Testing question 25: I like coding, what should I choose?
...
```

---

### Run All 100 Tests

```bash
python terminal_qa_tester.py all
```

**Output:**
- Tests all 100 questions sequentially
- Shows progress with question number and category
- Displays intent, confidence, and answer preview for each
- Generates comprehensive summary report
- Saves results to `test_results_100.json`

**With Full Responses:**
```bash
python terminal_qa_tester.py all --full
```

---

### Test Specific Category

```bash
python terminal_qa_tester.py category admission_process
```

**Available Categories:**
- `admission_process` (20 questions)
- `fees_financial` (15 questions)
- `courses_programs` (15 questions)
- `placements_career` (15 questions)
- `campus_facilities` (10 questions)
- `hostel_accommodation` (10 questions)
- `exploratory_counselor` (15 questions)

---

### Quick Sample Test

```bash
python quick_test_sample.py
```

Tests 10 sample questions (2 from each major category) for quick verification.

---

## Question Categories

### 1. Admission Process & Requirements (20 questions)

**Topics:**
- Application basics (acceptance rate, deadlines, fee waivers)
- Requirements (tests, scores, portfolios, interviews)
- Documents & eligibility
- Process details (timeline, online application, next steps)

**Sample Questions:**
- "What is the university's current acceptance rate?"
- "What documents are required for admission?"
- "What is the eligibility criteria for MBA?"

---

### 2. Fees & Financial Aid (15 questions)

**Topics:**
- Fee structure (program-specific, installments, inclusions)
- Scholarships & aid (merit, financial aid, loans)
- Comparisons (value, total cost, hidden charges)

**Sample Questions:**
- "What are the fees for BCA?"
- "Are scholarships available for merit students?"
- "Can I pay fees in installments?"

---

### 3. Courses & Programs (15 questions)

**Topics:**
- Course offerings (available programs, specializations)
- Course details (duration, subjects, curriculum)
- Comparisons (BCA vs B.Sc, BBA vs B.Com, career options)

**Sample Questions:**
- "What courses are offered at AIMS?"
- "What specializations are available in MBA?"
- "Should I choose BCA or B.Sc Computer Science?"

---

### 4. Placements & Career (15 questions)

**Topics:**
- Placement stats (average package, highest package, placement rate)
- Career support (placement cell, internships, counseling)
- Specific queries (company names, roles, higher studies)

**Sample Questions:**
- "What is the placement record?"
- "Which companies come for campus recruitment?"
- "What are the placement opportunities for BCA students?"

---

### 5. Campus & Facilities (10 questions)

**Topics:**
- Infrastructure (library, classrooms, Wi-Fi, sports)
- Campus life (clubs, events, cafeteria, environment)

**Sample Questions:**
- "What facilities are available on campus?"
- "What is campus life like at AIMS?"
- "Are there student clubs and societies?"

---

### 6. Hostel & Accommodation (10 questions)

**Topics:**
- Hostel basics (availability, fees, room types)
- Hostel facilities (food, security, laundry, visitors)

**Sample Questions:**
- "Is hostel facility available?"
- "What are the hostel fees?"
- "Is there 24/7 security in hostels?"

---

### 7. Exploratory/Counselor Queries (15 questions)

**Topics:**
- Career confusion ("I like coding, what should I choose?")
- Vague queries ("Tell me everything about your college")
- Preference-based ("Which course has better scope?")

**Sample Questions:**
- "I like coding, what should I choose?"
- "I'm not sure what to study, can you help?"
- "Why should I join AIMS?"

**⚠️ Current Status:** These queries currently fall back to RAG. **Counselor layer needed** to handle them properly.

---

## Current Test Results

### Quick Sample Test (10 questions)
- **Good**: 8/10 (80%)
- **Fallback**: 2/10 (20%) - both exploratory queries
- **Error**: 0/10

### Expected Full Test Results (100 questions)
Based on brutal test (50 questions, 76% pass rate):
- **Good**: ~75-80 questions
- **Fallback**: ~20-25 questions (mostly exploratory)
- **Error**: 0-5 questions

---

## Response Quality Metrics

### Good Response
- ✅ Confidence >= 0.8
- ✅ Answer length > 50 chars
- ✅ Not a fallback
- ✅ Relevant to query

### Medium Response
- ⚠️ Confidence 0.5-0.8
- ⚠️ Partial answer
- ⚠️ May need improvement

### Poor Response
- ❌ Confidence < 0.5
- ❌ Very short answer
- ❌ Irrelevant content

### Fallback Response
- ⚠️ System couldn't find structured or RAG answer
- ⚠️ Returns generic snippet
- ⚠️ Needs counselor layer for exploratory queries

---

## Analysis Features

### Terminal Tester Provides:

1. **Real-time Testing**
   - Color-coded output (green = good, yellow = medium, red = poor)
   - Intent and confidence display
   - Answer preview or full response

2. **Comprehensive Summary**
   - Total questions tested
   - Success rate
   - Quality breakdown (good/medium/poor/fallback)
   - Category-wise performance
   - Average response time

3. **Detailed Results Export**
   - JSON file with all responses
   - Per-question analysis
   - Category mapping
   - Full response data (optional)

---

## Next Steps

### Phase 1: Information Engine ✅
- Structured Q&A: Working
- Multi-intent: Working
- RAG retrieval: Working

### Phase 2: Guidance Engine ⚠️ (Needed)
- **Problem**: 15-20 exploratory queries fall back
- **Solution**: Add counselor layer
- **Impact**: Will improve pass rate from 76% to ~95%

**Exploratory queries that need counselor layer:**
- "I like coding, what should I choose?"
- "I'm not sure what to study, can you help?"
- "Which course has better scope?"
- "I want a job quickly, which course?"

---

## Tips for Testing

### 1. Start with Interactive Mode
- Get familiar with system responses
- Test edge cases manually
- Verify specific categories

### 2. Run Category Tests
- Focus on problem areas
- Verify specific improvements
- Compare before/after changes

### 3. Run Full Test Suite
- Comprehensive system validation
- Generate baseline metrics
- Track improvements over time

### 4. Analyze Results
- Check `test_results_100.json` for details
- Identify patterns in failures
- Focus on low-performing categories

---

## Troubleshooting

### Backend Not Running
```
ERROR: Connection refused - is the backend running?
```

**Solution:**
```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Timeout Errors
```
ERROR: Request timeout
```

**Solution:**
- Increase timeout in `terminal_qa_tester.py` (line 30)
- Check backend performance
- Reduce test delay

### Rate Limiting
If testing too fast, add delay:
```bash
# In terminal_qa_tester.py, increase delay parameter
run_all_tests(show_full=False, delay=1.0)  # 1 second between queries
```

---

## Example Output

### Interactive Mode
```
================================================================================
INTERACTIVE Q&A MODE
================================================================================

Commands:
  - Type your question and press Enter
  - Type 'quit' or 'exit' to exit
  - Type 'test <number>' to test a specific question from the dataset
  - Type 'list' to see all 100 questions

You: What are the fees for MBA?

Q: What are the fees for MBA?
Intent: fees | Confidence: 1.00 | ✅ HIGH CONF

Answer:
--------------------------------------------------------------------------------
MBA fee structure:
Annual fee: ₹50,000 - ₹1,00,000
Varies by specialization. Contact admissions for exact figures.
Contact: admission@theaims.ac.in
--------------------------------------------------------------------------------

You: test 50
Testing question 50: I like coding, what should I choose?

Q: I like coding, what should I choose?
Intent: fallback | Confidence: 0.18 | ⚠️  FALLBACK

Answer Preview:
- BCA (Bachelor of Computer Applications) at AIMS Institutes: - Duration: 3 years...

You: quit

Goodbye!
```

---

## Summary

This testing suite provides:
- ✅ **100 real student questions** covering all major topics
- ✅ **Interactive terminal tool** for manual testing
- ✅ **Automated batch testing** for comprehensive validation
- ✅ **Category-specific testing** for focused analysis
- ✅ **Detailed reporting** with quality metrics
- ✅ **Export functionality** for result tracking

**Current Status**: 76-80% pass rate (information queries working, exploratory queries need counselor layer)

**Next Step**: Implement counselor layer to handle exploratory queries and reach 95%+ pass rate.
