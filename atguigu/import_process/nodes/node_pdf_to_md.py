# atguigu/import_process/nodes/node_pdf_to_md.py
import shutil
import time
from pathlib import Path

from atguigu.config.congif import LoadEnvMineru
from atguigu.import_process.base import NodeBase
from atguigu.import_process.state import ImportGraphState
from atguigu.tool.logger import logger


class NodePDFToMD(NodeBase):
    """
    PDF 转 Markdown 节点：PDF结构化解析
    """

    name = "node_pdf_to_md"

    def process(self, state: ImportGraphState):
        local_dir = state.get("local_dir", "")
        pdf_path = state.get("pdf_path", "")
        if not local_dir:
            logger.error("目录为空")
            raise Exception("目录为空")
        dir_obj = Path(local_dir)
        if not dir_obj.exists():
            dir_obj.mkdir(parents=True, exist_ok=True)
        if not pdf_path:
            logger.error("文件路径为空")
            raise Exception("文件路径为空")
        pdf_path_obj = Path(pdf_path)
        if not pdf_path_obj.exists():
            logger.error("文件不存在")
            raise Exception("文件不存在")
        logger.info(f"{pdf_path_obj},{dir_obj}")
        import requests

        token = LoadEnvMineru.api_key
        url = "https://mineru.net/api/v4/file-urls/batch"
        header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        data = {
            "files": [{"name": f"{pdf_path_obj.name}", "data_id": "abcd"}],
            "model_version": "vlm",
        }
        file_path = [f"{pdf_path_obj}"]
        response = requests.post(url, headers=header, json=data)
        result = response.json()
        if response.status_code != 200:
            logger.error("请求失败")
            raise Exception("请求失败")
        if result["code"] != 0:
            logger.error("上传文件请求的数据失败")
            raise Exception("上传文件请求的数据失败")
        batch_id = result["data"]["batch_id"]
        urls = result["data"]["file_urls"]
        for i in range(len(urls)):
            with open(file_path[i], "rb") as f:
                res_upload = requests.put(urls[i], data=f)
                if res_upload.status_code == 200:
                    logger.info("请求成功")
                else:
                    logger.error("请求失败")
                    raise Exception("请求失败")

        import requests

        token = LoadEnvMineru.api_key
        batch_id = batch_id
        url = f"https://mineru.net/api/v4/extract-results/batch/{batch_id}"
        header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        max_time = 60
        current_time = 0
        star_time = 0
        end_time = 0
        while True:
            try:
                star_time = time.time()
                res = requests.get(url, headers=header)

                if res.status_code != 200:
                    logger.error("获取文件路径请求失败")
                    raise Exception("获取文件路径请求失败")
                res_json = res.json()
                if res_json["code"] != 0:
                    logger.error("获取文件路径请求的数据失败")
                    raise Exception("获取文件路径请求的数据失败")

                if res_json["data"]["extract_result"][0]["state"] != "done":
                    logger.error("获取文件路径请求的数据不正确")
                    raise Exception("获取文件路径请求的数据不正确")
                url = res_json["data"]["extract_result"][0]["full_zip_url"]
                break
            except:
                time.sleep(1)
                end_time = time.time()
                current_time += end_time - star_time
                if current_time > max_time:
                    logger.error("请求获取数据超时")
                    raise Exception("请求获取数据超时")
                continue
        import requests

        response = requests.get(url)
        if response.status_code != 200:
            logger.error("url下载请求失败")
            raise Exception("url下载请求失败")
        zip_obj = dir_obj / f"{pdf_path_obj.stem}.zip"
        with open(zip_obj, "wb") as z:
            z.write(response.content)
        logger.info("下载压缩包请求成功,保存到本地")

        import zipfile

        zip_file_obj = zipfile.ZipFile(zip_obj)
        unzip_file_path_obj = dir_obj / f"{pdf_path_obj.stem}"

        # 如果解压目录存在，就删除掉，再去重新建
        if unzip_file_path_obj.exists():
            shutil.rmtree(unzip_file_path_obj)
        unzip_file_path_obj.mkdir(parents=True, exist_ok=True)

        # 把内容解压到创建好的目录下
        zip_file_obj.extractall(unzip_file_path_obj)  # 解压到哪里

        # 把解压缩的md文件改名
        origin_md_path_obj = unzip_file_path_obj / "full.md"
        new_md_path_obj = origin_md_path_obj.with_name(f"{pdf_path_obj.stem}.md")
        # 修改名字，但是没落盘，在内存里面，返回一个新的Path对象
        origin_md_path_obj.rename(
            new_md_path_obj
        )  # 真正的改名落盘，把新的Path对象赋值给原来的

        with open(new_md_path_obj, "r", encoding="utf-8") as f:
            md_content = f.read()

        return {
            "md_path": str(new_md_path_obj),
            "md_content": md_content,
        }


if __name__ == "__main__":
    md = NodePDFToMD()
    print(
        md(
            {
                "local_dir": r"D:\Software\SGG\资料\视频分发\掌柜智库01\资料\05-设备手册汇总\doc",
                "pdf_path": r"D:\Software\SGG\资料\视频分发\掌柜智库01\资料\05-设备手册汇总\doc\hak180产品安全手册.pdf",
            }
        )
    )
