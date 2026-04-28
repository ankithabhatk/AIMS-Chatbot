import asyncio
from app.api.chat_phase4 import chat_endpoint
from app.models.schemas import ChatRequest, ContextInfo
from fastapi import BackgroundTasks
import logging

logging.basicConfig(level=logging.INFO)

async def test_explicit_course():
    session_id = "test_explicit_001"
    
    test_queries = [
        "I want to do BCA",
        "I am interested in BCA",
        "BCA sounds good"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        req = ChatRequest(query=query, context=ContextInfo(session_id=session_id))
        bg = BackgroundTasks()
        res = await chat_endpoint(req, background_tasks=bg)
        
        print(f"Mode: {res['mode']}")
        print(f"Intent: {res['intent']}")
        print(f"Fallback: {res.get('fallback', False)}")
        print(f"Answer preview: {res['answer'][:150]}...")
        
        # Check if it locked
        if 'BCA' in res['answer'] and 'fallback' not in res['answer'].lower():
            print("✅ Locked and provided BCA guidance")
        else:
            print("❌ Did not lock properly")

asyncio.run(test_explicit_course())
