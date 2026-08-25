import os

from dotenv import load_dotenv

load_dotenv(override=True)


class LoadEnvMineru:
    api_key = os.getenv("MINERU_TOKEN")
class LoadLLM:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
    LLM_DEFAULT_MODEL = os.getenv("LLM_DEFAULT_MODEL")
    LLM_DEFAULT_TEMPERATURE = os.getenv("LLM_DEFAULT_TEMPERATURE")
    VL_MODEL = os.getenv("VL_MODEL")
    ITEM_MODEL = os.getenv("ITEM_MODEL")