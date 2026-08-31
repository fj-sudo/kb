# atguigu/import_process/nodes/node_item_name_recognition.py
import json
from prompt
from langchain.chat_models import init_chat_model
from openai import api_key, base_url
from torch.cuda import temperature

from atguigu.config.congif import LoadLLM
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState


class NodeItemNameRecognition(NodeBase):
    """
    主体识别节点：主体识别与标签提取
    """

    name = "node_item_name_recognition"

    def process(self, state: ImportGraphState):
        chunks_list = state.get("chunks")
        file_title = state.get("file_title")
        if not chunks_list:
            raise Exception("切片内容为空")
        if not file_title:
            raise Exception("文件不能为空")
        # 取前20个chunk给llm，返回item_name
        print(chunks_list)
        chunks_list = chunks_list[:20]
        chunks = "\n"
        for chunk in chunks_list:
            md_content = chunk.get("md_content")
            chunks += file_title + "\n" + md_content
            if len(chunks) > 1000:
                break
        chunks_str = chunks[:1000]
        print(chunks_str)
        llm=init_chat_model(
            f"openai:{LoadLLM.vl_model}",
            base_url=LoadLLM.openai_api_base,
            api_key=LoadLLM.openai_api_key,
            temperature=float(LoadLLM.llm_default_temperature)
        )
        message=(
            "user":ITEM_NAME_USER_PROMPT_TEMPLATE,
        )
        return state


if __name__ == "__main__":
    node = NodeItemNameRecognition()
    path = r"D:\Software\SGG\资料\视频分发\掌柜智库01\资料\05-设备手册汇总\doc\hak180产品安全手册\chunks.json"
    with open(path, "r", encoding="utf-8") as f:
        md_content = f.read()
    init_state = {
        "chunks": json.loads(md_content),
        "file_title": "hak180产品安全手册",
    }
    node(init_state)
