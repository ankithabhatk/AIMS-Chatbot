# Full AI Admission Counselor Architecture

## High-Level Pipeline

```
                ┌────────────────────────────┐
                │        FRONTEND            │
                │  (Web / Mobile / Widget)   │
                └────────────┬───────────────┘
                             │
                             ▼
                ┌────────────────────────────┐
                │        API LAYER           │
                │  FastAPI + Rate Limiter    │
                │  Auth + Input Validation   │
                └────────────┬───────────────┘
                             │
                             ▼
        ┌──────────────────────────────────────────┐
        │         ORCHESTRATION ENGINE             │
        │  (STATELESS — YOUR CORE BRAIN)           │
        └──────────────────────────────────────────┘
                             │
     ┌───────────────────────┼────────────────────────┐
     │                       │                        │
     ▼                       ▼                        ▼
┌───────────────┐   ┌────────────────────┐   ┌────────────────────┐
│   ROUTER      │   │  ENTITY EXTRACTOR  │   │   MEMORY FETCH     │
│ (deterministic│   │ (courses, marks)   │   │   (Redis)          │
│ scoring)      │   └────────────────────┘   └────────────────────┘
└──────┬────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│        COUNSELOR MODULE LAYER            │
│ (PURE LOGIC — NO LLM INVOLVED)           │
├──────────────────────────────────────────┤
│ • Guidance Engine                        │
│ • Comparator Engine                      │
│ • Constraint Advisor                     │
│ • Career Engine                          │
│ • Life Assistant                         │
│ • Unavailable Handler                    │
└───────────────┬──────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────┐
│     MULTI-INTENT COMPOSER                │
│ (merge outputs in correct order)         │
└───────────────┬──────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────┐
│     CONVERSION STATE MACHINE             │
│ decision → visualize → permission → CTA  │
└───────────────┬──────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────┐
│        AUTO-TUNING ENGINE                │
│ (analytics-driven behavior shifts)       │
│ • CTA style                             │
│ • response length                       │
│ • guidance confidence                   │
└───────────────┬──────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────┐
│      AI REINFORCEMENT LAYER              │
│ (LLM — Gemini / Ollama)                  │
│ • tone rewrite                          │
│ • clarity optimization                  │
│ • persuasion tuning                     │
│ ⚠️ NEVER changes logic                   │
└───────────────┬──────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────┐
│        SAFETY + SANITIZATION             │
│ • remove risky claims                   │
│ • enforce constraints                   │
└───────────────┬──────────────────────────┘
                │
                ▼
                📤 RESPONSE TO USER
```

## Side Systems

### Memory (State)
- **Store:** Redis
- **Keys:** session_id -> marks, interests, stage, conversion_stage, turn_count
- **TTL:** 30 minutes (prevents memory leaks)

### Analytics Pipeline
- **Flow:** Orchestrator -> Event Logger -> Queue (Async) -> Storage -> Optimizer
- **Events Tracked:** `user_message`, `intent_detected`, `decision_hit`, `confusion_loop`, `drop_off`, `permission_granted`, `conversion_complete`

### Optimizer Loop
- **Flow:** Analytics Data -> Pattern Detection -> `SYSTEM_TUNING UPDATE` -> Live Behavior Change

### LLM Fallback System
- Gemini (Primary) -> Ollama (Backup) -> Rule-based fallback

## Request Flow (Execution)
1. User sends query
2. API validates + rate limits
3. Fetch session from Redis
4. Extract entities
5. Router detects intents
6. Run counselor engines
7. Compose response
8. Run conversion state machine
9. Apply auto-tuning rules
10. (If needed) -> LLM reinforcement
11. Sanitize output
12. Save memory
13. Log analytics (async)
14. Return response

## Hard System Boundaries
- **LLM NEVER:** decides course, checks eligibility, chooses intent, overrides rules
- **LLM ONLY:** rewrites tone, improves clarity, adjusts persuasion

## Scaling Architecture
```
           Load Balancer
                │
     ┌──────────┼──────────┐
     ▼          ▼          ▼
 FastAPI    FastAPI    FastAPI   (horizontal scale)
     │
     ▼
   Redis (shared state)
     │
     ▼
   Workers (LLM / analytics)
```

## Performance Targets
- **Response Time:** < 1.5s
- **Memory Fetch:** < 50ms
- **LLM Usage:** < 30% requests
- **Drop-off Rate:** < 40%
- **Conversion Intent:** > 20%
