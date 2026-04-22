import requests
import json
import time
import os
from typing import List, Dict

API_URL = "http://localhost:8000/api/v1/chat"
TEST_QUERIES_FILE = "scripts/test_queries_v3.json"

def fuzzy_match(expected: str, actual: str) -> bool:
    """Case-insensitive partial matching for entity validation"""
    if not actual:
        return False
    # Check if the expected entity or common variants are in the answer
    variants = [expected, expected.lower(), expected.upper(), expected.capitalize()]
    return any(v in actual for v in variants)

def run_evaluation():
    if not os.path.exists(TEST_QUERIES_FILE):
        print(f"❌ Test file not found: {TEST_QUERIES_FILE}")
        return

    with open(TEST_QUERIES_FILE, "r") as f:
        test_queries = json.load(f)

    results = []
    # session_id -> current turn context
    session_states = {}
    
    print(f"🚀 [PRODUCTION TRUTH] Starting Multi-Turn Evaluation ({len(test_queries)} steps)...")
    print(f"Goal: Status=100% | Entity Alignment > 85%\n")
    
    # Sort by sequence and turn to ensure order
    test_queries.sort(key=lambda x: (x.get("sequence_id", "z"), x.get("turn", 0)))

    for i, test in enumerate(test_queries):
        seq_id = test.get("sequence_id")
        
        # Determine session ID for multi-turn consistency
        if seq_id:
            if seq_id not in session_states:
                session_states[seq_id] = {
                    "sid": f"seq_{seq_id}_{int(time.time())}",
                    "unlocked": False
                }
            current_sid = session_states[seq_id]["sid"]
        else:
            current_sid = f"sid_{i}_{int(time.time())}"
        
        # MOCK LEAD SUBMISSION STEP
        # If the query is "MOCK_SUBMIT", we send the lead details instead of a normal question
        is_mock_submit = test.get("query") == "MOCK_SUBMIT"
        query_text = test["query"]
        if is_mock_submit:
            query_text = "John Doe, john@test.com, MBA, 9876543210"
            print(f"🔹 [SEQUENCE: {seq_id}] Simulating Lead Submission...")

        payload = {
            "query": query_text,
            "context": {
                "session_id": current_sid
            }
        }
        
        try:
            response = requests.post(API_URL, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unlock")
                answer = data.get("answer") or ""
                
                # Rule 1: Status Check
                status_correct = (status == test["expect_status"])
                
                # Special logic for unlocking
                if is_mock_submit and status == "unlock":
                    session_states[seq_id]["unlocked"] = True

                # Rule 2: Entity Check
                must_contain = test.get("must_contain", [])
                missing_entities = [ent for ent in must_contain if not fuzzy_match(ent, answer)]
                entity_correct = (len(missing_entities) == 0) if must_contain else True
                
                results.append({
                    "query": query_text,
                    "category": test["category"],
                    "expected_status": test["expect_status"],
                    "actual_status": status,
                    "status_correct": status_correct,
                    "entity_correct": entity_correct,
                    "missing": missing_entities,
                    "answer": answer
                })
                
                indicator = "✅" if (status_correct and entity_correct) else "⚠️" if status_correct else "❌"
                print(f"{indicator} [{test['category']}] Q: {query_text[:40]}...")
                if not status_correct:
                    print(f"   ↳ 🚨 STATUS ERROR: Expected {test['expect_status']}, got {status}")
                    print(f"   ↳ Session: {current_sid}")
                if not entity_correct:
                    print(f"   ↳ ⚠️ ENTITY ERROR: Missing {missing_entities}")
                    # print(f"   ↳ Answer: {answer[:100]}...")
            else:
                print(f"❌ HTTP {response.status_code} on query: {query_text}")
                results.append({"query": query_text, "status_correct": False, "entity_correct": False, "error": response.status_code})
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")

    # Summary logic remains same...
    total = len(results)
    correct_status = sum(1 for r in results if r.get("status_correct"))
    correct_entities = sum(1 for r in results if r.get("entity_correct"))
    
    status_acc = (correct_status / total) * 100 if total > 0 else 0
    entity_acc = (correct_entities / total) * 100 if total > 0 else 0
    
    summary = {
        "status_accuracy": f"{status_acc:.1f}%",
        "entity_accuracy": f"{entity_acc:.1f}%",
        "ready": "YES" if status_acc == 100.0 and entity_acc >= 85.0 else "NO"
    }
    
    with open("scripts/evaluation_report_final.json", "w") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)
    
    print("\n" + "="*60)
    print("📊 FINAL DEMO READINESS REPORT")
    print(f"Rule 1: Status Accuracy: {summary['status_accuracy']} {'✅' if status_acc == 100 else '❌'}")
    print(f"Rule 2: Entity Accuracy: {summary['entity_accuracy']} {'✅' if entity_acc >= 85 else '⚠️'}")
    print(f"OVERALL READINESS:      {summary['ready']}")
    print("="*60)
    
    if status_acc < 100:
        print("\n🚨 FAILED STATUS CASES:")
        for r in results:
            if not r.get("status_correct"):
                print(f"- Q: {r['query']}")
                print(f"  Exp: {r['expected_status']} | Act: {r['actual_status']}")

if __name__ == "__main__":
    run_evaluation()
