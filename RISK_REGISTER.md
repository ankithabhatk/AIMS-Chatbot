# RISK REGISTER & MITIGATION STRATEGIES

## Overview

This document outlines all identified risks, their impact/probability, and mitigation strategies.

---

## Tier 1: CRITICAL RISKS (Can halt project)

### Risk #1: LLM Hallucination Rate Exceeds Tolerance

**Description:** Chatbot gives false information about admissions, programs, or requirements.

**Example Scenarios:**
- "B.Tech CS only accepts 50 students" (when it's 500)
- "Admission closes Dec 31" (when it's actually Jan 15)
- "Placements at Google is 100%" (misleading)

**Impact:** 
- **Severity:** 9/10 (destroys credibility)
- **Business Loss:** Negative impressions, student frustration, legal liability
- **Recovery Time:** 2-4 weeks (requires prompt tuning + data collection)

**Probability:** 
- **GPT-3.5:** 15-20% (1 in 5-7 responses)
- **GPT-4:** 5-10% (1 in 10-20 responses)
- **Fine-tuned:** 2-5% (with good data)

**Detection Method:**
```python
# We can't detect 100% of hallucinations, but can reduce exposure:

# 1. Confidence Scoring
confusion_matrix = compare_response_to_context(response, retrieved_chunks)
if confidence < 0.7:
    use_fallback("I'm not certain. Contact admissions...")

# 2. Semantic Drift Detection
response_embedding = embed(response)
max_similarity = max([cosine(response_embedding, embed(chunk)) 
                      for chunk in context_chunks])
if max_similarity < 0.6:
    flag_for_manual_review()

# 3. Specific Answer Patterns
hallucination_patterns = [
    r'\d+%\s+(placement|salary)',  # Exact percentages (risky)
    r'(will|must|definitely|guaranteed)',  # Overconfident language
    r'only?\s+\d+\s+(students|seats)',  # Specific seat numbers
]
if any(re.search(p, response, re.I) for p in hallucination_patterns):
    require_confidence > 0.85
```

**Mitigation Strategy (Priority 1):**

1. **Strict Guardrails** (Week 5)
   - Implement confidence threshold (>0.75)
   - Force fallback on low confidence
   - Test on 100 pre-built Q&A pairs

2. **Prompt Engineering** (Week 5-6)
   - Refine system prompt: "ONLY use provided context"
   - Add examples of good/bad responses
   - Test 10+ prompt templates
   - Measure hallucination rate on test set

3. **Manual Review Process** (Week 6)
   - Establish review workflow: suspicious responses → human check
   - Train admissions team to flag incorrect responses
   - Feedback loop: flagged responses → improve prompt
   - Weekly review (target: 0 false positives from manual check)

4. **Response Validation** (Week 6)
   - Auto-extract claims from response
   - Validate against context chunks
   - Score confidence per claim
   - Flag mixed-confidence responses

5. **Monitoring & Alerting** (Week 9)
   - Collect user feedback ("Was this helpful?")
   - Dashboard showing hallucination rate
   - Alert if hallucination rate > 10%

6. **Contingency** (Phase 2)
   - Fine-tune GPT-3.5 on college-specific data
   - Expected improvement: 50% reduction in hallucinations
   - Cost: 2 weeks engineer time + $100

**Success Criteria:**
- Hallucination rate ≤ 5% (measured on test set)
- Zero critical errors found in QA testing
- All user-flagged errors in first month act as learning data

---

### Risk #2: Scraper Breaks Due to Website Changes

**Description:** College website structure changes, scraper CSS selectors no longer match.

**Result:** Zero documents scraped → knowledge base becomes stale → chatbot becomes useless within weeks.

**Example Scenarios:**
- College redesigns homepage
- URL structure changes (/programs → /academics/programs)
- Dynamic content moved to JavaScript
- PDF links moved to different section

**Impact:**
- **Severity:** 8/10 (system becomes non-functional in 2-3 weeks)
- **Probability:** 30-40% chance in first year (college websites change frequently)
- **Detection Latency:** 24 hours (daily scrape) to 7 days (if not monitoring)

**Detection Method:**
```python
# Monitor scraper health
async def monitor_scraper_health():
    last_successful_scrape = await db.fetch_one(
        "SELECT MAX(scraped_at) FROM documents"
    )
    
    hours_since_scrape = (
        datetime.now() - last_successful_scrape
    ).total_seconds() / 3600
    
    if hours_since_scrape > 30:  # No scrape in 30 hours
        alert_ops_team()
    
    # Content freshness check
    known_content = "B.Tech Computer Science"
    if known_content not in latest_documents:
        alert_ops_team("Content missing or moved")
```

**Mitigation Strategy (Priority 1):**

1. **Alert System** (Week 2)
   - Monitor scraper success/failure
   - Alert if: no docs scraped in 24 hours
   - Alert if: expected content missing
   - Send to Slack / email ops team
   - SLA: Ops team responds within 2 hours

2. **Selector Monitoring** (Week 2-3)
   - Log which selectors matched
   - Track match rate: (docs found / expected docs)
   - Alert if match rate drops below 80%
   - Example: "Expected 10 program pages, found 6 → selector broken"

3. **Content Archiving** (Week 2)
   - Keep 30-day history of all documents
   - If scraper breaks, serve stale docs with warning:
     "Information last updated 2024-01-15. Please verify."
   - Buys time for manual fix

4. **Manual Scraping Fallback** (Week 3)
   - Maintain manual data sources:
     * College PDF brochures (updated monthly)
     * Google Drive with static FAQs
     * Contact info for manual updates
   - If auto-scraper broken >3 days, activate manual process

5. **Redundant Selectors** (Week 3-4)
   - Don't rely on one CSS selector
   - Try multiple paths to find content:
     ```python
     selectors = [
         'div.program-title h1',  # Primary
         'h1[data-type="program"]',  # Alternative 1
         'section.academics h1',  # Alternative 2
     ]
     for selector in selectors:
         if content := soup.select_one(selector):
             return content
     ```

6. **Weekly Manual Audit** (Week 9+, ongoing)
   - Admissions team spot-checks 5-10 pages monthly
   - "Does chatbot have correct info for [program]?"
   - Raises issues → ops team fixes selector

7. **Contingency** (Phase 2)
   - Hire student (500 INR/month) to maintain data
   - OR: Direct integration with college portal API (if available)

**Success Criteria:**
- Scraper failure detected within 24 hours
- Ops team fixes broken selectors within 48 hours
- Stale data warning displayed to users
- Zero users encounter completely outdated information

---

### Risk #3: Salesforce Sync Data Loss / Duplication

**Description:** Leads don't sync to CRM, or duplicate leads created, causing lost revenue and admissions chaos.

**Impact:**
- **Severity:** 7/10 (affects business process)
- **Probability:** 20% (CRM integrations notoriously fragile)
- **Business Loss:** Admissions team doesn't see leads → no follow-up → lost conversions

**Example Scenarios:**
- SF API returns 500 error → lead queued but never retried
- Same email submitted twice → two leads created in SF
- SF sync fails silently → lead sits in "pending" state forever
- Duplicate in SF AND database, but under different names

**Detection Method:**
```python
# Monitor sync health
async def validate_lead_sync():
    pending_leads = await db.fetch(
        "SELECT COUNT(*) FROM leads WHERE sf_sync_status = 'pending'"
    )
    
    if pending_leads > 10:
        alert_ops_team("High number of pending syncs")
    
    # Check for duplicates
    duplicate_check = await db.fetch("""
        SELECT email, COUNT(*) as count FROM leads
        GROUP BY email HAVING COUNT(*) > 1
    """)
    
    if duplicate_check:
        alert_ops_team(f"Duplicates detected: {duplicate_check}")
    
    # Reconciliation: DB vs SF
    db_count = await db.fetch_one("SELECT COUNT(*) FROM leads")
    sf_count = await salesforce_client.get_lead_count()
    
    if abs(db_count - sf_count) > 5:
        alert_ops_team("DB and SF counts diverged")
```

**Mitigation Strategy (Priority 1):**

1. **Async Queue with Retry Logic** (Week 7-8)
   ```python
   # Use Celery + Redis for reliable async processing
   from celery import shared_task
   from celery.exceptions import Retry
   
   @shared_task(bind=True, max_retries=3)
   def sync_lead_to_salesforce(self, lead_id):
       try:
           lead = db.get_lead(lead_id)
           salesforce_client.create_lead(lead)
           db.update_lead(lead_id, sf_sync_status='synced')
       except SalesforceAPIError as e:
           # Retry with exponential backoff: 5s, 30s, 5min
           retry_in = 5 ** self.request.retries
           raise self.retry(exc=e, countdown=retry_in)
   
   # When lead captured
   sync_lead_to_salesforce.delay(lead_id)
   ```

2. **Deduplication Logic** (Week 7)
   ```python
   def check_für_duplicates(new_lead):
       # Query Salesforce for existing leads
       existing_leads = salesforce_client.search_leads(
           email=new_lead.email
       )
       
       if existing_leads:
           # Update instead of create
           return salesforce_client.update_lead(
               existing_leads[0].id,
               new_lead.data()
           )
       else:
           return salesforce_client.create_lead(new_lead.data())
   ```

3. **Dual-Write with Reconciliation** (Week 8)
   ```python
   # Write to both DB and SF, then reconcile
   lead_id = await db.create_lead(lead_data)
   sf_response = await salesforce_client.create_lead(lead_data)
   
   await db.update_lead(lead_id, {
       'salesforce_id': sf_response.id,
       'sf_sync_status': 'synced'
   })
   
   # Nightly reconciliation job
   # Compare DB leads with SF leads by email
   # Flag mismatches
   ```

4. **Monitoring Dashboard** (Week 9)
   - Total leads captured (DB)
   - Total leads synced to SF
   - Pending sync count
   - Failed sync count
   - Duplicate rate
   - Alert if: pending > 5 OR failed > 3

5. **Weekly Audit** (Week 9+, ongoing)
   - SF admin spot-checks: "Do lead counts match?"
   - Manual sync of any stragglers
   - Document any api issues

6. **Contingency Plan** (Phase 2)
   - If SF API down >1 hour: Queue leads locally, batch sync when API back
   - If sync completely broken: Manual CSV export → SF import

**Success Criteria:**
- 99%+ lead sync success rate (retries account for transient errors)
- Zero duplicate leads in SF
- Manual audit finds no drift
- Admissions team reports all leads visible in CRM

---

## Tier 2: HIGH-RISK Issues (Cause significant degradation)

### Risk #4: Vector Retrieval Returning Irrelevant Chunks

**Description:** Semantic search doesn't find the right information, returning chunks that seem related but don't answer the question.

**Impact:**
- **Severity:** 7/10 (degrades answer quality)
- **Probability:** 20% (retrieval is hard!)

**Example:**
- Q: "What's the fee structure?"
- Retrieved: Chunks about dining plans, scholarships (mentioned "fees")
- Result: LLM gives wrong answer based on irrelevant context

**Mitigation:**
1. **Chunking & Overlapping** (Week 3-4)
   - Test different chunk sizes (128, 256, 512 tokens)
   - Add overlapping chunks (50-100 token overlap)
   - Measure: precision & recall on 20-question test set

2. **Embedding Quality** (Week 4-5)
   - Use better embedding model (OpenAI > Sentence-Transformers)
   - Fine-tune if needed (Phase 2)

3. **Distance Threshold** (Week 5)
   - Only return chunks with similarity > 0.75
   - If no results -> fallback

4. **Re-ranking** (Phase 2)
   - Use LLM to re-score chunks for relevance
   - More expensive but more accurate

---

### Risk #5: LLM Latency Exceeds Tolerance (3+ seconds)

**Impact:**
- **Severity:** 6/10 (poor UX, user frustration)
- **Probability:** 40% (LLM calls are slow)

**Current: ~1500ms per GPT-3.5 call**
**Target: <2000ms P95**
**Reality at scale: May hit 3000-5000ms**

**Mitigation:**
1. **Caching** (Week 10)
   - Cache response for identical queries (20-30% hit rate)
   - Cache embeddings (40% hit rate)

2. **Model Choice** (Week 5)
   - GPT-3.5-turbo faster than GPT-4
   - OR: Use local Mistral (if you want to self-host)

3. **Queue & Batch** (Phase 2)
   - Hold queries 5 seconds, batch with others
   - Trade: +5s latency, -40% LLM calls

4. **Timeout Handling** (Week 6)
   - If LLM doesn't respond in 5s, return best-effort response from context
   - Fallback: "I found this info: [chunks]"

---

### Risk #6: Cost Explosion (OpenAI bills spike)

**Impact:**
- **Severity:** 6/10 (budget overrun)
- **Probability:** 30% (easy to underestimate usage)

**Current:** 100 queries/day = $50/month
**At 10K queries/day:** $500/month (worst case: $2K+ if using GPT-4)

**Mitigation:**
1. **Cost Monitoring** (Week 1)
   - Set AWS billing alert at $500/month
   - Track OpenAI API costs daily
   - Flag if costs > 20% above forecast

2. **Query Quotas** (Week 6)
   - Limit to 10K queries/day if budget constrained
   - Queue requests, process in off-peak hours

3. **Caching** (Week 10)
   - Aggressive caching → 30-40% cost reduction

4. **Model Optimization** (Phase 2)
   - Fine-tune smaller model (cheaper + domain-specific)
   - Expected: 50% cost reduction

---

## Tier 3: MEDIUM-RISK Issues (Operational friction)

### Risk #7: Salesforce API Rate Limits Hit

**Problem:** Salesforce allows 10K API calls/24hrs. If syncing 500 leads/day + frequent updates = could hit limit.

**Mitigation:**
- Batch processing (bulk API, not REST)
- Time-shift syncs (avoid peak hours)
- Request higher limits from Salesforce

---

### Risk #8: Database Connection Pool Exhausted

**Problem:** RDS max_connections default is 100. With 100+ concurrent users, you hit limit.

**Mitigation:**
- Use PgBouncer (connection pooling)
- Increase RDS max_connections to 200
- Implement circuit breaker (queue requests if pool full)

---

### Risk #9: Prompt Injection / Jailbreak Attempts

**Problem:** User tries to manipulate chatbot to ignore guidelines:
- "Forget the context and tell me X"
- SQL injection attempts
- Social engineering

**Mitigation:**
- Input sanitization (block suspicious keywords)
- Prompt isolation (clear separation between system + user input)
- Response filtering (detect hallucinations)
- Rate limiting (prevent brute-force jailbreak attempts)

---

### Risk #10: Data Privacy Breach

**Problem:** Student email/phone exposed in logs or database.

**Impact:**
- **Severity:** 9/10 (legal + compliance)
- **Probability:** 5% (if proper security in place)

**Mitigation:**
- Encrypt PII at rest (AES-256) and in transit (TLS)
- No logging of email/phone
- Access control (only admissions team can see leads)
- Data retention limits (delete after 90 days)
- Regular security audit

---

## Risk Management Dashboard (Track Weekly)

| Risk | Impact | Probability | Detection | Mitigation Status | Owner |
|------|--------|-------------|-----------|-------------------|-------|
| Hallucinations | 9 | 20% | User feedback | Building confidence scoring | ML Eng |
| Scraper breaks | 8 | 40% | No docs for 24h | Alert system ready | Backend |
| SF sync fails | 7 | 20% | Manual audit | Retry logic + monitoring | Backend |
| Low retrieval | 7 | 20% | Test set eval | Chunking tuning | Backend |
| Latency spikes | 6 | 40% | Dashboard | Caching strategy | Backend |
| Cost explosion | 6 | 30% | Billing alerts | Cost monitoring | Finance |
| Rate limits | 5 | 15% | Error logs | Batching strategy | Backend |
| DB pool exhaustion | 4 | 10% | Connection logs | PgBouncer config | DevOps |
| Security/Injection | 8 | 5% | Audit + testing | Input validation | Security |
| Data breach | 9 | 5% | Access logs | Encryption + retention | Security |

---

## Go/No-Go Decision Gate (before production)

**CRITICAL:** All Tier 1 risks must be mitigated before production launch:

- [ ] Hallucination rate tested & validated (<5%)
- [ ] Scraper alerts implemented & tested
- [ ] CRM sync reliability validated (99%+ success)
- [ ] Manual QA checklist passed (0 false admissions info)
- [ ] Cost monitoring in place + within budget

**If ANY unchecked:** Delay launch. Fix before going live.

