from pymilvus import AnnSearchRequest, MilvusClient, WeightedRanker

from atguigu.config.congif import LoadMilvus

milvus_client = None


def get_milvus_client():
    global milvus_client
    if not milvus_client:
        milvus_client = MilvusClient(uri=LoadMilvus.milvus_uri)
    return milvus_client


def creat_hybrid_reqs(
    dense_data,
    sparse_data,
    dense_anns_field,
    sparse_anns_field,
    dense_param=None,
    sparse_parm=None,
    limit=10,
    expr=None,
):
    if not dense_param:
        dense_param = {"metric_type": "COSINE"}
    if not sparse_parm:
        sparse_parm = {"metric_type": "IP"}
    dense_req = AnnSearchRequest(
        data=[dense_data],
        anns_field=dense_anns_field,
        param=dense_param,
        limit=limit,
        expr=expr,
    )
    sparse_req = AnnSearchRequest(
        data=[sparse_data],
        anns_field=sparse_anns_field,
        param=sparse_parm,
        limit=limit,
        expr=expr,
    )
    return [dense_req, sparse_req]


def hybrid_search(
    collection_name, reqs, limit=10, output_fields=None, ranker=(0.5, 0.5)
):
    milvus_client = get_milvus_client()
    weighted_ranker = WeightedRanker(*ranker)
    res = milvus_client.hybrid_search(
        collection_name=collection_name,
        reqs=reqs,
        ranker=weighted_ranker,
        limit=limit,
        output_fields=output_fields,
    )
    return res
