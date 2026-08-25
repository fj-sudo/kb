from langgraph.constants import END
from langgraph.graph import StateGraph

from atguigu.import_process.nodes.node_bge_embedding import NodeBGEEmbedding
from atguigu.import_process.nodes.node_document_split import NodeDocumentSplit
from atguigu.import_process.nodes.node_entry import NodeEntry
from atguigu.import_process.nodes.node_import_milvus import NodeImportMilvus
from atguigu.import_process.nodes.node_item_name_recognition import (
    NodeItemNameRecognition,
)
from atguigu.import_process.nodes.node_md_img import NodeMDImg
from atguigu.import_process.nodes.node_pdf_to_md import NodePDFToMD
from atguigu.import_process.state import ImportGraphState


class MainGraph:
    def __init__(self):
        self.state_graph = StateGraph(state_schema=ImportGraphState)
        self.add_node()
        self.add_edge()
        self.graph = None

    def add_node(self):
        self.state_graph.add_node(NodeEntry.name, NodeEntry())
        self.state_graph.add_node(NodePDFToMD.name, NodePDFToMD())
        self.state_graph.add_node(NodeMDImg.name, NodeMDImg())
        self.state_graph.add_node(NodeDocumentSplit.name, NodeDocumentSplit())
        self.state_graph.add_node(
            NodeItemNameRecognition.name, NodeItemNameRecognition()
        )
        self.state_graph.add_node(NodeBGEEmbedding.name, NodeBGEEmbedding())
        self.state_graph.add_node(NodeImportMilvus.name, NodeImportMilvus())

    def add_edge(self):
        self.state_graph.set_entry_point(NodeEntry.name)
        self.state_graph.add_conditional_edges(NodeEntry.name, self.edge_route)

        self.state_graph.add_edge(NodePDFToMD.name,NodeMDImg.name)
        self.state_graph.add_edge(NodeMDImg.name, NodeDocumentSplit.name)
        self.state_graph.add_edge(NodeDocumentSplit.name, NodeItemNameRecognition.name)
        self.state_graph.add_edge(NodeItemNameRecognition.name, NodeBGEEmbedding.name)
        self.state_graph.add_edge(NodeBGEEmbedding.name, NodeImportMilvus.name)

    def edge_route(self, state: ImportGraphState):
        if state.get("is_md_read_enabled"):
            return NodeMDImg.name
        if state.get("is_pdf_read_enabled"):
            return NodePDFToMD.name
        return END

    def run(self, state: ImportGraphState):
        if not self.graph:
            graph = self.state_graph.compile()
        res = graph.invoke(state)
        return res

    @classmethod
    def create_run(cls, state: ImportGraphState):
        return cls().run(state)


if __name__ == "__main__":
    state1 = {"local_file_path": r"D:\Software\SGG\资料\视频分发\掌柜智库01\资料\05-设备手册汇总\doc\hak180产品安全手册.pdf"
              ,"local_dir": r"D:\Software\SGG\资料\视频分发\掌柜智库01\资料\05-设备手册汇总\doc"}
    print(MainGraph.create_run(state1))
