import asyncio
from app.api.chat_phase4 import chat_endpoint
from app.models.schemas import ChatRequest, ContextInfo
from fastapi import BackgroundTasks
import logging

logging.basicConfig(level=logging.INFO)

async def test_conversation():
    session_id = "test_001"
    
    queries = [
        "I want to do BCA",
        "yeah tell me fees",
        "okay sounds good"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"Turn {i}: {query}")
        print('='*60)
        
        req = ChatRequest(query=query, context=ContextInfo(session_id=session_id))
        bg = BackgroundTasks()
        res = await chat_endpoint(req, background_tasks=bg)
        
        print(f"Answer: {res['answer'][:200]}...")
        print(f"Mode: {res['mode']}")
        print(f"Intent: {res['intent']}")
        print(f"Turn count: {res['turn_count']}")

asyncio.run(test_conversation())
