from kb.import_process import ImportGraphState
from abc import ABC, abstractmethod

from kb.tool.logger import logger


# 规定 接口 让所有的子类必须重写process  不能实例化
# 抽离所有节点类的公共部分
class NodeBase(ABC):
    name = (
        "node_base"  # 后期拿所有节点名称，如果某个节点没写名称，默认拿到的就是node_base
    )

    def __init__(self):
        if self.name == "node_base":
            logger.error(
                f"{self.__class__.__name__}类没有设置name属性，请在子类中重写该属性"
            )
            raise Exception(
                f"{self.__class__.__name__}类没有设置name属性，请在子类中重写该属性"
            )

    def __call__(self, state: ImportGraphState):
        # 统一的打印日志，统一的处理异常
        try:
            logger.info(f"开始执行节点")
            self.process(state)
            logger.info(f"结束执行节点")
        except Exception as e:
            logger.error(f"执行节点{self.name}时发生异常")
            raise e

    @abstractmethod
    def process(self, state: ImportGraphState):
        pass


