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
    dense = [i.tolist() for i in embedding["dense"]]
    sparse = [
        dict(zip(i.indices.tolist(), i.data.tolist())) for i in embedding["sparse"]
    ]
    return {"dense": dense, "sparse": sparse}


print(get_embedding(["hello"]))
