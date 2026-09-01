from pymilvus import MilvusClient

from atguigu.config.congif import LoadMilvus

milvus_client = None


def get_milvus_client():
    global milvus_client
    if not milvus_client:
        milvus_client = MilvusClient(uri=LoadMilvus.milvus_uri)
    return milvus_client
