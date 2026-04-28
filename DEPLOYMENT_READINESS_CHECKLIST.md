# Deployment Readiness Checklist

**Before deploying to real users, verify everything is working.**

---

## System Checks

### Backend

- [ ] Backend server running without errors
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Database connected and accessible
- [ ] API endpoints responding (test with curl)
- [ ] Error handling working (test with invalid input)
- [ ] Logging enabled and writing to file

**Test command:**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "fees for bca", "user": {"course": "BCA"}}'
```

**Expected:** Valid JSON response with fees information

### Frontend

- [ ] Frontend running without errors
- [ ] Chat interface loads
- [ ] Can type and send messages
- [ ] Receives responses from backend
- [ ] No console errors
- [ ] Mobile responsive (if needed)

**Test steps:**
1. Open http://localhost:3000
2. Click robot icon
3. Select BCA
4. Type "fees"
5. Verify response appears

### Database

- [ ] Database running
- [ ] Tables created
- [ ] Can read/write data
- [ ] Backups configured (if production)

**Test command:**
```bash
# Check database connection
python -c "from app.db import get_db; print(get_db())"
```

---

## Logging Checks

### Query Logging

- [ ] Queries are being logged
- [ ] Log file exists: `logs/query_events.jsonl`
- [ ] Each log entry is valid JSON
- [ ] Logs include: query, intent, mode, fallback, timestamp

**Test:**
```bash
# Send a test query
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "user": {"course": "BCA"}}'

# Check logs
tail -f logs/query_events.jsonl
```

**Expected:** New log entry appears with all fields

### Error Logging

- [ ] Errors are being logged
- [ ] Error log file exists: `logs/errors.log`
- [ ] Error messages are descriptive

**Test:**
```bash
# Send invalid query to trigger error
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "", "user": {}}'

# Check error logs
tail -f logs/errors.log
```

---

## Functionality Checks

### Input Validation

- [ ] Empty queries rejected
- [ ] Garbage input rejected
- [ ] Valid queries processed

**Test queries:**
```
"" → Should reject
"!!!" → Should reject
"fees for bca" → Should process
```

### Spell Correction

- [ ] Typos corrected
- [ ] Protected words preserved
- [ ] Sentence structure maintained

**Test queries:**
```
"feees for bca" → Should correct to "fees for bca"
"bca fees" → Should preserve "bca"
"admisson process" → Should correct to "admission process"
```

### Intent Detection

- [ ] Single intent detected correctly
- [ ] Multiple intents detected
- [ ] Intent order preserved

**Test queries:**
```
"fees for bca" → Should detect: fees
"what is aims and fees" → Should detect: about_aims, fees (in order)
"why choose aims" → Should detect: why_aims
```

### Structured Responses

- [ ] Fees response correct
- [ ] Admission response correct
- [ ] About AIMS response correct
- [ ] Why AIMS response correct
- [ ] Facilities response correct

**Test queries:**
```
"fees for bca" → Should return BCA fees
"admission process" → Should return admission steps
"what is aims" → Should return about AIMS
"why choose aims" → Should return why AIMS
"facilities" → Should return campus facilities
```

### Fallback Handling

- [ ] Unknown queries handled gracefully
- [ ] Fallback message helpful
- [ ] No errors on fallback

**Test queries:**
```
"what's the weather" → Should fallback gracefully
"random gibberish" → Should fallback gracefully
"xyz abc def" → Should fallback gracefully
```

---

## Performance Checks

### Response Time

- [ ] Response time < 1 second (target)
- [ ] No timeout errors
- [ ] Consistent performance

**Test:**
```bash
# Time a query
time curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "fees for bca", "user": {"course": "BCA"}}'
```

**Expected:** < 1000ms total time

### Load Testing

- [ ] Can handle 10 concurrent requests
- [ ] No crashes under load
- [ ] Graceful degradation if needed

**Test:**
```bash
# Send 10 concurrent requests
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/chat \
    -H "Content-Type: application/json" \
    -d '{"query": "fees", "user": {"course": "BCA"}}' &
