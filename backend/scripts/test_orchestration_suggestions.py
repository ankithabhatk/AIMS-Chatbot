from backend.app.services.orchestration.engine import execute_orchestration, OrchestrationResult, generate_smart_suggestions


def test_generate_smart_suggestions_fees_mba():
    query = "mba fees"
    intent = "fees"
    entities = {"course": "mba"}
    history = []
    suggestions = generate_smart_suggestions(query, intent, entities, history)
    expected_suggestions = ["MBA admission", "MBA placements", "MBA specializations", "Admission process"]
    assert suggestions == expected_suggestions, f"Expected {expected_suggestions}, got {suggestions}"

def test_generate_smart_suggestions_placements():
    query = "placement record"
    intent = "placements"
    entities = {}
    history = []
    suggestions = generate_smart_suggestions(query, intent, entities, history)
    expected_suggestions = ["Top recruiters", "Average package", "Internship opportunities", "MBA fees"]
    assert suggestions == expected_suggestions, f"Expected {expected_suggestions}, got {suggestions}"

def test_generate_smart_suggestions_fallback():
    query = "??"
    intent = "general"
    entities = {}
    history = []
    suggestions = generate_smart_suggestions(query, intent, entities, history)
    expected_suggestions = ["MBA fees", "BCA admission", "Placement record", "Hostel facilities"]
    assert suggestions == expected_suggestions, f"Expected {expected_suggestions}, got {suggestions}"

def test_generate_smart_suggestions_admission_bca():
    query = "bca admission"
    intent = "admission"
    entities = {"course": "bca"}
    history = []
    suggestions = generate_smart_suggestions(query, intent, entities, history)
    expected_suggestions = ["BCA admission", "BCA placements", "BCA specializations", "Eligibility criteria"]
    assert suggestions == expected_suggestions, f"Expected {expected_suggestions}, got {suggestions}"

def test_generate_smart_suggestions_courses_mca():
    query = "mca courses"
    intent = "courses"
    entities = {"course": "mca"}
    history = []
    suggestions = generate_smart_suggestions(query, intent, entities, history)
    expected_suggestions = ["MCA admission", "MCA placements", "MCA specializations", "MBA details"]
    assert suggestions == expected_suggestions, f"Expected {expected_suggestions}, got {suggestions}"


def test_execute_orchestration_suggestions_fees_mba():
    query = "mba fees"
    result = execute_orchestration(query)
    expected_suggestions = ["MBA admission", "MBA placements", "MBA specializations", "Admission process"]
    assert result.suggestions == expected_suggestions, f"Expected {expected_suggestions}, got {result.suggestions}"

def test_execute_orchestration_suggestions_placements():
    query = "placement record"
    result = execute_orchestration(query)
    expected_suggestions = ["Top recruiters", "Average package", "Internship opportunities", "MBA fees"]
    assert result.suggestions == expected_suggestions, f"Expected {expected_suggestions}, got {result.suggestions}"

def test_execute_orchestration_suggestions_fallback():
    query = "??"
    result = execute_orchestration(query)
    expected_suggestions = ["MBA fees", "BCA admission", "Placement record", "Hostel facilities"]
    assert result.suggestions == expected_suggestions, f"Expected {expected_suggestions}, got {result.suggestions}"


if __name__ == "__main__":
    print("Running tests for Smart Suggestion Engine...")
    test_generate_smart_suggestions_fees_mba()
    test_generate_smart_suggestions_placements()
    test_generate_smart_suggestions_fallback()
    test_generate_smart_suggestions_admission_bca()
    test_generate_smart_suggestions_courses_mca()
    test_execute_orchestration_suggestions_fees_mba()
    test_execute_orchestration_suggestions_placements()
    test_execute_orchestration_suggestions_fallback()
    print("All Smart Suggestion Engine tests passed!")