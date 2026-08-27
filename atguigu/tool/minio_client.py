import json

from minio import Minio

from atguigu.config.congif import LoadMinio
from atguigu.tool.logger import logger

minio_client: Minio | None = None


def get_minio_client():
    try:
        global minio_client
        if not minio_client:
            buck_name = LoadMinio.minio_bucket_name
            minio_client = Minio(
                endpoint=LoadMinio.minio_endpoint,
                access_key=LoadMinio.minio_access_key,
                secret_key=LoadMinio.minio_secret_key,
                secure=False,
            )
            if not minio_client.bucket_exists(buck_name):
                minio_client.make_bucket(bucket_name=buck_name)
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                        "Resource": f"arn:aws:s3:::{buck_name}",
                    },
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{buck_name}/*",
                    },
                ],
            }
            minio_client.set_bucket_policy(
                bucket_name=buck_name, policy=json.dumps(policy)
            )
        return minio_client
    except:
        logger.error("minio客户端创建失败")
        raise
