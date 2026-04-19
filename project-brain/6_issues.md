# Issues & Blockers

## 🔴 Critical Issues (Blocking MVP)

None currently. ✅

---

## 🟡 Medium Issues (MVP-relevant)

### Issue #1: Real Website Scraping Not Tested
- **Status**: Identified
- **Details**: 
  - Scraper code written but not tested on actual AIMS website
  - HTML structure might not match expectations
  - Website might have rate limiting / robots.txt
- **Impact**: Can't ingest real data for production
- **Solution**: 
  - [ ] Test scraper on AIMS website
  - [ ] Handle HTML variations
  - [ ] Add polite delays + User-Agent
  - [ ] Fallback: use sample data
- **Priority**: High (needed for production data)
- **Blocker**: Can continue with sample data for now

### Issue #2: FAISS Not Persistent on Server Restart
- **Status**: Identified
- **Details**:
  - Index saved to /tmp/ (temporary directory)
  - Filesystem may be ephemeral in some deployments
  - Data loss on container restart
- **Impact**: Lost embeddings + index after restart
- **Solution**:
  - [ ] Move FAISS index to mounted volume
  - [ ] Or: Load from PostgreSQL on startup
  - [ ] Or: Commit to git (for small datasets)
- **Priority**: Medium (important for production)
- **Workaround**: Re-ingest data on startup

### Issue #3: Template-Based Responses May Have Low Quality
- **Status**: Known limitation
- **Details**:
  - Current: "Based on information about '[topic]': [excerpt]"
  - Can be repetitive and unnatural
  - Better responses need LLM (OpenAI)
- **Impact**: User satisfaction may drop with broad questions
- **Solution**:
  - [ ] Improve templates
  - [ ] Add OpenAI integration (if budget)
  - [ ] Fine-tune embeddings on college data
  - [ ] Multi-hop retrieval (combine multiple chunks)
- **Priority**: Medium (affects user experience)
- **Workaround**: Works for MVP, acceptable for launch

### Issue #4: Sample Data Limited (5 documents)
- **Status**: Design decision, not a blocker
- **Details**:
  - Only 5 sample documents
  - Real AIMS website has 50+ pages
  - Doesn't represent production scale
- **Impact**: Limited coverage of topics
- **Solution**:
  - [ ] Expand sample data to 20-30 Q&A pairs
  - [ ] Or: Switch to real scraping
- **Priority**: Medium (needed for realistic testing)
- **Target**: 30+ documents before user testing

### Issue #5: No Database Persistence Yet
- **Status**: Identified
- **Details**:
  - PostgreSQL configured but not used
  - No schema migrations
  - Documents only in FAISS (ephemeral)
  - Can't query history
- **Impact**: Can't build analytics, can't persist data
- **Solution**:
  - [ ] Run migrations (Alembic)
  - [ ] Store documents in PostgreSQL
  - [ ] Load embeddings on startup from DB
  - [ ] Index chat events for analytics
- **Priority**: High (needed for phase 2)
- **Timeline**: Next session (1-2 hours)

---

## 🟢 Low Issues (Non-blocking)

### Issue #6: No Unit Tests
- **Status**: MVP acceptable
- **Details**:
  - Only integration test script (test_rag.py)
  - No pytest fixtures
  - No CI/CD testing
- **Solution**:
  - [ ] Add pytest suite
  - [ ] Test each service in isolation
  - [ ] Mock external calls
- **Priority**: Low (MVP doesn't require)
- **Timeline**: Post-launch

### Issue #7: No Error Recovery in Scraper
- **Status**: Nice-to-have
- **Details**:
  - If page scrape fails, whole job fails
  - No retry logic
  - No error logging per page
- **Solution**:
  - [ ] Try-catch per page
  - [ ] Log failed pages
  - [ ] Retry with exponential backoff
- **Priority**: Low (sample data works around this)
- **Timeline**: Phase 2

### Issue #8: FAISS Limited to Single Machine
- **Status**: Design choice
- **Details**:
  - FAISS doesn't scale to distributed systems
  - Works fine for <1M vectors
  - Not suitable for multi-instance deployment
- **Solution**:
  - [ ] Use Pinecone for distributed systems
  - [ ] Or: Load-balance with replicas
  - [ ] Or: Shard index by topic
- **Priority**: Low (MVP is single-instance)
- **Timeline**: Phase 3 (if scaling needed)

---

## 📋 Risk Assessment

### High-Risk Items
| Item | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Website scraper breaks on HTML change | Medium | High | Add backup sources, monitor |
| FAISS index becomes corrupted | Low | High | Regular backups, version control |
| Poor response quality frustrates users | Medium | Medium | Feedback loop, OpenAI upgrade |
| Hallucinations from LLM (if added) | Medium | High | Confidence threshold, validation |

### Medium-Risk Items
| Item | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| PostgreSQL not ready for production | Low | High | Test with load, proper schema |
| Salesforce API integration fails | Medium | Medium | Multiple sync retry logic |
| Performance degrades at scale | Low | High | Benchmark, optimize, cache |

### Low-Risk Items
| Item | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Frontend UI broken | Low | Low | User testing, design QA |
| Typos in sample data | High | Low | Automated spell check |
| Logging too verbose | Medium | Low | Adjust log levels |

---

## 🔍 Testing Status

### What's Tested ✅
- Embedding generation ✅
- FAISS retrieval ✅
- Response generation ✅
- Full pipeline end-to-end ✅
- Multiple query types ✅

### What's NOT Tested ❌
- Real website scraping (not tried)
- Database write/read (not connected)
- Salesforce API (not implemented)
- Lead capture endpoint (placeholder)
- Analytics queries (placeholder)
- Frontend integration (not built)
- Load testing (needs benchmarking)
- Error cases (minimal coverage)

---

## 🚨 Blockers for Next Phase

| Blocker | For Feature | Solution | ETA |
|---------|-------------|----------|-----|
| Database not setup | Analytics | Run migrations | TODAY |
| Salesforce auth | Lead capture | Get OAuth credentials | TBD |
| Real data | Production | Test scraper | THIS WEEK |
| Frontend design | User testing | Design mockups | THIS WEEK |

---

## 📌 Action Items (For Next Session)

Priority 1 (Do First):
- [ ] Test real website scraping
- [ ] Setup PostgreSQL + migrations
- [ ] Implement lead capture endpoint

Priority 2 (Do Next):
- [ ] Add database persistence for documents
- [ ] Build analytics dashboard
- [ ] Improve sample data to 30+ documents

Priority 3 (Polish):
- [ ] Add unit tests
- [ ] Improve error messages
- [ ] Add monitoring/logging
