# Phase 5: Frontend React Components Implementation Plan

## Current Status ✅
**Backend:** Production ready with structured response composition  
**Frontend:** Running and accessible (localhost:3000)  
**API:** Returning clean structured JSON with sections, CTAs, and metadata  

## What's Working
- ✅ Intent detection (fees/admission/placements/campus/courses/general)
- ✅ FAISS retrieval (64 documents, semantic search)
- ✅ Document filtering (score > 0.60, dedup, max 3 docs)
- ✅ Response composition (structured sections + CTAs)
- ✅ Lead capture gating (high-confidence queries redirect to form)
- ✅ Health check endpoint (all systems loaded)
- ✅ CORS configuration (frontend can reach backend)

## What's Pending: React Components

### Task 1: Create SectionBlock Component
**File:** `/frontend/src/components/SectionBlock.tsx`

```typescript
interface Section {
  type: 'list' | 'text' | 'table';
  title: string;
  items?: string[];
  content?: string;
}

export const SectionBlock: React.FC<{ section: Section }> = ({ section }) => {
  // Render section with:
  // - Title with emoji (extracted from title)
  // - Bullet points for list type
  // - Paragraph for text type
  // - Clean styling with hover effects
}
```

**Expected Rendering:**
```
📝 Admission Process
• A: No, hostel is not compulsory
• Facilities for boys and girls
• Most local students commute from home
• Q: Is an entrance exam required for MBA admission
```

### Task 2: Create CTAButton Component
**File:** `/frontend/src/components/CTAButton.tsx`

```typescript
interface CTA {
  label: string;
  action: string;
}

export const CTAButton: React.FC<{ cta: CTA; onClick: (action: string) => void }> = ({ cta, onClick }) => {
  // Render styled button that:
  // - Triggers onClick(action) on click
  // - Shows loading state while processing
  // - Handles "apply", "eligibility", "courses", "contact" actions
}
```

**Expected Rendering:**
```
[Check Eligibility] [Apply Now]
```

### Task 3: Create StructuredResponse Component
**File:** `/frontend/src/components/StructuredResponse.tsx`

```typescript
interface StructuredResponse {
  answer: string;
  sections?: Section[];
  ctas?: CTA[];
  confidence: number;
  compose_mode?: string;
}

export const StructuredResponse: React.FC<{ response: StructuredResponse }> = ({ response }) => {
  // Orchestrate rendering of:
  // 1. Answer text (summary)
  // 2. Sections array (map to SectionBlock components)
  // 3. CTAs array (map to CTAButton components)
  // 4. Optional: Confidence indicator
}
```

### Task 4: Update ChatContext
**File:** `/frontend/src/context/ChatContext.tsx`

**Changes needed:**
```typescript
// Update Message type to support structured responses
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  // NEW FIELDS:
  sections?: Section[];
  ctas?: CTA[];
  compose_mode?: string;
}

// Update response parsing in sendMessage:
const parseResponse = (response: any) => {
  return {
    content: response.answer,
    sections: response.sections,
    ctas: response.ctas,
    compose_mode: response.meta?.compose_mode
  };
}
```

### Task 5: Update ChatContainer
**File:** `/frontend/src/components/ChatContainer.tsx`

**Changes needed:**
```typescript
// Replace plain text rendering:
{message.role === 'assistant' ? (
  message.compose_mode ? (
    <StructuredResponse response={message} />
  ) : (
    <p>{message.content}</p>
  )
) : (
  <p>{message.content}</p>
)}
```

## Implementation Order
1. **SectionBlock** (simplest, no dependencies)
2. **CTAButton** (simple, needs onClick handler)
3. **StructuredResponse** (orchestrates 1 & 2)
4. **ChatContext** (enables API integration)
5. **ChatContainer** (uses StructuredResponse)

## Testing Strategy

### Unit Tests
```typescript
// Test SectionBlock renders with correct title/items
// Test CTAButton calls onClick with correct action
// Test StructuredResponse maps sections/ctas correctly
```

### Integration Tests
```typescript
// Test full response flow: API → ChatContext → StructuredResponse
// Test CTA button clicks trigger correct actions
// Test message history includes structured data
```

### E2E Tests
```typescript
// Screenshot "mba fees" → shows structured sections
// Screenshot "admission process" → shows CTAs
// Test CTA click → leads to form or correct action
```

## Expected Outcomes

### Before (Current)
```
User: "admission process"
Bot: [Raw text dump with mixed Q&A]
```

### After (Post-implementation)
```
User: "admission process"
Bot: 
  📝 Admission Process
  • A: No, hostel is not compulsory
  • Facilities for boys and girls
  • Most local students commute from home
  
  [Check Eligibility] [Apply Now]
```

## Time Estimates
- SectionBlock: 30 min
- CTAButton: 20 min
- StructuredResponse: 30 min
- ChatContext updates: 20 min
- ChatContainer updates: 15 min
- Testing & refinement: 30 min

**Total: ~2.5 hours**

## Success Criteria
- ✅ Structured responses render with proper formatting
- ✅ Sections display with titles, emojis, bullet points
- ✅ CTAs render as clickable buttons
- ✅ CTA clicks trigger appropriate actions
- ✅ Confidence indicator visible (optional)
- ✅ Browser console has no errors
- ✅ Playwright screenshots show clean structured UI

## Notes
- Backend API is **fully operational** - no changes needed
- Response format is **stable** - sections/ctas consistent
- No external UI library required - pure Tailwind/CSS
- Lead form integration happens after components working
- Typing indicators can be added as polish
