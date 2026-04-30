# Requirements Document

## Introduction

The Confidence-Calibrated Recommendations feature adds adaptive tone mapping to the career counseling chatbot's recommendation system. The system currently provides recommendations with uniform tone regardless of the user's confidence level. This feature will adjust recommendation tone based on detected user confidence (low, medium, high) to make interactions feel more natural and adaptive rather than scripted.

The system already extracts confidence levels from user signals and maintains them in the user profile. This feature focuses solely on mapping those confidence levels to appropriate recommendation tones without modifying existing decision logic or override mechanisms.

## Glossary

- **Recommendation_System**: The component that generates career counseling recommendations
- **Confidence_Level**: A categorical value ("low", "medium", "high") representing user's certainty about their situation
- **Tone_Mapper**: The component that maps confidence levels to appropriate recommendation tones
- **Recommendation_Tone**: The linguistic style and strength of language used in recommendations
- **User_Profile**: The data structure containing accumulated user information including confidence_level field
- **Decision_Override**: Existing mechanism that provides decisive recommendations when explicitly requested, regardless of confidence level

## Requirements

### Requirement 1: Detect User Confidence Level

**User Story:** As a system, I want to access the user's confidence level from their profile, so that I can adapt recommendation tone appropriately.

#### Acceptance Criteria

1. WHEN building a recommendation, THE Recommendation_System SHALL retrieve the confidence_level field from the User_Profile
2. THE Recommendation_System SHALL recognize three confidence_level values: "low", "medium", and "high"
3. IF the confidence_level field is missing or invalid, THEN THE Recommendation_System SHALL default to "medium" confidence_level

### Requirement 2: Map Confidence to Tone Parameters

**User Story:** As a system, I want to map confidence levels to specific tone parameters, so that recommendations match the user's certainty state.

#### Acceptance Criteria

1. WHEN confidence_level is "low", THE Tone_Mapper SHALL select exploratory tone parameters with gentle decision language
2. WHEN confidence_level is "medium", THE Tone_Mapper SHALL select balanced tone parameters with practical language
3. WHEN confidence_level is "high", THE Tone_Mapper SHALL select decisive tone parameters with strong recommendation language
4. THE Tone_Mapper SHALL provide tone parameters including prefix phrases and judgment phrase strength
5. FOR ALL confidence levels, the Tone_Mapper SHALL produce tone parameters that result in natural human language

### Requirement 3: Inject Tone into Recommendations

**User Story:** As a user, I want recommendations that match my confidence level, so that the system feels adaptive and realistic.

#### Acceptance Criteria

1. WHEN generating a recommendation, THE Recommendation_System SHALL apply tone parameters from the Tone_Mapper
2. THE Recommendation_System SHALL inject tone-appropriate prefix phrases into recommendations
3. THE Recommendation_System SHALL adjust judgment phrase strength based on tone parameters
4. THE Recommendation_System SHALL produce recommendations that feel natural and not robotic
5. FOR ALL recommendations, the output SHALL maintain grammatical correctness and professional quality

### Requirement 4: Preserve Decision Override Behavior

**User Story:** As a user with low confidence who explicitly asks for a decision, I want to receive a clear recommendation, so that I get guidance when I need it.

#### Acceptance Criteria

1. WHEN Decision_Override is active, THE Recommendation_System SHALL provide decisive recommendations regardless of confidence_level
2. THE Recommendation_System SHALL NOT modify existing Decision_Override logic
3. WHEN Decision_Override is active with low confidence_level, THE Recommendation_System SHALL combine gentle acknowledgment with clear decision
4. THE Recommendation_System SHALL maintain existing force parameter behavior in build_final_recommendation function

### Requirement 5: Tone Variation Examples

**User Story:** As a developer, I want clear examples of tone variation, so that I can verify the system produces appropriate output.

#### Acceptance Criteria

1. WHEN confidence_level is "low", THE Recommendation_System SHALL produce recommendations similar to "It's okay to feel unsure — but here's one way to approach this"
2. WHEN confidence_level is "medium", THE Recommendation_System SHALL produce recommendations similar to "A practical path would be..."
3. WHEN confidence_level is "high", THE Recommendation_System SHALL produce recommendations similar to "I'd strongly recommend..."
4. FOR ALL confidence levels, recommendations SHALL include appropriate human judgment phrases
5. FOR ALL confidence levels, recommendations SHALL avoid salesy or marketing language

### Requirement 6: Minimal System Changes

**User Story:** As a developer, I want to add tone calibration without rewriting existing logic, so that I preserve working functionality.

#### Acceptance Criteria

1. THE Tone_Mapper SHALL integrate with existing build_final_recommendation function
2. THE Recommendation_System SHALL NOT modify existing decision synthesis logic
3. THE Recommendation_System SHALL NOT modify existing profile accumulation logic
4. THE Recommendation_System SHALL NOT modify existing counselor routing logic
5. THE Tone_Mapper SHALL be implementable as a focused, minimal addition to the codebase
