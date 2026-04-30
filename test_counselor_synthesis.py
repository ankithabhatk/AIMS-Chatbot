import asyncio
import os
import sys

# Ensure backend is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from backend.app.services.counselor_handler import get_counselor_response
from backend.app.services.intelligence_layer import get_intelligence_layer
from backend.app.services.conversation_memory import get_memory_store
import uuid

async def run_sequence():
    session_id = f"test-counselor-{uuid.uuid4().hex[:8]}"
    print(f"--- STARTING RAG COUNSELOR SYNTHESIS TEST (Session: {session_id}) ---\n")
    
    queries = [
        "idk",
        "maybe coding",
        "I like coding",
        "actually I hate coding",
        "maybe business is better"
    ]
    
    intel = get_intelligence_layer()
    memory = get_memory_store()
    
    for i, q in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"TURN {i}: User says -> '{q}'")
        print(f"{'='*60}")
        
        # 1. Process query
        query_data = intel.process_query(q, session_id)
        
        # 2. Call counselor handler directly to bypass chat router constraints for testing
        print(">> Calling get_counselor_response...")
        
        # Mocking the prompt print by patching AILlmProvider temporarily
        from backend.app.services.llm.provider import AILlmProvider
        original_generate = AILlmProvider.generate_response
        
        captured_prompt = None
        def mock_generate(self, query, context, system_prompt):
            nonlocal captured_prompt
            captured_prompt = system_prompt
            return original_generate(self, query, context, system_prompt)
            
        AILlmProvider.generate_response = mock_generate
        
        result = get_counselor_response(q, session_id, query_data=query_data)
        
        AILlmProvider.generate_response = original_generate
        
        # 3. Retrieve state
        profile = memory.get_profile(session_id)
        
        print("\n[CONFIDENCE & EMOTION EVOLUTION]")
        print(f"Score: {profile.confidence_score:.3f}")
        print(f"Level: {profile.confidence_level.upper()}")
        print(f"Interests: {profile.interests}")
        print(f"Emotions: {profile.recent_emotions}")
        
        if captured_prompt:
            print("\n[PROMPT SENT TO QWEN/GROQ]")
            print(captured_prompt)
            
        print("\n[FINAL GENERATED RESPONSE]")
        if result:
            print(f"Provider Used: {result.get('provider')}")
            print(f"Reflection Summary: {result.get('reflection')}")
            print(f"Response: {result.get('answer')}")
        else:
            print("None (Query was not classified as exploratory or counselor)")
            
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(run_sequence())
