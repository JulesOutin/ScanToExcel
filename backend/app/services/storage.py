"""Stockage objet (S3 / Cloudflare R2 / Supabase Storage — API compatible S3)."""
import uuid

import boto3
from botocore.client import Config

from app.core.config import get_settings

settings = get_settings()


def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL or None,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY or None,
        region_name=settings.S3_REGION,
        config=Config(signature_version="s3v4"),
    )


def build_key(user_id: str, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"documents/{user_id}/{uuid.uuid4()}.{ext}"


def upload_bytes(key: str, data: bytes, content_type: str) -> None:
    _client().put_object(Bucket=settings.S3_BUCKET, Key=key, Body=data, ContentType=content_type)


def download_bytes(key: str) -> bytes:
    obj = _client().get_object(Bucket=settings.S3_BUCKET, Key=key)
    return obj["Body"].read()


def delete_object(key: str) -> None:
    _client().delete_object(Bucket=settings.S3_BUCKET, Key=key)


def presigned_get_url(key: str, expires_seconds: int = 300) -> str:
    return _client().generate_presigned_url(
        "get_object", Params={"Bucket": settings.S3_BUCKET, "Key": key}, ExpiresIn=expires_seconds
    )
