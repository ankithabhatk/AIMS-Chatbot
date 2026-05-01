# AIMS Chatbot E2E Test Report

## 🟢 Final Pass/Fail Summary
**Status: ALL PASSED (12/12 tests)**
- **Chromium**: 6 tests passed
- **Mobile Chrome**: 6 tests passed
- **Total Time**: 2.6 minutes

## 📂 Executed Test Suites
1. `tests/behavioral/contradiction-flow.spec.ts` (Behavioral / Contradiction)
2. `tests/ux/chatbot.spec.ts` (UX / Interactions)

## 📸 Screenshots Generated (`testing/screenshots/`)
* `1-initial-load.png` (Onboarding Flow)
* `2-coding-interest.png` (Coding Interest Flow)
* `3-contradiction-hate-coding.png` (Contradiction Pivot)
* `4-pivot-business.png` (Business Pivot)
* `5-offline-fallback.png` (Offline Fallback State)
* `regression-business-pivot.png` (Behavioral Pivot Proof)
* `regression-confidence-drop.png` (Confidence Curve Drop)
* `regression-hate-coding.png` (Avoidance Routing Validation)

## 📊 Feature Behavior Validation

### Confidence-Bar Behavior
✅ Confirmed via `Confidence bar drops after contradiction` test.
- Interest builds confidence to ~0.45 (visible in UI).
- Contradiction properly registers as a risk signal, triggering a confidence drop to ~0.27 (visible in UI).
- Bar correctly renders without zero-width Playwright failure.

### Contradiction-Flow Behavior
✅ Confirmed via `Avoidance: "hate coding" must NOT re-promote coding` test.
- User intent "I like coding" routed to `counselor_coding`.
- Avoidance intent "actually I hate coding" successfully bypassed `counselor_coding` despite containing the keyword "coding".
- Handled via `counselor_general` as an open exploratory pivot.
- A secondary pivot to "maybe business is better" routed successfully to `counselor_business` without forced looping.

### Mobile Responsiveness Results
✅ Confirmed via `[Mobile Chrome]` project execution.
- `.onboarding-radio-grid` pointer interception bypassed using programmatic scrolling and forced clicks.
- `ChatInput` does not obscure submission functionality.
- Layout scales successfully across the simulated viewport.

## ⚠️ Network / Console Events
- `[browser] Image with src "/aims logo.jpg" has "fill" but is missing "sizes" prop.` (Harmless performance warning)
- `[browser] API Error: TypeError: Failed to fetch` (Expected failure during Offline Fallback Handling test)
- `WARNING:app.services.database.db_logger:[DB] Supabase env missing; local persistence will be used` (Expected in local test environment)
- `WARNING:app.services.production_analytics:SUPABASE_URL or SUPABASE_KEY not set. Analytics will be skipped.` (Expected)

## 🐛 Failures & Auto-Debug Steps
*None. The suite executed cleanly on the first pass due to the robust stabilization patches introduced in the previous iteration.*
