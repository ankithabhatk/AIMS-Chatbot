import requests 
import json

BASE = 'http://localhost:8001/api/v1/chat' 
SESSION = 'destruction-50-final' 

# 50 Questions covering Standard, Loopy, Edge, and Progression scenarios
QUESTIONS = [
    # --- PHASE 1: Discovery ---
    "hi",
    "idk what to do",
    "confused about my career",
    "what courses do you have?",
    "tell me about bba",
    "what about bca?",
    "which is better bba or bca?",
    "what are the fees for bba?",
    "is there any scholarship?",
    "what is the average salary for bca?",
    
    # --- PHASE 2: Information & Marks ---
    "I got 75% in 12th",
    "can I get admission in bca with 75%?",
    "what are the eligibility criteria for mba?",
    "i have 60% marks, what can i do?",
    "is 60% enough for bcom?",
    "i like coding",
    "i also like business",
    "suggest a course for me",
    "but i am weak in math",
    "can i do bca if i am weak in math?",
    
    # --- PHASE 3: Deep Dive & Comparison ---
    "what is the difference between bba and bcom?",
    "placement record for mba",
    "highest package last year",
    "top recruiters",
    "does aims have hostel?",
    "where is the campus located?",
    "how to reach there?",
    "what are the timing of the college?",
    "is there a library?",
    "sports facilities?",
    
    # --- PHASE 4: Loop & Repetition Testing ---
    "confused", # Repeat of Q2/Q3
    "idk what to do", # Repeat of Q2
    "tell me about bba", # Repeat of Q5
    "what are the fees?", # Vague
    "fees for bba", # Specific
    "fees for bba", # Intentional repeat
    "fees for bba", # Intentional repeat
    "ok",
    "sounds good",
    "not sure yet",
    
    # --- PHASE 5: Progression & Conversion ---
    "I want high salary",
    "which course gives high package?",
    "mba salary details",
    "is mba better than bba for salary?",
    "how to apply?",
    "what is the admission process?",
    "documents required for admission",
    "last date to apply",
    "can i apply online?",
    "send me the application link"
]

last_answer = None 
repeat_count = 0 
PASS = FAIL = 0 

print(f"🚀 Starting FULL 50-QUESTION DESTRUCTION TEST")
print(f"Session: {SESSION}")
print("-" * 60)

for i, msg in enumerate(QUESTIONS, 1): 
    payload = {'query': msg, 'session_id': SESSION} 
    try:
        r = requests.post(BASE, json=payload, timeout=15) 
        data = r.json() 

        answer = data.get('answer', '') 
        mode   = data.get('mode', '?') 
        turn   = data.get('turn_count', '?')
        metrics = data.get('metrics', {})
        sim = metrics.get('similarity', 0)
        prog = metrics.get('progression', 0)

        # 🚨 LOOP DETECTION 
        if last_answer and answer[:80] == last_answer[:80]: 
            repeat_count += 1 
        else: 
            repeat_count = 0 

        last_answer = answer 

        bad = ( 
            repeat_count >= 2 or 
            len(answer.strip()) < 30 or
            sim > 0.9
        ) 

        verdict = "FAIL" if bad else "PASS" 

        if bad: 
            FAIL += 1 
        else: 
            PASS += 1 

        print(f"{i:2}. [{verdict}] mode={mode:12} turn={turn:2} | Sim={sim:.2f} | Prog={prog:.2f}") 
        print(f"    Q: {msg}") 
        clean_answer = answer[:120].replace('\n', ' ')
        print(f"    A: {clean_answer}...") 
        if bad:
            if repeat_count >= 2: print("    ⚠️ LOOP DETECTED (Repeated Answer)")
            if len(answer.strip()) < 30: print("    ⚠️ SHORT ANSWER")
            if sim > 0.9: print(f"    ⚠️ HIGH SIMILARITY ({sim:.2f})")
        print() 
        
    except Exception as e:
        print(f"{i:2}. [ERROR] Q: {msg} -> {e}")
        FAIL += 1

print("-" * 60)
print(f"=== RESULT: {PASS}/{len(QUESTIONS)} PASS | {FAIL} FAIL ===") 
