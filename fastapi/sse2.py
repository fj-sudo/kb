import time
from queue import Queue

import uvicorn
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

from fastapi import BackgroundTasks, Body, FastAPI

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_headers=["*"],
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=True,
)
q_dict = {}


def task(user):
    session_id = user.session_id
    query = user.query
    if not q_dict.get(session_id):
        q_dict[session_id] = Queue()
    q = q_dict.get(session_id)
    q.put(1)
    q.put(2)
    q.put(3)
    q.put(None)


class User(BaseModel):
    session_id: int = Field(...)
    query: str = Field(...)


@app.post("/test02")
def test(bk: BackgroundTasks, user: User = Body(...)):
    bk.add_task(task, user)
    return {"hello": "hello"}


def decccccc(session_id):
    while not q_dict:
        time.sleep(1)
    while 1:
        q = q_dict.get(session_id)
        data = q.get()
        yield f"data: {data}\n\n"
        time.sleep(1)
        if not data:
            break


@app.get("/sse/{session_id}")
def sse(session_id: int):
    return StreamingResponse(decccccc(session_id), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run("sse2:app", port=8000, reload=True)
