# atguigu/query_process/nodes/node_search_embedding.py
import json

from atguigu.config.congif import LoadMilvus
from atguigu.query_process.base import NodeBase
from atguigu.query_process.state import QueryGraphState
from atguigu.tool.get_bgem3 import get_embedding
from atguigu.tool.milvus_client import creat_hybrid_reqs, hybrid_search


class NodeSearchEmbedding(NodeBase):
    """
    节点功能：基于已确认主体名+改写后的用户问题，执行Milvus向量数据库混合检索
    """

    # 覆盖基类的 name 属性，标识节点名称
    name: str = "node_search_embedding"

    def process(self, state: QueryGraphState):
        rewritten_query, item_names = (
            state.get("rewritten_query"),
            state.get("item_names"),
        )
        embedding = get_embedding([rewritten_query])
        dense_list = embedding["dense"][0]
        print(dense_list)
        sparse_dict_list = embedding["sparse"][0]
        expr = f"item_name in {json.dumps(item_names)}"
        reqs = creat_hybrid_reqs(
            dense_list,
            sparse_dict_list,
            "dense_vector",
            "sparse_vector",
            expr=expr,
            dense_param={"metric_type": "L2"},
        )
        search = hybrid_search(
            LoadMilvus.chunks_collection,
            reqs,
            output_fields=["id", "title", "file_title", "md_content", "item_name"],
            ranker=(0.8, 0.2),
        )
        temp_list = [
            {**i["entity"], "source": "local", "score": i.distance} for i in search[0]
        ]
        print(temp_list)
        return {"embedding_chunks": temp_list}


if __name__ == "__main__":
    init_state = {
        "rewritten_query": "关于HAK180烫金机如何使用",
        "item_names": ["HAK180烫金机"],
    }
    node_search_embedding = NodeSearchEmbedding()
    result = node_search_embedding(init_state)