done
wait
```

---

## Security Checks

### Input Sanitization

- [ ] SQL injection attempts blocked
- [ ] XSS attempts blocked
- [ ] No sensitive data in logs

**Test:**
```
"'; DROP TABLE users; --" → Should be treated as normal query
"<script>alert('xss')</script>" → Should be treated as normal query
```

### Error Messages

- [ ] No stack traces in user responses
- [ ] No database details exposed
- [ ] No file paths exposed

**Test:** Send invalid requests and check responses

---

## User Experience Checks

### Chat Interface

- [ ] Chat opens smoothly
- [ ] Messages display correctly
- [ ] Responses are readable
- [ ] No formatting issues

### Onboarding

- [ ] Course selection works
- [ ] Form submission works
- [ ] State persists after refresh

**Test steps:**
1. Open chat
2. Select course
3. Submit form
4. Refresh page
5. Verify course still selected

### Multi-Intent Responses

- [ ] Multiple answers formatted clearly
- [ ] Answers in query order
- [ ] No duplicate answers

**Test query:**
```
"what is aims and fees for bca"
```

**Expected:**
```
About AIMS: [answer]
Fees: [answer]
```

---

## Documentation Checks

- [ ] README updated
- [ ] API documentation current
- [ ] Deployment instructions clear
- [ ] Troubleshooting guide available

---

## Final Verification

### Manual Test Sequence

1. **Start fresh**
   - [ ] Clear logs
   - [ ] Restart backend
   - [ ] Restart frontend

2. **Test happy path**
   - [ ] Open chat
   - [ ] Select course
   - [ ] Ask "fees"
   - [ ] Verify correct response

3. **Test edge cases**
   - [ ] Empty query
   - [ ] Typo query
   - [ ] Multi-intent query
   - [ ] Unknown query

4. **Test logging**
   - [ ] Check logs exist
   - [ ] Verify log format
   - [ ] Check for errors

5. **Test performance**
   - [ ] Response time acceptable
   - [ ] No timeouts
   - [ ] Consistent behavior

### Sign-Off

- [ ] All checks passed
- [ ] No critical issues
- [ ] Ready for deployment
- [ ] Backup created (if production)

---

## Deployment Steps

1. **Backup current system** (if production)
   ```bash
   cp -r backend backend.backup
   cp -r src src.backup
   ```

2. **Deploy backend**
   ```bash
   git pull origin main
   pip install -r requirements.txt
   python -m backend.app.main
   ```

3. **Deploy frontend**
   ```bash
   git pull origin main
   npm install
   npm run build
   npm start
   ```

4. **Verify deployment**
   - [ ] Backend responding
   - [ ] Frontend loading
   - [ ] Logging working
   - [ ] No errors

5. **Notify users**
   - [ ] Send deployment notification
   - [ ] Provide feedback channel
   - [ ] Monitor for issues

---

## Rollback Plan

If something breaks:

1. **Stop services**
   ```bash
   # Stop backend
   pkill -f "python.*main"
   
   # Stop frontend
   pkill -f "npm start"
   ```

2. **Restore backup**
   ```bash
   rm -rf backend src
   cp -r backend.backup backend
   cp -r src.backup src
   ```

3. **Restart services**
   ```bash
   python -m backend.app.main &
   npm start &
   ```

4. **Verify**
   - [ ] Backend responding
   - [ ] Frontend loading
   - [ ] System stable

---

## Post-Deployment Monitoring

### First Hour

- [ ] Monitor error logs
- [ ] Check response times
- [ ] Verify logging working
- [ ] No user complaints

### First Day

- [ ] Review all logs
- [ ] Check for patterns
- [ ] Verify data integrity
- [ ] Monitor performance

### First Week

- [ ] Collect 100 queries
- [ ] Analyze patterns
- [ ] Identify issues
- [ ] Plan fixes

---

## Checklist Summary

**Before Deployment:**
- [ ] All system checks passed
- [ ] All functionality checks passed
- [ ] All performance checks passed
- [ ] All security checks passed
- [ ] All UX checks passed
- [ ] Documentation complete
- [ ] Manual test sequence passed
- [ ] Backup created

**After Deployment:**
- [ ] Monitor first hour
- [ ] Monitor first day
- [ ] Collect data for first week
- [ ] Analyze and plan fixes

---

## Contact & Support

**If something breaks:**
1. Check error logs
2. Review recent changes
3. Rollback if needed
4. Document issue
5. Plan fix

**Questions?**
- Check README
- Check API docs
- Check troubleshooting guide
- Ask for help

---

**Status:** Ready for deployment ✅

