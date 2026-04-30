# Requirements Document

## Introduction

This feature completes the Decision Synthesis Layer for the AIMS chatbot system by resolving three critical UX issues that prevent production readiness. The Decision Synthesis Layer provides multi-turn conversational memory and personalized career guidance, combining user signals (interests, constraints, goals) across multiple conversation turns to deliver final recommendations with human-level reasoning.

**Current State**: The Decision Synthesis Layer has been partially implemented with multi-turn memory, conflict resolution, and personalization working. However, three UX issues remain:

1. **Counselor lock not fully deterministic**: Turn 3 sometimes routes to placements instead of staying in counselor mode
2. **Generic "counselor_general" responses are weak**: Mid-conversation turns show filler responses like "I'm here to help you find the right path"
3. **Decision output needs human judgement tone**: Recommendations lack micro-judgement phrases like "If I were in your position, I'd..."

**Success Criteria**: Production-ready Decision Synthesis Layer with deterministic routing, no generic mid-conversation responses, human-feeling recommendations, and 10/10 GOOD rating on harsh audit.

## Glossary

- **Decision_Synthesis_Layer**: The system component that combines user signals (interests, constraints, goals) from multiple conversation turns to generate personalized career recommendations
- **Counselor_Mode**: Conversational guidance mode for exploratory queries where the system acts as a career counselor rather than an information retrieval system
- **Counselor_Lock**: Mechanism that keeps users in counselor mode once they have an active profile (interests/constraints/goals) to prevent routing to other handlers mid-conversation
- **User_Profile**: Session-based data structure tracking interests, constraints, goals, education level, and ambiguity signals across conversation turns
- **Multi_Intent_Handler**: System component that handles queries with multiple structured intents (e.g., "fees and hostel")
- **Structured_Knowledge_Handler**: System component that provides deterministic responses for factual queries (fees, courses, admission)
- **Generic_Response**: Weak filler response that doesn't build on accumulated user profile (e.g., "I'm here to help you find the right path")
- **Human_Judgement_Tone**: Conversational style using phrases like "If I were in your position" or "In my experience" to make recommendations feel more human
- **Session_ID**: Unique identifier for a conversation session used to track user profile across turns
- **Active_Counselor_Session**: A session where the user has provided interests, constraints, or goals indicating they are in exploratory/guidance mode

## Requirements

### Requirement 1: Complete Counselor Lock Implementation

**User Story:** As a student in counselor mode, I want to stay in counselor mode throughout my conversation, so that I don't get interrupted with placement facts when I'm exploring career options.

#### Acceptance Criteria

1. WHEN a user has an active counselor profile (interests OR constraints OR goals), THE Structured_Knowledge_Handler SHALL check for active counselor session before returning structured responses
2. WHEN `get_structured_response()` is called with a session_id, THE Structured_Knowledge_Handler SHALL retrieve the user profile from conversation memory
3. IF the user profile contains interests OR constraints OR goals, THEN THE Structured_Knowledge_Handler SHALL return None to keep the user in counselor mode
4. WHEN a user in counselor mode asks "I want good salary", THE System SHALL route to counselor handler (not placements handler)
5. WHEN a user in counselor mode is on turn 3 or later, THE System SHALL NOT route to placements handler unless the user explicitly exits counselor mode

### Requirement 2: Eliminate Generic Mid-Conversation Responses

**User Story:** As a student providing information across multiple turns, I want the system to build forward from what I've told it, so that I don't get generic "I'm here to help" responses mid-conversation.

#### Acceptance Criteria

1. WHEN `_handle_general_exploration()` is called with an existing user profile, THE Counselor_Handler SHALL reference accumulated profile data in the response
2. IF the user profile contains interests, THEN THE Counselor_Handler SHALL acknowledge those interests in the response
3. IF the user profile contains constraints, THEN THE Counselor_Handler SHALL acknowledge those constraints in the response
4. IF the user profile contains goals, THEN THE Counselor_Handler SHALL acknowledge those goals in the response
5. THE Counselor_Handler SHALL NOT return generic greeting responses ("I'm here to help you find the right path") when a user profile exists
6. WHEN a user is on turn 2 or later with accumulated profile, THE Counselor_Handler SHALL provide next steps based on known information (not generic questions)

### Requirement 3: Add Human Judgement Tone to Recommendations

**User Story:** As a student receiving career advice, I want recommendations that feel like they come from a human counselor, so that I trust the guidance and feel supported in my decision.

#### Acceptance Criteria

1. WHEN `build_final_recommendation()` generates a recommendation, THE Decision_Synthesis_Layer SHALL include human judgement phrases
2. THE Decision_Synthesis_Layer SHALL use phrases like "If I were in your position" OR "In my experience" OR "Here's what I'd recommend" in final recommendations
3. WHEN presenting options, THE Decision_Synthesis_Layer SHALL use conversational language like "Here's the honest path" OR "Let me break this down"
4. WHEN explaining trade-offs, THE Decision_Synthesis_Layer SHALL use empathetic language like "I know this is tough" OR "This is a common dilemma"
5. THE Decision_Synthesis_Layer SHALL avoid robotic language like "Based on analysis" OR "The optimal solution is"

