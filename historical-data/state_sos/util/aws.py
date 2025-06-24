import gzip
import json
import logging
from io import BytesIO
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError
from state_sos.util.config import CONFIG

DEFAULT_REGION = "us-east-1"


def create_client(aws_service_name: str, env=CONFIG.sos_scraper_environment) -> Any:
    """Create a boto3 client. Point it at motoserver if working locally"""
    if env != "local":
        return boto3.client(aws_service_name)
    return boto3.client(aws_service_name, endpoint_url=CONFIG.moto_url)


def create_bucket(bucket_name: str) -> bool:
    """Create an S3 bucket"""
    client = create_client("s3", env=CONFIG.sos_scraper_environment)
    try:
        client.create_bucket(Bucket=bucket_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def configure_local_s3() -> bool:
    if CONFIG.sos_scraper_environment != "local":
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


def write_file_to_s3(bucket: str, key: str, data: Dict, compress: bool = True) -> bool:
    """Write a list of data objects to a new file in S3"""
    client = create_client("s3", env=CONFIG.sos_scraper_environment)
    file_data = json.dumps(data).encode('utf-8')
    if compress:
        file_data = gzip.compress(file_data)
        key = f"{key}.gz"
        client.upload_fileobj(Fileobj=BytesIO(file_data), Bucket=bucket, Key=key)
    try:
        client.put_object(Body=file_data, Bucket=bucket, Key=key)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def read_file_from_s3(bucket: str, key: str) -> Dict:
    client = create_client("s3", env=CONFIG.sos_scraper_environment)
    obj = client.get_object(Bucket=bucket, Key=key)
    data_string = gzip.decompress(obj["Body"].read()).decode("utf-8")
    return json.loads(data_string)