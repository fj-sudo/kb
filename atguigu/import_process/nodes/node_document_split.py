# atguigu/import_process/nodes/node_document_split.py
import re
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.json_format import json_format


class NodeDocumentSplit(NodeBase):
    """
    文档切分节点：智能文档切片
    """

    name = "node_document_split"

    def process(self, state: ImportGraphState):

        # 1获取数据校验
        md_path = state.get("md_path")
        file_title = state.get("file_title")
        md_path_obj = Path(md_path)
        if not md_path:
            raise Exception("文件路径空")
        if not md_path_obj.exists():
            raise Exception("文件不存在")
        if not file_title:
            raise Exception("文件标题为空")
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        # 2粗切：取上一个标题到现标题的内容,列表字典
        # 2.1 md_content将\r\n转换为\n,\r转换为\n(系统换行不一致)
        md_content = md_content.replace("\r\n", "\r").replace("\r", "\n")
        md_line_content_list = md_content.split("\n")

        # 2.2 通过标题切分，###。找到标题部分，代码块中有###所以找出代码块并跳过，
        code_pattern = r"^(`{3,}|~{3,})"  # ()代表分组捕获，捕获匹配到的原文内容，一个正则可以是9个，后期我们要拿哪个分组的内容，就用
        title_pattern = r"^\s*#{1,6}\s+.+"
        in_code_chunk = False
        temp = None
        current_idx = 0
        first_chunk_dict_list = []
        for idx, md_line in enumerate(md_line_content_list):
            # 代码块校验
            match = re.match(code_pattern, md_line)
            if match:
                # 进入代码块
                if not in_code_chunk:
                    in_code_chunk = True
                    temp = match.group(1)
                # 退出代码块
                elif in_code_chunk and temp == match.group(1):
                    in_code_chunk = False
                    temp = None
            # 不是代码块， 找到标题后通过列表切片。
            # 匹配标题
            if re.match(title_pattern, md_line) and not in_code_chunk:
                if not md_line_content_list[current_idx:idx]:
                    continue
                chunk = md_line_content_list[current_idx:idx]
                # 2.3转换成字符串，切完如果第一个不是###就加个默认标题，
                md_str_chunk = "\n".join(chunk)
                current_idx = idx
                # 2.4最后存字典title，md，file_title。最后一位要单独存。
                first_chunk_dict_list.append(
                    {
                        "title": "无标题" if not chunk[0].startswith("#") else chunk[0],
                        "file_title": file_title,
                        "md_content": md_str_chunk,
                    }
                )
        first_chunk_dict_list.append(
            {
                "title": md_line_content_list[current_idx]
                if md_line_content_list[current_idx].startswith("#")
                else "无标题",
                "file_title": file_title,
                "md_content": "\n".join(md_line_content_list[current_idx:]),
            }
        )
        # 3细切：用字符串文本切分器对内容长度大于300的进行切分，列表字典
        # 小于300，内容中有<table跳过。
        second_chunk_dick_list = []
        # 一个个取出符合条件的进行长切
        separators = ["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", " "]
        splitter = RecursiveCharacterTextSplitter(
            separators,
            chunk_size=300,
            chunk_overlap=20,
        )
        for first_chunk_dict in first_chunk_dict_list:
            # 不符合条件：1字数小于300，2包含列表的块
            title = first_chunk_dict.get("title")
            title_len = len(first_chunk_dict.get("title")) + 2
            md_content = first_chunk_dict.get("md_content")
            md_content_new = md_content[title_len:] if title != "无标题" else md_content
            if len(md_content_new) <= 300:
                second_chunk_dick_list.append({**first_chunk_dict, "part": 0})
                continue
            if "<table" in md_content_new:
                second_chunk_dick_list.append({**first_chunk_dict, "part": 0})
                continue
            # 符合条件切分
            md_chunk_content_list = splitter.split_text(md_content_new)
            for idx, md_chunk_content in enumerate(md_chunk_content_list):
                second_chunk_dick_list.append(
                    {
                        **first_chunk_dict,
                        "part": idx + 1,
                        "md_content": title + "\n\n" + md_chunk_content,
                    }
                )
        with open(
            r"D:\Software\SGG\资料\视频分发\掌柜"
            r"智库01\资料\05-设备手册汇总\doc\hak180产品安全手册\chunks.json",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(json_format(second_chunk_dick_list))
        return {"chunks": second_chunk_dick_list}

        # 传入切分器切分存part,md_content
        # 4 存一份json类型文件


if __name__ == "__main__":
    node = NodeDocumentSplit()
    init_state = {  # pyright: ignore[reportArgumentType]
        "md_path": r"D:\Software\SGG\资料\视频分发\掌柜智库01\资料\05-设备手册汇总\doc"
        r"\hak180产品安全手册\hak180产品安全手册_new.md",
        "file_title": "hak180产品安全手册",
    }
    node(init_state)
    # print(node(init_state))
    # result = node(init_state)
    # logger.info(json_format(result))
