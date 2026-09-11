# atguigu/import_process/nodes/node_md_img.py
import base64
import os
import re
import time
from collections import deque
from pathlib import Path
from typing import Any, override

from langchain.chat_models import init_chat_model
from minio.deleteobjects import DeleteObject

from atguigu.config.congif import LoadLLM, LoadMinio
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.logger import logger
from atguigu.tool.minio_client import get_minio_client


class NodeMDImg(NodeBase):
    """
    MarkDown图片处理节点：多模态图片理解
    """

    name = "node_md_img"

    @override
    def process(self, state: ImportGraphState):  # pyright: ignore[reportIncompatibleMethodOverride]
        image_dir, image_dir_obj, md_content = self.check_data(state)
        if not image_dir_obj.exists():  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
            return {"md_content": md_content}
        if not os.listdir(image_dir):
            return {"md_content": md_content}
        image_dict_list = self.get_context(image_dir, md_content)
        llm_dict_list = self.get_llm_content(image_dict_list)

        md_path_obj, url_with_context_dict_list = self.put_minio_url(
            llm_dict_list, state
        )
        # 获得url替换md中的摘要和图片地址
        md_content, new_md_path = self.sub_md(
            md_content,
            md_path_obj,  # pyright: ignore[reportArgumentType]
            url_with_context_dict_list,  # pyright: ignore[reportArgumentType]
        )
        return {"md_content": md_content, "md_path": str(new_md_path)}

    def sub_md(
        self, md_content: Path, md_path_obj: list[Any], url_with_context_dict_list: Path
    ) -> tuple[str | bytes | Any, Any]:
        for i in url_with_context_dict_list:  # pyright: ignore[reportGeneralTypeIssues]
            url = i["url"]
            summary = i["summary"]

            pattern = re.compile(r"!\[.*?\]\(.*?" + re.escape(i["image_name"]) + r"\)")
            md_content = pattern.sub(lambda _: f"![{summary}]({url})", md_content)
        new_md_path = md_path_obj.parent / f"{md_path_obj.stem}_new.md"  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        with open(new_md_path, "w", encoding="utf-8") as f:
            _ = f.write(md_content)  # pyright: ignore[reportArgumentType]
        return md_content, new_md_path

    def put_minio_url(
        self, llm_dict_list: list[Any], state: ImportGraphState
    ) -> tuple[Path, list[Any]]:
        # 幂等性删除

        md_path_obj = Path(state["md_path"])
        md_title = md_path_obj.stem
        bucket_name = LoadMinio.minio_bucket_name
        client = get_minio_client()
        objects = client.list_objects(f"{bucket_name}", recursive=True, prefix=md_title)
        delete_objects = [DeleteObject(i.object_name) for i in objects]  # pyright: ignore[reportArgumentType]

        errors = client.remove_objects(
            bucket_name,  # pyright: ignore[reportArgumentType]
            delete_objects,
        )
        for error in errors:
            print("error occurred when deleting object", error)
        url_with_context_dict_list = []
        # 上传图片url
        for i in llm_dict_list:
            image_path_obj = Path(i["image_path"])
            minio_object_path = f"{md_title}" + "/" + f"{image_path_obj.name}"

            _ = client.fput_object(
                bucket_name=bucket_name,  # pyright: ignore[reportArgumentType]
                object_name=minio_object_path,
                file_path=str(image_path_obj),
            )

            minio_object_url = f"http://192.168.10.4:9000/{bucket_name}/{md_title}/{image_path_obj.name}"

            url_with_context_dict_list.append({**i, "url": minio_object_url})
        return md_path_obj, url_with_context_dict_list  # pyright: ignore[reportReturnType, reportUnknownVariableType]

    def get_llm_content(self, image_dict_list: list[Any]):
        llm = init_chat_model(
            "openai:qwen3-vl-flash",
            base_url=LoadLLM.openai_api_base,
            api_key=LoadLLM.openai_api_key,
            temperature=LoadLLM.llm_default_temperature,
        )

        llm_dict_list = []
        dq = deque(maxlen=30)
        for i in image_dict_list:
            current_time = time.time()
            while dq and current_time - dq[0] > 60:
                dq.popleft()
            if len(dq) >= dq.maxlen:  # pyright: ignore[reportOperatorIssue]
                need_sleep_time = 60 - (current_time - dq[0])
                if need_sleep_time > 0:
                    time.sleep(need_sleep_time)
                current_time = time.time()
                while dq and (current_time - dq[0]) > 60:
                    dq.popleft()
            dq.append(current_time)
            with open(i["image_path"], "rb") as f:
                base64_data = base64.b64encode(f.read()).decode("utf-8")
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/jpeg;base64," + base64_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": f"""这是一张图片，图片上文部分为"{i.get("pre_content")}"，
                                            下文部分为"{i.get("post_content")}"，请用中文简要总结这张图片的摘要,字数在50字以内。""",
                        },
                    ],
                },
            ]
            llm_invoke = llm.invoke(messages)
            llm_dict_list.append(
                {
                    "image_name": i["image_name"],
                    "image_path": i["image_path"],
                    "summary": llm_invoke.content,
                }
            )
        return llm_dict_list

    def get_context(self, image_dir: Path, md_content: Path) -> list[Any]:
        image_name_list = os.listdir(image_dir)
        image_dict_list = []
        IMAGE_EXTENSIONS = {
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".webp",
            ".svg",
            ".tiff",
            ".tif",
        }
        for image_name in image_name_list:
            image_name_obj = Path(image_name)
            if image_name_obj.suffix.lower() not in IMAGE_EXTENSIONS:
                logger.warning("图片格式不匹配，跳过")
                continue
            pattern = re.compile(r"!\[.*?\]\(.*?" + re.escape(image_name) + r"\)")
            match = pattern.search(md_content)  # pyright: ignore[reportCallIssue, reportArgumentType]
            if not match:
                logger.info("没有引用该图片")
                continue
            # span = match[span]
            start, end = match.span()
            pre_content = md_content[max(start - 300, 0) : start]  # pyright: ignore[reportIndexIssue]
            post_content = md_content[end : min(end + 300, len(md_content))]  # pyright: ignore[reportIndexIssue, reportArgumentType]
            image_dict_list.append(
                {
                    "pre_content": pre_content,
                    "post_content": post_content,
                    "image_name": image_name,
                    "image_path": str(image_dir / image_name),
                }
            )
        return image_dict_list

    def check_data(self, state: ImportGraphState) -> tuple[Path, str, Path]:
        md_path = state.get("md_path", "")
        md_path_obj = Path(md_path)
        if not md_path:
            logger.error("文件路径为空")
            raise Exception("文件路径为空")
        if not md_path_obj.exists():
            logger.error("文件不存在")
            raise Exception("文件不存在")
        with open(md_path_obj, "r", encoding="utf-8") as f:
            md_content = f.read()
        image_dir = md_path_obj.parent / "images"
        image_dir_obj = Path(image_dir)
        return image_dir, image_dir_obj, md_content


if __name__ == "__main__":
    md = NodeMDImg()
    print(
        md(
            {  # pyright: ignore[reportArgumentType]
                "md_path": r"D:\Software\SGG\资料\视频分发\掌柜智库01\资料\05-设备手册汇总"
                r"\doc\hak180产品安全手册\hak180产品安全手册.md",
            }
        )
    )
