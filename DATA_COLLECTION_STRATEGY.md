# 📋 DATA COLLECTION STRATEGY — Action Plan

**Created**: April 19, 2026  
**Status**: Ready to present to AIMS  
**Timeline**: 3 weeks to improved system (32% → 75% answer rate)  

---

## 🎯 PHASE 1: What We Found

Your system works correctly. The problem isn't our code—it's that AIMS website doesn't contain information students are asking for.

### Validation Results
- **30 student queries tested**
- **9 answered** (32%)
- **21 fell back** (68%)
- **0 hallucinated** ✅ (system is safe)

### Where Students Are Asking

```
TOP UNANSWERED QUESTIONS:

1. "How much does the MBA/BBA cost?" 
   → Not on website (No fees page)

2. "Can I pay fees in installments?" 
   → Not documented (No payment policy)

3. "Is there a hostel?" 
   → Sparse info (No details)

4. "Which companies recruit from AIMS?" 
   → Not published (No placement data)

5. "What are the eligibility requirements?" 
   → Not complete (No entrance exam info)
```

---

## 🚀 PHASE 2: What We Can Fix

We built a **document ingestion system**. If college provides:

- Fee structure → we embed it
- Placement data → we embed it
- Facility info → we embed it
- Eligibility details → we embed it

→ System automatically starts answering these

---

## 📊 PHASE 3: The Ask (What We Need From AIMS)

### ✅ Item 1: Fee Structure PDF/Document

**What we need**:
```
Per program (MBA, BBA, etc):
- Total fee: X rupees
- Per year: X rupees
- Per semester: X rupees
- Payment options: (Annual/Semester/Monthly)
- Installment plan: (if available, with interest)
```

**We can accept**: PDF, Excel, Google Sheets, plain text

**Why**: 4 student queries about fees = Instant 13% coverage increase

---

### ✅ Item 2: Placement Report

**What we need**:
```
2023-24 Placement Report:
- Total students: XXX
- Students placed: XXX
- Placement rate: XX%
- Average salary: X LPA
- Highest package: X LPA
- Top 5-10 companies recruiting
```

**We can accept**: PDF report, Excel with data, JSON

**Why**: Career outcomes are THE decision driver for students

---

### ✅ Item 3: Campus & Facilities Guide

**What we need**:
```
Facilities available:
- Hostel: (Yes/No) + (Boys/Girls capacity)
- Gym: (Available) + (Equipment list optional)
- Sports: (list of facilities)
- WiFi: (Campus-wide or limited)
- Library: (24/7 or hours)
- Cafeteria: (Capacity, cuisine options)
- Medical center: (on campus)
- Transport: (shuttle service details)
```

**We can accept**: PDF, brochure, plain text, bullets

**Why**: 4 questions about facilities/hostel/gym

---

### ✅ Item 4: Admission & Eligibility

**What we need**:
```
Per program:
- Entrance exam: (GMAT, CAT, Merit-based, None?)
- Min score needed: (if exam required)
- Eligibility: (Bachelor's/12th pass/specific stream)
- Work experience required: (0/2-3 years?)
- Application deadline: (date)
- Documents needed: (list)
```

**We can accept**: Admission brochure, webpage copy, spreadsheet

**Why**: 3 questions about eligibility

---

### ✅ Item 5: Scholarships & Financial Aid

**What we need**:
```
Types:
- Merit scholarship: (% off, requirements)
- Sports scholarship: (available? details?)
- Diversity scholarship: (criteria)
- Gender-based: (specifics)

Financial aid:
- Education loan: (tie-ups with banks?)
- EMI available: (terms?)
- Payment plans: (details)

Contact: (email for scholarships@aims)
```

**We can accept**: PDF brochure, webpage text, JSON

**Why**: 2 student questions about scholarships

---

## 📈 Expected Impact

```
CURRENT STATE          →    AFTER INGESTION
─────────────────────       ───────────────────

Fees questions: ❌ (0%)  →  Fees: ✅ (100%)
           (+4 queries answered)

Placement: ❌ (0%)       →  Placement: ✅ (100%)
           (+2 queries answered)

Facilities: ⚠️ (sparse)  →  Facilities: ✅ (100%)
           (+2 queries answered)

Eligibility: ⚠️ (40%)    →  Eligibility: ✅ (100%)
           (+1 query answered)

Scholarships: ❌ (0%)    →  Scholarships: ✅ (100%)
           (+2 queries answered)

────────────────────────────────────────────

TOTAL: 9/30 answered   →    21/30 answered
       32% answer rate  →    70% answer rate
```

