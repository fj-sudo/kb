from pymilvus.model.hybrid import BGEM3EmbeddingFunction

from atguigu.config.congif import LoadBgem3

bgem3 = None


def get_bgem3():
    global bgem3
    if not bgem3:
        bgem3 = BGEM3EmbeddingFunction(
            model_name=LoadBgem3.bge_m3_patH,
            batch_size=LoadBgem3.bge_fp16,
            devices=LoadBgem3.bge_device,
        )
    return bgem3


def get_embedding(data_list):
    bgem = get_bgem3()
    embedding = bgem.encode_documents(data_list)
    dense = embedding["dense"][0]  # np.ndarray, shape=(1024,)
    sparse = embedding["sparse"][[0]].tocoo()  # 取第0行转coo
    sparse_dict = dict(zip(sparse.col.tolist(), sparse.data.tolist()))
    print(dense)
    print(sparse_dict)


get_embedding(["hello"])
