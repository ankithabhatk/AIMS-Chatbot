#!/usr/bin/env python3
"""Debug failing test cases"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def debug_query(query: str):
    """Show full response for a query"""
    print(f"\n{'='*70}")
    print(f"Query: '{query}'")
    print('='*70)
    
    response = requests.post(
        f"{BASE_URL}/api/v1/chat",
        json={"query": query, "session_id": "debug"},
        timeout=15
    )
    
    data = response.json()
    
    print(f"Mode: {data.get('mode')}")
    print(f"Fallback: {data.get('fallback')}")
    print(f"Confidence: {data.get('confidence')}")
    print(f"\nAnswer ({len(data.get('answer', ''))} chars):")
    print(f"---")
    print(data.get('answer', ''))
    print(f"---")

# Debug the failing cases
debug_query("hostel")
debug_query("What about placements?")
debug_query("campus facilities")
