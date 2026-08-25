import json


def json_format(obj):
    return json.dumps(obj,ensure_ascii=False,indent=4)