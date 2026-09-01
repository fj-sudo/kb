from datetime import datetime

from pymongo import MongoClient

from atguigu.config.congif import MongoConfig

# client = MongoClient('mongodb://user:password@localhost:27017/mydatabase?authSource=admin')
# db = client['mydatabase']
mongo_client = None


def get_mongo_client():
    global mongo_client
    if not mongo_client:
        # 替换为你的MongoDB连接字符串
        mongo_client = MongoClient(MongoConfig.mongo_url)
    return mongo_client


def get_mongo_tool():
    mongo_client = get_mongo_client()
    # 创建获取数据库
    db = mongo_client[MongoConfig.mongo_db_name]  # 获取数据库
    collection = db["chat_history"]  # 获取数据库当中的表 （自动创建）
    collection.create_index([("_id", 1), ("session_id", 1), ("ts", -1)])
    return collection


# 封装mongodb 增删改查的函数工具
# clear_history清空某个session_id的所有消息
def clear_history(session_id):
    collection = get_mongo_tool()
    collection.delete_many({"session_id": session_id})


# get_recent_messages 根据session_id获取最近的n条消息
def get_recent_messages(session_id, n):
    collection = get_mongo_tool()
    res = collection.find({"session_id": session_id}).sort("ts", -1).limit(n)
    #     cursor对象 游标
    return list(res)  # 转成列表
    # return res


# add_or_update_history保存历史记录（根据id决定是添加还是修改）


def add_or_update_history(
    session_id, role, text, rewritten_query=None, item_names=None, ts=None, id=None
):
    collection = get_mongo_tool()
    if id:
        # 修改逻辑 修改的时候数据（传递过来的参数）一定有id了
        res = collection.update_one(
            {"_id": id},
            {
                "$set": {
                    "session_id": session_id,
                    "role": role,
                    "text": text,
                    "rewritten_query": rewritten_query,
                    "item_names": item_names,
                    "ts": ts or datetime.now(),
                }
            },
        )
        return res
    else:
        # 添加逻辑 添加的时候数据（传递过来的参数）是没有id的
        res = collection.insert_one(
            {
                "session_id": session_id,
                "role": role,
                "text": text,
                "rewritten_query": rewritten_query,
                "item_names": item_names,
                "ts": ts or datetime.now(),
            }
        )
        return res.inserted_id


if __name__ == "__main__":
    # res = get_recent_messages(session_id="123",n=5)
    # print(res)
    # {
    #     _id: ObjectId('6a96996ad740357eec32b092'),
    #     session_id: 'test111',
    #     role: 'user',
    #     text: '哈哈',
    #     rewritten_query: null,
    #     item_names: null,
    #     ts: ISODate('2026-09-01T17:22:50.995Z')
    # }
    res = add_or_update_history("test111", "user", "gaga")
    print(res, type(res))
    #
    print(get_recent_messages("test111", 6))
    print(
        add_or_update_history("test111", "user", "gaga", id="a96c2f301903dac88914319")
    )
    clear_history("test111")