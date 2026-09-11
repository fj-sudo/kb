import json
from uuid import uuid4

import uvicorn
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

from atguigu.query_process.main_graph import QueryMainGraphRunner
from atguigu.tool.mongon_tool import clear_history, get_recent_messages
from atguigu.tool.task_utils import (
    TASK_STATUS_COMPLETED,
    TASK_STATUS_PROCESSING,
    create_q,
    get_q,
    get_task_info,
    put_q,
    update_task_status,
)
from fastapi import BackgroundTasks, Body, FastAPI, Path

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_headers=["*"],
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=True,
)


@app.get("/health")
def health():
    return {"hi": 1}


@app.get("/history/{session_id}")
def history(session_id: str = Path(...)):
    recent_messages = get_recent_messages(session_id)
    for i in recent_messages:
        i["_id"] = str(i["_id"])
    print(recent_messages)
    return {"items": sorted(recent_messages, key=lambda x: x["ts"])}


@app.delete("/history/{session_id}")
def del_history(session_id: str = Path(...)):
    clear_history(session_id)
    return {"code": "ok"}


class Body_info(BaseModel):
    query: str = Field(...)
    session_id: str = Field(...)


def start_main_graph(body_info, task_id):
    init_state = {
        "session_id": body_info.session_id,
        "original_query": body_info.query,
        "task_id": task_id,
    }
    update_task_status(task_id, TASK_STATUS_PROCESSING)
    put_q(task_id, "progress", get_task_info(task_id))
    QueryMainGraphRunner.create_and_run(
        init_state,
    )
    update_task_status(task_id, TASK_STATUS_COMPLETED)
    put_q(task_id, "progress", get_task_info(task_id))


@app.post("/query")
def query(bk: BackgroundTasks, body_info: Body_info = Body(...)):
    task_id = str(uuid4())
    create_q(task_id)
    bk.add_task(start_main_graph, body_info, task_id)
    return {
        "task_id": task_id,  # 放进响应体返回给前端
    }


@app.get("/stream/{task_id}")
def sse(task_id: str = Path(...)):
    def interior():
        while 1:
            q = get_q(task_id)
            yield f"event: {q.get('event')}\n"
            yield f"data: {json.dumps(q.get('data'), ensure_ascii=False)}\n\n"

    return StreamingResponse(interior(), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run(app, port=8001)
