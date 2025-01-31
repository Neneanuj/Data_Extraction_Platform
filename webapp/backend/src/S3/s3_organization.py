import boto3
import os
from typing import Any, Dict
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from typing import Union 

def generate_presigned_url(bucket: str, key: str, expiration=3600) -> str:
    """生成S3预签名下载链接（企业级安全配置）"""
    s3_client = boto3.client('s3', config=boto3.session.Config(signature_version='s3v4'))
    try:
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration
        )
    except ClientError as e:
        raise RuntimeError(f"预签名URL生成失败: {str(e)}")




def upload_to_s3(bucket_name: str, s3_key: str, data: Union[bytes, str]) -> None:
    """
    上传文件或字节数据到指定的S3桶

    :param bucket_name: 目标S3桶名称
    :param s3_key: S3中的目标键（路径）
    :param data: 可以是文件路径（str）或字节数据（bytes）
    """
    try:
        s3 = boto3.client('s3')
        if isinstance(data, bytes):
            # 处理字节数据
            s3.put_object(Bucket=bucket_name, Key=s3_key, Body=data)
        else:
            # 处理文件路径
            s3.upload_file(Filename=data, Bucket=bucket_name, Key=s3_key)
    except Exception as e:
        raise Exception(f"Failed to upload file to S3: {str(e)}")

def generate_s3_key(file_type: str, file_name: str) -> str:
    """
    Generate S3 key for storing files
    """
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{file_type}/{timestamp}_{file_name}"

def download_from_s3(bucket_name: str, object_name: str, file_path: str) -> None:
    """
    Download a file from S3 bucket
    """
    s3_client = boto3.client('s3')
    try:
        s3_client.download_file(bucket_name, object_name, file_path)
    except Exception as e:
        raise Exception(f"Failed to download file from S3: {str(e)}")
