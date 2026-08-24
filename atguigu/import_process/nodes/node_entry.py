# atguigu/import_process/nodes/node_entry.py
from pathlib import Path

from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.logger import logger


class NodeEntry(NodeBase):
    """
    入口节点：任务分发
    """

    name = "node_entry"

    def process(self, state: ImportGraphState):
        file_path = state.get("local_file_path", "")
        if not file_path:
            logger.error("文件目录为空")
            raise Exception("文件目录为空")
        path_obj = Path(file_path)
        if not path_obj.exists():
            logger.error("文件不存在")
            raise Exception("文件不存在")
        suffix = path_obj.suffix
        tetel = path_obj.stem
        if suffix.lower() == ".md":
            return {
                "file_title": tetel,
                "md_path": file_path,
                "is_md_read_enabled": True,
            }
        if suffix.lower() == ".pdf":
            return {
                "file_title": tetel,
                "pdf_path": file_path,
                "is_pdf_read_enabled": True,
            }
        logger.error("文件类型不支持")
        raise Exception("文件类型不支持")


if __name__ == "__main__":
    node_entry = NodeEntry()
    state = {"local_file_path": r"D:\Software\SGG\test\hak180产品安全手册.md"}
    print(node_entry(state))
