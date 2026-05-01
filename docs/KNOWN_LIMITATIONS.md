# Known Limitations

This document outlines the known boundaries, heuristics, and architectural constraints of the AIMS Chatbot. It serves as an operational safeguard to set expectations for deployment, debugging, and future contributor onboarding.

## 1. Knowledge Base & Retrieval Constraints
- **Data Dependency:** The semantic retrieval engine (FAISS) is strictly bounded by the `course_guidance.json` and `.json` artifacts generated during the scraping phase. The bot does not "know" about real-time events or unindexed programs.
- **Ingestion Requirement:** Adding new academic programs or updating fees requires a manual execution of the "Knowledge Governance Workflow" (Audit -> Update JSON -> Rebuild Embeddings -> Regression Test).
- **Structured Precision Bypass:** Inquiries about basic enumeration (e.g., "What courses are offered?", "What is the fee for MBA?") bypass the LLM reasoning layer and are served via `structured_knowledge.py`. This ensures 100% accuracy but limits conversational variance for these specific intents.

## 2. Behavioral & Conversational Limits
- **Verbosity:** The LLM synthesis layer (especially when relying on fallback models) may occasionally produce verbose responses. While prompts constrain output to short paragraphs, the raw generation cannot be perfectly bounded.
- **Confidence Scoring:** The `profile_confidence_score` displayed in the UI is a **heuristic state tracker**, not a measure of psychological certainty. It is calculated deterministically based on form inputs, message count, intent density, and contradiction triggers.
- **Contradiction Reset:** When a user explicitly contradicts themselves (e.g., "Actually I hate coding"), the system applies a heavy penalty (-35%) to confidence and resets the routing logic to an exploratory state. It does not perfectly "unlearn" prior context but relies on the penalty to shift behavior.

## 3. Infrastructure & Provider Fallbacks
- **Primary vs. Fallback Discrepancies:** The primary LLM provider (Groq/Llama-3) produces highly concise and emotionally intelligent routing. If the primary provider fails, the system falls back to the local `TinyLlama` model. Responses from TinyLlama may vary significantly in tone, coherence, and adherence to strict bullet-point constraints.
- **Cold Starts:** On initial boot in serverless environments (like Railway), the first query may take an additional 3-5 seconds as the FAISS index and local embedding models (SentenceTransformers) are loaded into memory.
- **Mobile Viewport Interactions:** The UI handles mobile scaling, but deeply nested structured components (like fee comparison tables) may require horizontal scrolling on narrow devices.

## 4. Analytics
- **Local Fallback:** If the `SUPABASE_URL` or `SUPABASE_KEY` are not properly configured or if the database is unreachable, conversational analytics will silently fall back to `local_chat_logs.json` to prevent application crashes. Real-time dashboards will not reflect this local data.

---
*Maintained by the Antigravity Engineering Loop.*
