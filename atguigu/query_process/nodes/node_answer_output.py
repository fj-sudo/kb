# atguigu/query_process/nodes/node_answer_output.py
import re

from langchain.chat_models import init_chat_model

from atguigu.config.congif import LoadLLM
from atguigu.config.prompt import ANSWER_PROMPT
from atguigu.query_process.base import NodeBase
from atguigu.query_process.state import QueryGraphState
from atguigu.tool.mongon_tool import add_or_update_history
from atguigu.tool.task_utils import put_q


class NodeAnswerOutput(NodeBase):
    """
    节点功能: 答案生成
    """

    # 覆盖基类的 name 属性，标识节点名称
    name: str = "node_answer_output"

    def process(self, state: QueryGraphState):
        reranked_docs = state.get("reranked_docs")
        rewritten_query = state.get("rewritten_query")
        item_names = state.get("item_names")
        session_id = state.get("session_id")
        history_list = state.get("history")
        answer = state.get("answer") or ""
        task_id = state.get("task_id")
        if answer:
            put_q(task_id, "final", {"answer": answer})
        else:
            # 代表之前做意图识别的时候，没有生成答案,有确定的商品名字，进行三路检索 rrf  rerank
            #     根据rerank完成后获得的chunks 准备提交给大模型，让大模型生成答案
            #   todo一、整理提示词
            context = ""
            for idx, item in enumerate(reranked_docs, start=1):
                title = item.get("title")
                content = item.get("content")
                url = item.get("url")
                source = item.get("source")
                score = item.get("score")
                context += f"第{idx}个文档：标题:{title}, 内容: {content}, 来源: {source}, 得分: {score},地址: {url}\n"
            print(context)
            history = ""
            for item in history_list:
                role = item.get("role")
                text = item.get("text")
                history += f"{role}: {text}\n"

            item_names = ",".join(item_names)
            question = rewritten_query
            prompt = ANSWER_PROMPT.format(
                item_names=item_names,
                question=question,
                context=context,
                history=history,
            )
            if len(prompt) >= 12000:
                prompt = prompt[:12000]
            llm = init_chat_model(
                f"openai:{LoadLLM.llm_default_model}",
                base_url=LoadLLM.openai_api_base,
                api_key=LoadLLM.openai_api_key,
                temperature=float(LoadLLM.llm_default_temperature),
            )
            messages = [
                {"role": "user", "content": prompt},
            ]

            res = llm.stream(messages)

            for i in res:
                put_q(task_id, "delta", {"delta": i.content})
                answer += i.content
                print(answer)
            seen = set()  # 用于去重，避免同一张图片重复出现
            md_img_pattern = re.compile(r"!\[.*?\]\((.*?)\)")
            for doc in reranked_docs:
                # 检查 text 字段中的 Markdown 图片 (主要针对 Local Chunk)
                text = doc.get("content")
                matches = md_img_pattern.findall(text)
                for img_url in matches:
                    img_url = img_url.strip()
                    seen.add(img_url)
            image_urls = list(seen)

            # 这里拿到图片做最后一次推送，前端就关闭sse
            put_q(task_id, "final", {"image_urls": image_urls})

            #   todo 四、答案输出完成，需要保存历史记录
            if answer:
                add_or_update_history(
                    session_id,
                    "assistant",
                    answer,
                    rewritten_query=rewritten_query,
                    item_names=item_names,
                )

        return {
            "answer": answer,
        }
