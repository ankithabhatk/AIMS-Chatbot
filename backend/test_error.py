import asyncio
from app.api.chat_phase4 import chat_endpoint
from app.models.schemas import ChatRequest

async def main():
    class Context:
        session_id = "test-hostel-short5"
    class Req:
        query = "hostel?"
        user = None
        context = Context()

    class BackgroundTasks:
        def add_task(self, func, *args, **kwargs):
            pass

    try:
        res = await chat_endpoint(Req(), BackgroundTasks())
        print(res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
