# UI → API TRACE MODE

## Objective
Find exactly where the message flow breaks between UI and backend.

## Console Logs Added

All trace logs have been added to the codebase with emoji prefixes for easy identification:

### STEP 1: Robot Click
**File:** `src/components/Chat/FloatingRobot.tsx`
**Log:** `🤖 [STEP 1] Robot clicked`
**Expected:** Should appear when you click the floating robot button

### STEP 2: Chat Opens
**File:** `src/context/ChatContext.tsx`
**Log:** `💬 [STEP 2] Chat open state: true`
**Expected:** Should appear immediately after robot click

### STEP 3: Input Captured
**File:** `src/components/Chat/ChatInput.tsx`
**Log:** `⌨️  [STEP 3] User typed: <your message>`
**Expected:** Should appear when you click Send button

### STEP 4: sendMessage Triggered
**File:** `src/context/ChatContext.tsx`
**Log:** `📤 [STEP 4] sendMessage triggered: { query, isFromForm, onboardingName }`
**Expected:** Should appear immediately after Step 3

### STEP 5: API Call Sent
**File:** `src/services/api.ts`
**Log:** `🌐 [STEP 5] API CALL → { url, payload }`
**Expected:** Should show the API URL and full request payload

### STEP 6: API Response Received
**File:** `src/services/api.ts`
**Log:** `📥 [STEP 6] API RESPONSE ← <response data>`
**Expected:** Should show the backend response

### STEP 7: UI Receives Response
**File:** `src/context/ChatContext.tsx`
**Log:** `✅ [STEP 7] Bot response received: <data>`
**Expected:** Should show the processed bot response

### STEP 8: Message Rendered
**File:** `src/components/Chat/MessageBubble.tsx`
**Log:** `🎨 [STEP 8] Rendering message: { id, isUser, content }`
**Expected:** Should appear for each message bubble rendered

## How to Run the Trace

1. **Start the frontend:**
   ```bash
   npm run dev
   ```

2. **Open browser console:**
   - Chrome/Edge: F12 or Cmd+Option+I (Mac)
   - Look for the Console tab

3. **Test the flow:**
   - Click the floating robot button
   - Type a message: "I like coding"
   - Click Send
   - Watch the console logs

4. **Record results:**
   - Note which step is the LAST one that appears
   - Copy all console logs
   - Note any errors in red

## Expected Flow (All Pass)

```
🤖 [STEP 1] Robot clicked
💬 [STEP 2] Chat open state: true
⌨️  [STEP 3] User typed: I like coding
📤 [STEP 4] sendMessage triggered: { query: "I like coding", isFromForm: false }
🌐 [STEP 5] API CALL → { url: "http://localhost:8000/api/v1/chat", payload: {...} }
📥 [STEP 6] API RESPONSE ← { answer: "...", ... }
✅ [STEP 7] Bot response received: { answer: "...", ... }
🎨 [STEP 8] Rendering message: { id: "...", isUser: true, content: "I like coding" }
🎨 [STEP 8] Rendering message: { id: "...", isUser: false, content: "..." }
```

## Failure Patterns

### Pattern 1: Robot doesn't open chat
- **Symptom:** Only Step 1 appears, no Step 2
- **Cause:** `setIsChatOpen` not working
- **Location:** ChatContext state management

### Pattern 2: Input not captured
- **Symptom:** Steps 1-2 appear, but no Step 3
- **Cause:** Send button not triggering `handleSend`
- **Location:** ChatInput component

### Pattern 3: sendMessage not firing
- **Symptom:** Steps 1-3 appear, but no Step 4
- **Cause:** `sendMessage` function not being called
- **Location:** ChatContext provider

### Pattern 4: API not called
- **Symptom:** Steps 1-4 appear, but no Step 5
- **Cause:** `fetchChatResponse` not being invoked
- **Location:** ChatContext → api.ts connection

### Pattern 5: Backend not responding
- **Symptom:** Step 5 appears, but no Step 6
- **Cause:** Backend error or not running
- **Location:** Backend API endpoint

### Pattern 6: Response not processed
- **Symptom:** Step 6 appears, but no Step 7
- **Cause:** Response parsing error
- **Location:** ChatContext response handling

### Pattern 7: UI not rendering
- **Symptom:** Step 7 appears, but no Step 8
- **Cause:** Message not added to state or render issue
- **Location:** MessageBubble component

## Next Steps

After running the trace, report back with:

```
STEP 1 → PASS / FAIL
STEP 2 → PASS / FAIL
STEP 3 → PASS / FAIL
STEP 4 → PASS / FAIL
STEP 5 → PASS / FAIL
STEP 6 → PASS / FAIL
STEP 7 → PASS / FAIL
STEP 8 → PASS / FAIL
```

Include:
- Console logs (copy/paste)
- Any errors (red text in console)
- Screenshots if helpful

## CRITICAL RULES

❌ Do NOT modify code yet
❌ Do NOT guess the bug
❌ Do NOT skip steps

✅ Only locate the break
✅ Report exact step that fails
✅ Copy console output