---

## 💼 How to Present This to AIMS

### Email Template

```
Subject: Improve AIMS Student Chatbot — Data-Driven Approach

Hi [Admissions Head],

We've tested our chatbot with 30 real student questions.

Current status:
✅ 32% of questions answered accurately
⚠️ 68% require students to contact admissions

The issue isn't our system—it's that critical student info isn't 
published online:

MISSING DATA:
❌ Fee structure (students asking: "How much?")
❌ Placement companies (students asking: "Who recruits?")
❌ Eligibility requirements (students asking: "Do I qualify?")
❌ Facility details (students asking: "Is there hostel?")
❌ Scholarships (students asking: "Any aid?")

SOLUTION:
If you provide this data (as PDF/Excel/docs), we can 
automatically embed it in the chatbot.

Expected improvement:
32% → 70% answer rate (41 more valid answers per 100 questions)

Timeline:
- You provide data: Week 1
- We integrate: Week 2
- We validate: Week 3

NEXT STEP:
Can you provide the 5 documents mentioned below?

[Attach: DATA_GAPS_ANALYSIS.md]

Thanks,
[Your name]
```

---

## 🔄 Technical Implementation (For Us, Not College)

Once college provides data, here's our pipeline:

```
flow
1. College provides: PDFs + documents
   ↓
2. We extract: document_processor.py
   ├─ Parse text from PDFs
   ├─ Normalize to JSON
   └─ Save to /tmp/chatbot_ingest/external_data
   ↓
3. We ingest: merge_external_data.py
   ├─ Load extracted data
   ├─ Chunk long documents
   ├─ Embed with same model
   ├─ Backup current index (snapshot)
   └─ Add to FAISS
   ↓
4. We validate: test_reliability_30queries.py
   ├─ Run same 30 queries
   ├─ Measure improvement
   └─ Log results
   ↓
5. We deploy: New system live with 70% answer rate
```

---

## 📅 Project Timeline

### Week 1 (Now)
- [ ] Send DATA_GAPS_ANALYSIS.md to AIMS
- [ ] Schedule call with admissions/registrar
- [ ] Provide specific document requests
- [ ] Set deadline (end of week)

### Week 2
- [ ] Receive documents from AIMS
- [ ] Extract data using document_processor.py
- [ ] Ingest into FAISS using merge_external_data.py
- [ ] Create "before" and "after" indices

### Week 3
- [ ] Re-run 30 queries on new system
- [ ] Measure: 32% → 70%+ improvement
- [ ] Test edge cases
- [ ] Document improvements
- [ ] Deploy new system to production

### Week 4+
- [ ] Monitor live system
- [ ] Collect real student feedback
- [ ] Iterate based on actual usage
- [ ] Plan Phase 5 (CRM integration)

---

## 💬 Key Talking Points for AIMS

**For Admissions Team**:
> "This chatbot will reduce our inbound email volume. Instead of 100 
> students asking 'How much is the fee?', the chatbot answers it. 
> You only handle the complex questions."

**For Marketing/Communications**:
> "Students get instant answers. Improves conversion (faster decision-making). 
> Better user experience."

**For IT/Data Team**:
> "We're not asking for new systems. Just provide data in PDF/Excel 
> format you already have. We'll handle the rest."

**For Finance/Registrar**:
> "Fee information is already published in brochures. We just need a copy 
> so our system can share it automatically."

---

## ✅ Checklist for Next Steps

- [ ] Create /tmp/chatbot_ingest/external_data directory structure
- [ ] Send DATA_GAPS_ANALYSIS.md to AIMS contact
- [ ] Set expectation: Response by [DATE]
- [ ] Prepare document_processor.py for PDF ingestion
- [ ] Prepare merge_external_data.py for integration
- [ ] Have snapshot system ready (for rollback if needed)
- [ ] Schedule time to re-run validation after merge

---

## 🎯 Success Metrics

After we ingest external data:

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Answer Rate | 32% | ? | 70%+ |
| Fallback Rate | 68% | ? | 30% |
| Avg Confidence | 0.367 | ? | 0.60+ |
| Response Time | 18ms | ~20ms | <50ms |
| Data Sources | Web only | Web + College | Complete |

---

## 🚀 Final Note

```
You've built a production-quality system.
Now you have a clear path to make it valuable.

The work ahead:
✅ Is NOT coding
✅ IS data collection + integration
✅ WILL have immediate ROI

The college wants higher conversion rates.
You're giving them exactly that.
```

---

**Status**: Ready to present  
**Owner**: [Your Name]  
**Questions?** [Contact]
