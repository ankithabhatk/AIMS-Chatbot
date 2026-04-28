import requests 
import json

BASE = 'http://localhost:8001/api/v1/chat' 
SESSION = 'killer-test-v2' 

# 50 Questions designed to expose decision overrides, stage blurring, and soft-looping
QUESTIONS = [
    # --- PHASE 1: Chaotic Discovery ---
    "hi",
    "I got 58% but want high salary and maybe coding but I hate maths and my parents want business and I’m confused and I don’t want long study",
    "what are my options with 58%?",
    "tell me about bba",
    "what about bca?",
    "which course is better for 58% marks?",
    "i like coding", # Should trigger BCA despite 58%
    "but my parents say bba is better",
    "is bca hard?",
    "what is the salary for bca?",
    
    # --- PHASE 2: Decision Lock Test ---
    "i think i'll go with bca", # DECISION LOCK TRIGGER
    "wait, actually tell me about bba again", # Exploration after lock
    "what is the fee for bba?",
    "okay bca sounds better, i'll stick with that", # RE-CONFIRM
    "what is the eligibility for bca?",
    "can i get in with 58%?", # CONSTRAINTS
    "how to apply?", # CONVERSION TRIGGER
    
    # --- PHASE 3: Hard Stage Enforcement Test ---
    "what is the process for admission?", # Should be STRICT conversion mode
    "what documents do i need?",
    "how to pay the fees?",
    "can i apply online?",
    "is there an entrance exam?",
    "where is the college?", # Tool intent during conversion
    "how to reach?",
    "can i visit the campus?",
    
    # --- PHASE 4: Loop & Tone Repetition Test ---
    "confused", 
    "i am still confused",
    "idk what to do",
    "suggest a course",
    "bca or bba?",
    "fees for bca",
    "fees for bca", # REPEAT
    "fees for bca", # REPEAT
    "ok",
    "sounds good",
    "tell me more",
    
    # --- PHASE 5: The "Killer" Scenarios ---
    "I like coding, got 75%", # Should NEVER override to BBA (Override Bug Test)
    "actually i have 75% marks", # Update marks
    "now suggest the best course", # Should be BCA
    "why not bba?",
    "salary for bca vs bba",
    "i'll go with bca",
    "how to join?",
    "what are the steps?",
    "documents?",
    "can i apply now?",
    "send the link",
    "is it open?",
    "thanks",
    "bye"
]

last_answer = None 
repeat_count = 0 
PASS = FAIL = 0 

print(f"🚀 Starting KILLER TEST V2 (50 Questions)")
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

        # Success Criteria for Killer Test:
        # 1. No triple repeats
        # 2. No high similarity loops (> 0.85)
        # 3. No empty answers
        # 4. Conversion mode must trigger for "apply/process" (Stage Enforcement)
        
        is_conversion_query = any(k in msg.lower() for k in ["apply", "process", "document", "step", "join", "link"])
        stage_fail = is_conversion_query and mode != "conversion" and mode != "bridge"
        
        bad = ( 
            repeat_count >= 2 or 
            len(answer.strip()) < 20 or
            sim > 0.85 or
            stage_fail
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
            if len(answer.strip()) < 20: print("    ⚠️ SHORT/EMPTY ANSWER")
            if sim > 0.85: print(f"    ⚠️ HIGH SIMILARITY ({sim:.2f})")
            if stage_fail: print(f"    ⚠️ STAGE ENFORCEMENT FAIL (Mode: {mode})")
        print() 
        
    except Exception as e:
        print(f"{i:2}. [ERROR] Q: {msg} -> {e}")
        FAIL += 1

print("-" * 60)
print(f"=== RESULT: {PASS}/{len(QUESTIONS)} PASS | {FAIL} FAIL ===") 
