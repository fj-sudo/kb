# atguigu/query_process/nodes/node_search_embedding_hyde.py
import json

from langchain.chat_models import init_chat_model

from atguigu.config.congif import LoadLLM, LoadMilvus
from atguigu.config.prompt import HYDE_PROMPT
from atguigu.query_process.base import NodeBase
from atguigu.query_process.state import QueryGraphState
from atguigu.tool.get_bgem3 import get_embedding
from atguigu.tool.milvus_client import creat_hybrid_reqs, hybrid_search


class NodeSearchEmbeddingHyde(NodeBase):
    """
    节点功能：HyDE (Hypothetical Document Embedding)
    先让 LLM 生成假设性答案，再对答案进行向量检索，提高召回率。
    """

    # 覆盖基类的 name 属性，标识节点名称
    name: str = "node_search_embedding_hyde"

    def process(self, state: QueryGraphState):
        rewritten_query, item_names = (
            state.get("rewritten_query"),
            state.get("item_names"),
        )
        llm = init_chat_model(
            f"openai:{LoadLLM.llm_default_model}",
            base_url=LoadLLM.openai_api_base,
            api_key=LoadLLM.openai_api_key,
            temperature=LoadLLM.llm_default_temperature,
        )
        message = [("user", HYDE_PROMPT.format(rewritten_query=rewritten_query))]
        llm_res = llm.invoke(message).content

        embedding = get_embedding([llm_res])
        dense_list = embedding["dense"][0]
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
        return {"hyde_embedding_chunks": temp_list}


if __name__ == "__main__":
    init_state = {
        "rewritten_query": "关于HAK180烫金机如何使用",
        "item_names": ["HAK180烫金机"],
    }
    node_search_embedding_hyde = NodeSearchEmbeddingHyde()
    result = node_search_embedding_hyde(init_state)
