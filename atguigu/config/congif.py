import os

from dotenv import load_dotenv

load_dotenv(override=True)


class LoadEnvMineru:
    api_key = os.getenv("MINERU_TOKEN")
