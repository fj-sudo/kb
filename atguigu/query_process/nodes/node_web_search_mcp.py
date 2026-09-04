# atguigu/query_process/nodes/node_web_search_mcp.py
import asyncio
import json

from agents.mcp import MCPServerStreamableHttp

from atguigu.config.congif import LoadMcp
from atguigu.query_process.base import NodeBase
from atguigu.query_process.state import QueryGraphState


class NodeWebSearchMcp(NodeBase):
    """
    节点功能，调用外部搜索引擎补充信息
    """

    # 覆盖基类的 name 属性，标识节点名称
    name: str = "node_web_search_mcp"

    def process(self, state: QueryGraphState):
        rewritten_query, item_names = (
            state.get("rewritten_query"),
            state.get("item_names"),
        )
        result = asyncio.run(self.main(rewritten_query))
        res = json.loads(result.content[0].text)["pages"]
        chunks = [
            {
                "content": item.get("snippet"),
                "title": item.get("title"),
                "url": item.get("url"),
                "source": "web",
            }
            for item in res
        ]
        return {"web_search_docs": chunks}

    async def main(self, rewritten_query) -> None:
        token = LoadMcp.api_key
        async with MCPServerStreamableHttp(
            name="Streamable HTTP Python Server",
            params={
                "url": LoadMcp.mcp_base_url,
                "headers": {"Authorization": f"Bearer {token}"},
                "timeout": 10,
            },
            cache_tools_list=True,
            max_retry_attempts=3,
        ) as server:
            res = await server.call_tool(
                "bailian_web_search", {"query": rewritten_query, "count": 10}
            )
            return res


if __name__ == "__main__":
    init_state = {
        "rewritten_query": "关于HAK180烫金机如何使用",
        "item_names": ["HAK180烫金机"],
    }
    node_search_embedding_hyde = NodeWebSearchMcp()
    result = node_search_embedding_hyde(init_state)
