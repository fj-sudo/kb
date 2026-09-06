from http import HTTPStatus

import dashscope

from atguigu.config.congif import LoadRerank

# 以下为华北2（北京）地域的配置，调用时请将{WorkspaceId}替换为真实的业务空间ID，各地域的配置不同。
dashscope.base_http_api_url = LoadRerank.base_http_api_url
dashscope.api_key = LoadRerank.api_key


def text_rerank(rewritten_query: str, text: list[str], top_n=10):
    resp = dashscope.TextReRank.call(
        model="qwen3.7-text-rerank",
        query=rewritten_query,
        documents=text,
        top_n=top_n,
        instruct="Given a web search query, retrieve relevant passages that answer the query.",
    )
    if resp.status_code == HTTPStatus.OK:
        resp = [
            {"idx": i["index"], "score": i["relevance_score"]}
            for i in resp.output["results"]
        ]
        return resp
    else:
        raise Exception("Rerank服务连接失败")


if __name__ == "__main__":
    text_rerank("hello", ["你好", "你不好"])
