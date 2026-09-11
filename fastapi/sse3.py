import asyncio
from asyncio import Queue

import uvicorn
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from fastapi import BackgroundTasks, FastAPI, Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_headers=["*"],
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=True,
)


class User(BaseModel):
    query: str
    session_id: int


q_dict = {}


async def task(user):
    session_id = user.session_id
    query = user.query
    if not q_dict.get(session_id):
        q_dict[session_id] = Queue()
    q = q_dict.get(session_id)
    await q.put({"event": "processing", "data": 1})
    await q.put({"event": "processing", "data": 2})
    await q.put({"event": "processing", "data": 3})
    await q.put({"event": "final", "data": ""})


@app.post("/test02")
def test(bk: BackgroundTasks, user: User):
    bk.add_task(task, user)
    return {"hi": "hi"}


@app.get("/sse/{session_id}")
def sse(session_id: int = Path(...)):
    return StreamingResponse(aaa(session_id), media_type="text/event-stream")


async def aaa(session_id):
    while not q_dict.get(session_id):
        await asyncio.sleep(1)
    while 1:
        q = q_dict.get(session_id)
        dict = await q.get()
        yield f"event: {dict['event']}\n"
        yield f"data: {dict['data']}\n\n"
        await asyncio.sleep(1)
        if dict["event"] == "final":
            break


uvicorn.run("sse3:app", port=8000)
