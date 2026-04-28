#!/usr/bin/env python3
"""Fix remaining issues in chat_phase4.py - handles CRLF line endings"""

with open('backend/app/api/chat_phase4.py', 'r', newline='') as f:
    content = f.read()

print(f"Original length: {len(content)} chars")

# ---- FIX 1: Add session recovery call ----
old1 = '        # Base session context\r\n        session = get_or_create_session(session_id)\r\n        \r\n        # Treat valid UI profile'

new1 = '        # Base session context\r\n        session = get_or_create_session(session_id)\r\n        \r\n        # Session recovery from DB if email provided\r\n        if request.user and request.user.email:\r\n            try:\r\n                session = recover_session_from_db(session_id, request.user.email)\r\n                logger.info(f"[{session_id}] Session recovery attempted for {request.user.email}")\r\n            except Exception as e:\r\n                logger.warning(f"[{session_id}] Session recovery failed: {e}")\r\n        \r\n        # Treat valid UI profile'

if old1 in content:
    content = content.replace(old1, new1)
    print("✅ Fix 1: Session recovery call added")
else:
    print("❌ Fix 1: Pattern not found")
    # Try simpler
    if 'session = get_or_create_session(session_id)' in content:
        print("   Found session creation line")

# ---- FIX 2: Add hard fallback for empty answers ----
old2 = '        # Safety net: if synthesis returns empty but we have chunks, use top chunk text\r\n'

new2 = '        # HARD FALLBACK: Catch empty/short answers (Checklist item 6)\r\n        if not answer or not answer.strip() or len(answer.strip()) < 5:\r\n            logger.warning(f"[{session_id}] HARD FALLBACK: answer too short or empty")\r\n            answer = "Try asking about courses, fees, or admission process."\r\n            is_fallback = True\r\n            confidence = 0.3\r\n            suggestions = ["MBA fees", "BCA admission", "Placement record"]\r\n        \r\n        # Safety net: if synthesis returns empty but we have chunks, use top chunk text\r\n'

if old2 in content:
    content = content.replace(old2, new2)
    print("✅ Fix 2: Hard fallback for empty answers added")
else:
    print("❌ Fix 2: Pattern not found")

# ---- FIX 3: Add minimum keyword match ----
old3 = '        query = request.query.strip()\r\n        query_lower = query.lower()\r\n        \r\n        # ===='

new3 = '        query = request.query.strip()\r\n        query_lower = query.lower()\r\n        \r\n        # MINIMUM KEYWORD MATCH (Checklist item 12)\r\n        words = query.split()\r\n        if len(words) >= 2:\r\n            keywords = ["mba", "mca", "bca", "bba", "bcom", "mcom", "bhm", \r\n                       "fee", "cost", "price", "admission", "placement", "hostel",\r\n                       "course", "program", "apply", "eligibility"]\r\n            matches = sum(1 for w in words if w.lower() in keywords)\r\n            min_required = 1 if len(words) <= 3 else 2\r\n            if matches < min_required:\r\n                logger.warning(f"[{session_id}] Keyword match failed: {matches} matches for \'{query}\'")\r\n                return {\r\n                    "answer": "Try asking about courses, fees, or admission process.",\r\n                    "status": "unlock",\r\n                    "fallback": True,\r\n                    "confidence": 0.2,\r\n                    "suggestions": ["MBA fees", "MCA admission", "Placement record"],\r\n                    "meta": {"session_id": session_id}\r\n                }\r\n        \r\n        # ===='

if old3 in content:
    content = content.replace(old3, new3)
    print("✅ Fix 3: Minimum keyword match added")
else:
    print("❌ Fix 3: Pattern not found")
    if 'query = request.query.strip()' in content:
        idx = content.index('query = request.query.strip()')
        print(f"   Context around: {repr(content[idx:idx+150])}")

# Write back
with open('backend/app/api/chat_phase4.py', 'w', newline='') as f:
    f.write(content)

print(f"\nFinal length: {len(content)} chars")
print("✅ File written back")
