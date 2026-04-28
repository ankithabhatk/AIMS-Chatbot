import requests 

BASE = 'http://localhost:8001/api/v1/chat' 
SESSION = 'destruction-debug-13' 

QUESTIONS = [ 
"idk what to do", 
"confused", 
"I got 60%", 
"I think finance", 
"but salary is low no?", 
"I want high salary", 
"I like coding, got 75%", 
"sounds good", 
"job after", 
"how to apply", 
"I got 42%" 
] 

last_answer = None 
repeat_count = 0 

PASS = FAIL = 0 

for i, msg in enumerate(QUESTIONS, 1): 
    payload = {'query': msg, 'session_id': SESSION} 
    try:
        r = requests.post(BASE, json=payload, timeout=12) 
        data = r.json() 

        answer = data.get('answer', '') 
        mode   = data.get('mode', '?') 
        turn   = data.get('turn_count', '?')
        # Some versions might use 'meta' -> 'mode'
        if not mode or mode == '?':
            mode = data.get('meta', {}).get('mode', '?')

        # 🚨 LOOP DETECTION 
        if last_answer and answer[:80] == last_answer[:80]: 
            repeat_count += 1 
        else: 
            repeat_count = 0 

        last_answer = answer 

        bad = ( 
            repeat_count >= 2 or 
            len(answer.strip()) < 30 
        ) 

        verdict = "FAIL" if bad else "PASS" 

        if bad: 
            FAIL += 1 
        else: 
            PASS += 1 

        print(f"{i}. [{verdict}] mode={mode} turn={turn}") 
        print(f"   Q: {msg}") 
        print(f"   → {answer[:150]}") 
        if repeat_count >= 2: 
            print("   ⚠️ LOOP DETECTED") 
        print() 
    except Exception as e:
        print(f"{i}. [ERROR] Q: {msg} -> {e}")
        FAIL += 1

print(f"=== RESULT: {PASS}/{len(QUESTIONS)} PASS | {FAIL} FAIL ===") 
