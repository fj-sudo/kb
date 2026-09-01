# atguigu/import_process/nodes/node_item_name_recognition.py
import json

from langchain.chat_models import init_chat_model
from pymilvus import DataType

from atguigu.config.congif import LoadLLM, LoadMilvus
from atguigu.config.prompt import (
    ITEM_NAME_SYSTEM_PROMPT,
    ITEM_NAME_USER_PROMPT_TEMPLATE,
)
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.get_bgem3 import get_embedding
from atguigu.tool.json_format import json_format
from atguigu.tool.milvus_client import get_milvus_client


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
        chunks_list1 = chunks_list[:20]
        chunks = "\n"
        for idx, chunk in enumerate(chunks_list1, start=1):
            md_content = chunk.get("md_content")
            title = chunk.get("title")
            chunk_str = f"[切片{idx}]\n{title}\n{file_title}\n{md_content}\n"
            chunks += chunk_str
            if len(chunks) > 10000:
                break
        chunks_str = chunks[:10000]
        llm = init_chat_model(
            f"openai:{LoadLLM.vl_model}",
            base_url=LoadLLM.openai_api_base,
            api_key=LoadLLM.openai_api_key,
            temperature=float(LoadLLM.llm_default_temperature),
        )
        message = [
            ("system", ITEM_NAME_SYSTEM_PROMPT),
            (
                "user",
                ITEM_NAME_USER_PROMPT_TEMPLATE.format(
                    file_title=file_title, context=chunks_str
                ),
            ),
        ]
        res = llm.invoke(message)
        item_name = res.content.replace("\n", "").replace("\t", "").replace(" ", "")
        if not item_name:
            item_name = file_title
        milvus_client = get_milvus_client()
        schema = milvus_client.create_schema(auto_id=True)
        (
            schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
            .add_field(
                field_name="item_name", datatype=DataType.VARCHAR, max_length=500
            )
            .add_field(
                field_name="file_title", datatype=DataType.VARCHAR, max_length=500
            )
            .add_field(
                field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=1024
            )
            .add_field(
                field_name="sparse_vector", datatype=DataType.SPARSE_FLOAT_VECTOR
            )
        )
        index_params = milvus_client.prepare_index_params()
        index_params.add_index(
            field_name="dense_vector",
            index_name="dense_vector_index",
            index_type="IVF_FLAT",
            metric_type="COSINE",
            params={"nlist": 128, "nprobe": 10},
        )
        index_params.add_index(
            field_name="sparse_vector",
            index_name="sparse_vector_index",
            index_type="SPARSE_INVERTED_INDEX",  # 优化的暴力搜索
            metric_type="IP",  # 计算稀疏向量的相似度算法（为了计算值）
            params={
                "inverted_index_algo": "DAAT_MAXSCORE",
                # 高效的稀疏检索算法
                "normalize": True,
                # ↑ L2 归一化，让内积 (IP) 等价于余弦相似度
                "quantization": "none",
            },
        )

        collection_name = LoadMilvus.item_name_collection
        milvus_client.create_collection(
            schema=schema,
            collection_name=collection_name,
            index_params=index_params,
        )
        embedding = get_embedding([item_name])
        dense = embedding.get("dense")[0]
        sparse = embedding.get("sparse")[0]
        data = {
            "item_name": item_name,
            "file_title": file_title,
            "dense_vector": dense,
            "sparse_vector": sparse,
        }
        milvus_client.load_collection(collection_name)
        item_name2 = item_name.replace("\\", "\\\\").replace("'", "'").replace('"', '"')
        fil = f"item_name=='{item_name2}'"
        milvus_client.delete(collection_name, filter=fil)
        milvus_client.insert(collection_name=collection_name, data=data)
        for chunk in chunks_list:
            chunk["item_name"] = item_name
        with open(
            r"D:\Software\SGG\资料\视频分发\掌柜智库01\资料\05-设备手册汇总\doc\hak180产品安全手册\chunks_item_name.json",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(json_format(chunks_list))
        return {
            "chunks": chunks_list,
            "item_name": item_name,
        }


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
