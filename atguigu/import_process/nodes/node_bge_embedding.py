# atguigu/import_process/nodes/node_bge_embedding.py
import json

from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.get_bgem3 import get_embedding


class NodeBGEEmbedding(NodeBase):
    """
    混合向量化节点：使用 BGE-M3 模型将文本转换为向量
    """

    name = "node_bge_embedding"

    def process(self, state: ImportGraphState):
        chunks_list = state.get("chunks")
        if not chunks_list:
            raise Exception("文件不能为空")

        for idx in range(0, len(chunks_list), 3):
            chunks_3_list = chunks_list[idx : idx + 3]
            md_content_3_list = [
                f"{chunk.get('item_name')}---{chunk.get('md_content')}"
                for chunk in chunks_3_list
            ]
            embedding_dict = get_embedding(md_content_3_list)
            for index, chunk in enumerate(chunks_3_list):
                chunk["dense_vector"] = embedding_dict["dense"][index]
                chunk["sparse_vector"] = embedding_dict["sparse"][index]

        return {"chunks": chunks_list}


if __name__ == "__main__":
    node = NodeBGEEmbedding()
    path = r"D:\Software\SGG\资料\视频分发\掌柜智库01\资料\05-设备手册汇总\doc\hak180产品安全手册\chunks_item_name.json"
    with open(path, "r", encoding="utf-8") as f:
        md_content = f.read()
    init_state = {
        "chunks": json.loads(md_content),
        "file_title": "hak180产品安全手册",
    }
    node(init_state)
