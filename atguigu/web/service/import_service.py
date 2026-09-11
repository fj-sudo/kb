import shutil
import time
import uuid
from datetime import datetime
from pathlib import Path

import uvicorn
from starlette.middleware.cors import CORSMiddleware

from atguigu.config.congif import LoadMinio
from atguigu.import_process.main_graph import MainGraph
from atguigu.tool.minio_client import get_minio_client
from atguigu.tool.task_utils import (
    add_done_task,
    add_node_duration,
    add_running_task,
    get_task_info,
    update_task_status,
)
from fastapi import BackgroundTasks, FastAPI, File, UploadFile

app = FastAPI(
    title="掌柜智库-导入API", description="此文档是掌柜智库导入流程的API接口说明"
)

# 2. 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许的源
    allow_credentials=True,  # 允许携带cookie
    allow_methods=["*"],  # 允许的请求方法
    allow_headers=["*"],  # 允许的请求头
)


def run_main_graph(task_id, local_path, local_dir):
    try:
        update_task_status(task_id, "processing")
        MainGraph.create_run(
            {"task_id": task_id, "local_file_path": local_path, "local_dir": local_dir}
        )
        update_task_status(task_id, "completed")
    except Exception as e:
        from atguigu.tool.logger import logger

        logger.error(f"任务执行失败，错误信息：{e}")
        update_task_status(task_id, "failed")


@app.post("/upload")
def upload(bk: BackgroundTasks, file: UploadFile = File(..., description="上传文件")):
    task_id = str(uuid.uuid4())

    start = time.time()
    add_running_task(task_id, "upload_file")
    time_now = str(datetime.now().strftime("%Y-%m-%d"))
    local_path = rf"D:\Software\SGG\output\{time_now}" + "\\" + str(file.filename)
    local_dir = rf"D:\Software\SGG\output\{time_now}"
    local_dir_obj = Path(local_dir)
    if not local_dir_obj.exists():
        local_dir_obj.mkdir(parents=True, exist_ok=True)
    with open(local_path, "wb") as f:
        shutil.copyfileobj(file.file, f, 1024 * 1024)

    get_minio_client().fput_object(
        LoadMinio.minio_bucket_name,
        object_name=rf"pdf_file/{time_now}/{file.filename}",
        file_path=rf"D:\Software\SGG\output\{time_now}" + "\\" + str(file.filename),
    )

    add_done_task(task_id, "upload_file")
    add_node_duration(task_id, "upload_file", time.time() - start)
    bk.add_task(run_main_graph, task_id, local_path, local_dir)
    return {"task_id": task_id}


@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    return get_task_info(task_id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
