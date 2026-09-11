# atguigu/query_process/nodes/node_item_name_confirm.py
import json

from langchain.chat_models import init_chat_model

from atguigu.config.congif import LoadLLM, LoadMilvus
from atguigu.config.prompt import (
    ITEM_NAME_EXTRACT_SYSTEM_PROMPT,
    ITEM_NAME_EXTRACT_TEMPLATE,
)
from atguigu.query_process.base import NodeBase
from atguigu.query_process.state import QueryGraphState
from atguigu.tool.get_bgem3 import get_embedding
from atguigu.tool.json_format import json_format
from atguigu.tool.logger import logger
from atguigu.tool.milvus_client import creat_hybrid_reqs, hybrid_search
from atguigu.tool.mongon_tool import (
    add_or_update_history,
    get_recent_messages,
    update_history_item_names_and_query,
)


class NodeItemNameConfirm(NodeBase):
    """
    节点功能：确认用户问题中的核心商品名称。
    """

    # 覆盖基类的 name 属性，标识节点名称
    name: str = "node_item_name_confirm"

    def process(self, state: QueryGraphState):
        session_id = state.get("session_id")
        original_query = state.get("original_query")
        if not session_id:
            raise Exception("session_id不能为空")
        if not original_query:
            raise Exception("original_query不能为空")
        # 先存当前提问，再取最近10条
        messages_10 = get_recent_messages(session_id)
        message_id = add_or_update_history(session_id, "user", original_query)
        # 组装最近10条提问
        messages_10_str = ""
        for i in messages_10:
            text = i.get("text")
            role = i.get("role")
            messages_10_str += f"{role}-{text}\n"
        llm = init_chat_model(
            f"openai:{LoadLLM.llm_default_model}",
            base_url=LoadLLM.openai_api_base,
            api_key=LoadLLM.openai_api_key,
            temperature=LoadLLM.llm_default_temperature,
        )
        messages = [
            (
                "system",
                ITEM_NAME_EXTRACT_SYSTEM_PROMPT,
            ),
            (
                "user",
                ITEM_NAME_EXTRACT_TEMPLATE.format(
                    history_text=messages_10_str, original_query=original_query
                ),
            ),
        ]
        print(messages_10_str)
        llm_res = llm.invoke(messages).content
        if llm_res.startswith("```json") or llm_res.startswith("~~~json"):
            llm_res = (
                llm_res.replace("```json", "")
                .replace("~~~json", "")
                .replace("```", "")
                .replace("~~~", "")
            )
        print(llm_res)
        try:
            llm_data_dict = json.loads(llm_res)
            item_names = llm_data_dict["item_names"]

            rewritten_query = llm_data_dict["rewritten_query"]
        except:
            item_names = []
            rewritten_query = original_query
        query_list = []
        item_names1_list = [
            i.replace("\n", "").replace("\t", "").replace(" ", "") for i in item_names
        ]
        for data in item_names1_list:
            embeddings = get_embedding([data])
            dense = embeddings.get("dense")[0]
            sparse = embeddings.get("sparse")[0]
            reqs = creat_hybrid_reqs(dense, sparse, "dense_vector", "sparse_vector")
            search = hybrid_search(
                LoadMilvus.item_name_collection,
                reqs,
                output_fields=["item_name"],
                ranker=(0.7, 0.3),
            )
            for dict1 in search[0]:
                query_list.append(
                    {
                        "score": dict1["distance"],
                        "search_item_name": dict1["entity"]["item_name"],
                        "original_item_name": data,
                    }
                )
        real_item_names = []
        may_item_names = []
        for i in query_list:
            search_item_name = i["search_item_name"]
            if i["score"] > 0.8:
                real_item_names.append(search_item_name)
            elif 0.8 > i["score"] > 0.6:
                may_item_names.append(search_item_name)
        if real_item_names:
            answer = None
        elif may_item_names:
            answer = (
                f"您提问的商品名称是下面哪一个，请确认一下{','.join(may_item_names)}"
            )
        else:
            answer = "没有找到相关的商品信息，请重新提问"
        if answer:
            message_id = add_or_update_history(session_id, "assistant", answer)
        history_list = get_recent_messages(session_id)
        ids = [item.get("_id") for item in history_list]
        update_history_item_names_and_query(ids, real_item_names, rewritten_query)
        return {
            "session_id": session_id,
            "original_query": original_query,
            "item_names": real_item_names,
            "answer": answer,
            "message_id": message_id,
            "rewritten_query": rewritten_query,
            "history": get_recent_messages(session_id),
        }


if __name__ == "__main__":
    # 模拟会话历史
    session_id = "test_001"
    # add_or_update_history(session_id, "user", "咨询下烫金机。")
    # add_or_update_history(session_id, "assistant", "您好。请问是哪个型号")
    # add_or_update_history(session_id, "user", "hak180")
    # add_or_update_history(session_id, "assistant", "具体有什么问题呢？")

    # 初始化图状态
    init_state = {"session_id": "test_001", "original_query": "咋用？"}

    # 创建节点对象
    node_item_name_confirm = NodeItemNameConfirm()
    # 执行节点的单元测试
    result = node_item_name_confirm(init_state)
    # 将返回的图状态进行json序列化
    logger.info(json_format(str(result)))