### Requirement 4: Handle Uncertainty with Appropriate Tone

**User Story:** As a student who is uncertain about my choices, I want the system to slow down and be more supportive, so that I don't feel pressured into decisions I'm not ready for.

#### Acceptance Criteria

1. WHEN a user query contains uncertainty signals ("idk", "maybe", "I'm not sure"), THE System SHALL extract ambiguity signals into the user profile
2. WHEN the user profile contains ambiguity signals, THE Counselor_Handler SHALL use a slower, more supportive tone
3. THE Counselor_Handler SHALL NOT provide final recommendations when the user has high ambiguity signals UNLESS an explicit decision query is detected
4. WHEN uncertainty is detected, THE Counselor_Handler SHALL ask clarifying questions before providing recommendations
5. THE Counselor_Handler SHALL use reassuring language like "It's okay to be unsure" OR "Let's explore this together"

### Requirement 4.5: Override Uncertainty Mode for Explicit Decision Queries (CRITICAL)

**User Story:** As a student who has been exploring options but is now ready for guidance, I want the system to provide a recommendation when I explicitly ask for one, even if I've expressed uncertainty earlier, so that I can get actionable advice when I need it.

**Rationale:** Without this override, the system can get stuck in exploratory mode indefinitely. A good advisor knows when to stop exploring and start deciding — this is what separates a chatbot from a trusted advisor.

#### Acceptance Criteria

1. WHEN a user query contains explicit decision signals ("what should i do", "what do you recommend", "suggest", "final advice", "what should i choose"), THE System SHALL detect this as a decision request
2. WHEN an explicit decision query is detected, THE System SHALL override uncertainty handling and enter decision synthesis mode
3. WHEN providing a recommendation with low confidence, THE System SHALL use a gentle but decisive tone that acknowledges uncertainty while still providing guidance
4. THE recommendation SHALL include human judgment phrases ("If I were in your position...") even when confidence is low
5. THE System SHALL NOT remain in purely exploratory mode when an explicit decision is requested

### Requirement 5: Verify Production Readiness

**User Story:** As a product owner, I want to verify that the Decision Synthesis Layer is production-ready, so that I can confidently deploy it to users.

#### Acceptance Criteria

1. WHEN the 5-turn conflict test is run, THE System SHALL pass all 12 verification checks
2. THE System SHALL demonstrate deterministic counselor lock (no routing to placements mid-conversation)
3. THE System SHALL demonstrate no generic responses in turns 2-5 of a conversation
4. THE System SHALL demonstrate human judgement tone in final recommendations
5. WHEN a harsh audit is performed with 10 test conversations, THE System SHALL achieve 10/10 GOOD rating

### Requirement 6: Test Round-Trip Property for Session Memory

**User Story:** As a developer, I want to ensure session memory is correctly persisted and retrieved, so that user profiles are not lost between turns.

#### Acceptance Criteria

1. FOR ALL valid user profiles, storing then retrieving the profile SHALL produce an equivalent profile object (round-trip property)
2. WHEN a user provides interests in turn 1, THE System SHALL retrieve those interests in turn 2
3. WHEN a user provides constraints in turn 2, THE System SHALL retrieve both interests and constraints in turn 3
4. WHEN a user provides goals in turn 3, THE System SHALL retrieve interests, constraints, and goals in turn 4
5. THE System SHALL maintain profile consistency across at least 10 conversation turns

### Requirement 7: Test Idempotence of Counselor Lock

**User Story:** As a developer, I want to ensure counselor lock is idempotent, so that checking the lock multiple times doesn't change system state.

#### Acceptance Criteria

1. WHEN counselor lock is checked for a session, THE System SHALL return the same result on subsequent checks (idempotence property)
2. WHEN `get_multi_intent_response()` checks for active counselor session, THE check SHALL NOT modify the user profile
3. WHEN `get_structured_response()` checks for active counselor session, THE check SHALL NOT modify the user profile
4. FOR ALL sessions with active profiles, checking counselor lock twice SHALL return identical results

### Requirement 8: Test Metamorphic Property for Profile Accumulation

**User Story:** As a developer, I want to ensure profile accumulation is monotonic, so that adding signals never removes existing information.

#### Acceptance Criteria

1. WHEN new signals are added to a user profile, THE profile size SHALL be greater than or equal to the previous size (metamorphic property)
2. WHEN interests are added, THE existing constraints and goals SHALL remain unchanged
3. WHEN constraints are added, THE existing interests and goals SHALL remain unchanged
4. WHEN goals are added, THE existing interests and constraints SHALL remain unchanged
5. FOR ALL signal additions, `len(new_profile.interests) >= len(old_profile.interests)` SHALL hold true

