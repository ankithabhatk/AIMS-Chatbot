import asyncio
from app.api.chat_phase4 import chat_endpoint
from app.models.schemas import ChatRequest, ContextInfo
from fastapi import BackgroundTasks
import logging

logging.basicConfig(level=logging.DEBUG)

async def test():
    req = ChatRequest(query="mba", context=ContextInfo(session_id="conv_123"))
    bg = BackgroundTasks()
    res = await chat_endpoint(req, background_tasks=bg)
    print(res)

asyncio.run(test())
