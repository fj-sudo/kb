# atguigu/import_process/nodes/node_import_milvus.py
import json

from pymilvus import DataType

from atguigu.config.congif import LoadMilvus
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.milvus_client import get_milvus_client


class NodeImportMilvus(NodeBase):
    """
    导入向量库节点：数据持久化
    """

    name = "node_import_milvus"

    def process(self, state: ImportGraphState):
        chunk_list = state.get("chunks")
        if not chunk_list:
            raise Exception("内容为空")
        milvus_client = get_milvus_client()
        collection_name = LoadMilvus.chunks_collection
        if not milvus_client.has_collection(collection_name):
            schema = milvus_client.create_schema(auto_id=True)
            schema.add_field(
                field_name="id", datatype=DataType.INT64, is_primary=True
            ).add_field(
                field_name="title", datatype=DataType.VARCHAR, max_length=500
            ).add_field(
                field_name="file_title", datatype=DataType.VARCHAR, max_length=500
            ).add_field(
                field_name="md_content", datatype=DataType.VARCHAR, max_length=5000
            ).add_field(
                field_name="item_name", datatype=DataType.VARCHAR, max_length=500
            ).add_field(field_name="part", datatype=DataType.INT64).add_field(
                field_name="dense_vector", datatype=DataType.FLOAT_VECTOR, dim=1024
            ).add_field(
                field_name="sparse_vector",
                datatype=DataType.SPARSE_FLOAT_VECTOR,
            )

            index_params = milvus_client.prepare_index_params()
            index_params.add_index(
                field_name="dense_vector",
                index_name="dense_vector_index",
                index_type="AUTOINDEX",
                metric_type="L2",
                # params={"nlist": 128,"nprobe": 10}, #使用AUTOINDEX时，不能设置nlist和nprobe
            )

            index_params.add_index(
                field_name="sparse_vector",
                index_name="sparse_vector_index",
                index_type="SPARSE_INVERTED_INDEX",
                metric_type="IP",
                params={
                    "inverted_index_algo": "DAAT_MAXSCORE",
                    # 高效的稀疏检索算法
                    "normalize": True,
                    # ↑ L2 归一化，让内积 (IP) 等价于余弦相似度
                    "quantization": "none",
                    # ↑ 关闭量化，保持原始精度：模型生成的向量已经压缩的一半的精度了（BGE_FP16=1），这里就不再压缩了
                    # "quantization": "none" → 存储原始向量，不压缩
                    # "quantization": "sq8" → 存储压缩后的向量（8-bit 量化
                },
            )

            milvus_client.create_collection(
                collection_name=collection_name,
                schema=schema,
                index_params=index_params,
            )
        file_title = chunk_list[0]["file_title"]
        milvus_client.load_collection(collection_name=collection_name)
        file_title = (
            file_title.replace("\\", "\\\\").replace("'", "'").replace('"', '"')
        )
        filter = f"file_title == '{file_title}'"
        milvus_client.delete(collection_name=collection_name, filter=filter)
        # 准备数据插入数据就是chunks
        res = milvus_client.insert(collection_name=collection_name, data=chunk_list)
        # 把插入数据，数据库给自增的id,回填到对应chunk,目的仅仅是为了state当中存储的chunks更完善，后期检索其实用不到
        ids = res.get("ids")
        for i, chunk in enumerate(chunk_list):
            chunk["id"] = ids[i]
        return {
            "chunks": chunk_list,
        }


if __name__ == "__main__":
    node = NodeImportMilvus()
    path = r"D:\Software\SGG\资料\视频分发\掌柜智库01\资料\05-设备手册汇总\doc\hak180产品安全手册\chunks_embeding.json"
    with open(path, "r", encoding="utf-8") as f:
        md_content = f.read()
    init_state = {
        "chunks": json.loads(md_content),
        "file_title": "hak180产品安全手册",
    }
    node(init_state)
