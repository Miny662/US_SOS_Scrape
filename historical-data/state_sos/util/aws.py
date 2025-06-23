import gzip
import logging
import os.path
from io import BytesIO
from typing import Any, Optional, List

import boto3
from botocore.exceptions import ClientError
from .config import CONFIG

DEFAULT_REGION = "us-east-1"


def create_client(aws_service_name: str, env="local") -> Any:
    """Create a boto3 client. Point it at motoserver if working locally"""
    if env != "local":
        return boto3.client(aws_service_name)
    return boto3.client(aws_service_name, endpoint_url=CONFIG.moto_url)


def create_bucket(bucket_name: str) -> bool:
    """Create an S3 bucket"""
    client = create_client("s3", env=CONFIG.pdp_env)
    try:
        client.create_bucket(Bucket=bucket_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def configure_local_s3() -> bool:
    if CONFIG.pdp_env != "local":
        logging.error(
            "Don't run configure_local_s3() in any environment other than 'local'"
        )
        return False
    try:
        create_bucket(CONFIG.pdp_source_bucket)
    except ClientError as e:
        logging.error(e)
        return False
    return True
