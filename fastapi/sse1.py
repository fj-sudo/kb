# 案例1(生产者消费者模式)
# 	1、客户前端发ajax请求要发邮件并携带session_id，服务端直接回复收到，制造邮件开始
#     写一个接口，然后服务端立即回复消息收到，后台任务


# 	2、服务端就开始执行backgroundtasks当中造邮件的函数，造的邮件全部放在队列当中


# 	3、客户端想直接拿到造的邮件内容，造一个拿一个，那么客户端需要去发送订阅sse请求
# 	4、服务端需要写sse回复接口，流式返回，流式返回就是把一个生成器对象返回
# 		生成器函数当中就是从queue_dict当中获取自己session_id的队列，从队列当中一个一个yield球
#
# 注意：每个session_id对应自己的邮件队列


# atguigu/test/myfastapi/mount_static.py

import asyncio
from queue import Queue

from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware

from fastapi import BackgroundTasks, FastAPI, Query

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
q_dict = {}


def my_task(session_id: int):
    if not q_dict.get(session_id):
        q_dict[session_id] = Queue()
    q_dict_v = q_dict.get(session_id)
    q_dict_v.put("1")
    q_dict_v.put("2")
    q_dict_v.put("3")
    q_dict_v.put(None)


@app.get("/test")
def test(bk: BackgroundTasks, session_id: int = Query(...)):
    bk.add_task(my_task, session_id)
    return {"hello"}


@app.get("/sse")
def sse(session_id: int = Query(...)):
    async def a(session_id):
        while not q_dict.get(session_id):
            await asyncio.sleep(1)
        while 1:
            get = q_dict[session_id].get()
            yield f"data: {get}\n\n"
            await asyncio.sleep(1)
            if not get:
                break

    return StreamingResponse(a(session_id), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
