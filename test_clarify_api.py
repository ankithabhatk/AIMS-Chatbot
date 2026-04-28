"""
Direct API Test for Clarify UX System
======================================

Tests the backend /api/v1/chat endpoint directly to validate:
1. Low-signal query "mba" → clarify response
2. Low-signal query "mb" → clarify response  
3. Valid query "mba fees" → normal response
4. Edge case "fees" → clarify response

No UI automation - pure API validation
"""

import asyncio
import json
import httpx
from pathlib import Path

API_URL = "http://localhost:8000/api/v1/chat"
PROOF_DIR = Path("/tmp/proof")

async def test_query(query: str, test_name: str):
    """Test a query and return the response."""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"{'='*70}")
    print(f"Query: '{query}'")
    
    payload = {
        "query": query,
        "context": {"session_id": f"test-{test_name.replace(' ', '-')}"},
        "user": {
            "name": "Test Student",
            "email": "test@example.com",
            "phone": "9876543210"
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(API_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Save response to JSON
            json_file = PROOF_DIR / f"{test_name.replace(' ', '_')}_response.json"
            with open(json_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✓ Response saved: {json_file.name}")
            
            # Analyze response
            status = data.get("status", "—")
            answer = data.get("answer", "")
            suggestions = data.get("suggestions", [])
            confidence = data.get("confidence", 0)
            fallback = data.get("fallback", False)
            
            print(f"\nResponse Details:")
            print(f"  status: {status}")
            print(f"  fallback: {fallback}")
            print(f"  confidence: {confidence}")
            print(f"  answer length: {len(answer)} chars")
            print(f"  suggestions: {len(suggestions)}")
            
            if suggestions:
                for i, s in enumerate(suggestions, 1):
                    print(f"    {i}. {s}")
            
            if answer:
                print(f"\n  Answer preview:")
                for line in answer[:200].split('\n')[:3]:
                    print(f"    {line}")
                if len(answer) > 200:
                    print(f"    ...")
            
            return data
            
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

async def main():
    print("=" * 70)
    print("CLARIFY UX SYSTEM - DIRECT API TEST")
    print("=" * 70)
    
    results = {}
    
    try:
        # ====================================================================
        # TEST 1: Low-signal "mba"
        # ====================================================================
        results["test1"] = await test_query("mba", "test1_mba")
        
        # Validate
        assert results["test1"].get("status") == "clarify", \
            f"Expected status='clarify', got '{results['test1'].get('status')}'"
        assert len(results["test1"].get("suggestions", [])) > 0, \
            "Expected suggestions for 'mba' clarify"
        assert "need a bit more detail" in results["test1"].get("answer", "").lower(), \
            "Expected clarify message in answer"
        print("✓ PASS: Clarify response with suggestions")
        
        # ====================================================================
        # TEST 2: Very short "mb"
        # ====================================================================
        results["test2"] = await test_query("mb", "test2_mb")
        
        # Validate
        assert results["test2"].get("status") == "clarify", \
            f"Expected status='clarify', got '{results['test2'].get('status')}'"
        assert len(results["test2"].get("suggestions", [])) > 0, \
            "Expected suggestions for 'mb' clarify"
        print("✓ PASS: Very short query triggers clarify")
        
        # ====================================================================
        # TEST 3: Valid query "mba fees" (should NOT clarify)
        # ====================================================================
        results["test3"] = await test_query("mba fees", "test3_mba_fees")
        
        # Validate
        status = results["test3"].get("status", "")
        is_clarify = status == "clarify"
        assert not is_clarify, \
            f"Expected NO clarify for 'mba fees', but got status='{status}'"
        assert len(results["test3"].get("answer", "")) > 0, \
            "Expected answer for valid query"
        print("✓ PASS: Valid query does NOT trigger clarify")
        
        # ====================================================================
        # TEST 4: Edge case "fees"
        # ====================================================================
        results["test4"] = await test_query("fees", "test4_fees")
        
        # Validate
        assert results["test4"].get("status") == "clarify", \
            f"Expected status='clarify' for 'fees', got '{results['test4'].get('status')}'"
        assert len(results["test4"].get("suggestions", [])) > 0, \
            "Expected suggestions for 'fees' clarify"
        print("✓ PASS: Edge case 'fees' triggers clarify")
        
        # ====================================================================
        # TEST 5: Another valid query
        # ====================================================================
        results["test5"] = await test_query("admission process", "test5_admission")
        
        # Validate
        status = results["test5"].get("status", "")
        is_clarify = status == "clarify"
        assert not is_clarify, \
            f"Expected NO clarify for 'admission process', but got status='{status}'"
        print("✓ PASS: Multi-word query gets normal answer")
        
        # ====================================================================
        # SUMMARY
        # ====================================================================
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        
        print("\n📊 Test Results Summary:")
        print(f"  Test 1 (mba)              → clarify: {results['test1'].get('status') == 'clarify'}")
        print(f"  Test 2 (mb)               → clarify: {results['test2'].get('status') == 'clarify'}")
        print(f"  Test 3 (mba fees)         → NOT clarify: {results['test3'].get('status') != 'clarify'}")
        print(f"  Test 4 (fees)             → clarify: {results['test4'].get('status') == 'clarify'}")
        print(f"  Test 5 (admission process)→ NOT clarify: {results['test5'].get('status') != 'clarify'}")
        
        print(f"\n📁 Response files saved to: {PROOF_DIR}")
        print("\nGenerated JSON files:")
        for f in sorted(PROOF_DIR.glob("test*_response.json")):
            print(f"  - {f.name}")
        
        print("\n" + "=" * 70)
        print("PROOF: Clarify UX system is WORKING CORRECTLY")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ ASSERTION FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(main())
