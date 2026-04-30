"""
Brutal Test Queries - Real-world messy queries that will break the system.

These are NOT polite test queries.
These are how real users actually talk.

Categories:
1. Real-style queries (messy, natural language)
2. Multi-intent queries (fees + hostel + placements)
3. Vague queries (maybe, not sure, thinking)
4. Break tests (everything, tell all, mixed topics)
5. Edge cases (typos, slang, incomplete)
"""

BRUTAL_QUERIES = [
    # Category 1: Real-style queries (how users actually talk)
    "i want something in computers what can i take",
    "how much money for bca",
    "hostel available or not",
    "tell fees and placement",
    "maybe mba idk",
    "i like coding what should i choose",
    "fees structure",
    "scholarship info",
    "how to apply",
    "campus life",
    "what courses you have",
    "tell me about aims",
    "is it good college",
    "placement record",
    "hostel facility",
    
    # Category 2: Multi-intent queries (multiple topics in one)
    "fees and hostel and placements",
    "what about bca fees and hostel",
    "tell me courses and fees",
    "admission process and documents",
    "scholarship and fees structure",
    "hostel and campus facilities",
    "placements and salary packages",
    "courses offered and eligibility",
    "fees for mba and bca",
    "admission dates and fees",
    
    # Category 3: Vague queries (uncertain, exploratory)
    "i want to study but not sure what",
    "maybe computer course",
    "thinking about management",
    "not decided yet",
    "what should i do",
    "confused between bca and mca",
    "is mba good",
    "which course is best",
    "i like business",
    "interested in technology",
    
    # Category 4: Break tests (asking for everything)
    "tell everything about bca",
    "complete information about mba",
    "all details",
    "everything i need to know",
    "full information about aims",
    "what all courses and fees",
    "give me all details about admission",
    
    # Category 5: Edge cases (typos, slang, incomplete)
    "bca fee",
    "mba",
    "hostel",
    "fees",
    "courses",
    "scholarship",
    "admission",
    "placements",
]

# Categorized for analysis
CATEGORIES = {
    "real_style": BRUTAL_QUERIES[0:15],
    "multi_intent": BRUTAL_QUERIES[15:25],
    "vague": BRUTAL_QUERIES[25:35],
    "break_tests": BRUTAL_QUERIES[35:42],
    "edge_cases": BRUTAL_QUERIES[42:50],
}

# Expected behaviors (for analysis, not pass/fail)
EXPECTED_BEHAVIORS = {
    "i want something in computers what can i take": {
        "should": "Suggest BCA/MCA courses",
        "should_not": "Ask for lead capture, return PhD content"
    },
    "how much money for bca": {
        "should": "Return BCA fees",
        "should_not": "Ask which course, return other course fees"
    },
    "fees and hostel and placements": {
        "should": "Handle multi-intent, return info for all three",
        "should_not": "Return only one topic, ask for clarification"
    },
    "tell everything about bca": {
        "should": "Return comprehensive BCA info (courses, fees, eligibility)",
        "should_not": "Return only one aspect, overflow with irrelevant content"
    },
    "bca": {
        "should": "Return BCA overview or ask what specifically",
        "should_not": "Return fees only, return other courses"
    },
}
