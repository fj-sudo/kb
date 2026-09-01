import os

from dotenv import load_dotenv

load_dotenv(override=True)


class LoadEnvMineru:
    api_key = os.getenv("MINERU_TOKEN")


class LoadLLM:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_api_base = os.getenv("OPENAI_API_BASE")
    llm_default_model = os.getenv("LLM_DEFAULT_MODEL")
    llm_default_temperature = os.getenv("LLM_DEFAULT_TEMPERATURE")
    vl_model = os.getenv("VL_MODEL")
    item_model = os.getenv("ITEM_MODEL")


class LoadMinio:
    minio_endpoint = os.getenv("MINIO_ENDPOINT")
    minio_access_key = os.getenv("MINIO_ACCESS_KEY")
    minio_secret_key = os.getenv("MINIO_SECRET_KEY")
    minio_bucket_name = os.getenv("MINIO_BUCKET_NAME")
    minio_img_dir = os.getenv("MINIO_IMG_DIR")


class LoadBgem3:
    bge_m3_patH = os.getenv("BGE_M3_PATH")
    bge_m3 = os.getenv("BGE_M3")
    bge_device = os.getenv("BGE_DEVICE")
    bge_fp16 = True if os.getenv("BGE_FP16") in ("True", "true", "1") else False


class LoadMilvus:
    milvus_uri = os.getenv("MILVUS_URI")
    chunks_collection = os.getenv("CHUNKS_COLLECTION")
    item_name_collection = os.getenv("ITEM_NAME_COLLECTION")
