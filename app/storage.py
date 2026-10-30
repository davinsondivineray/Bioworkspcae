import mimetypes
from pathlib import Path
from uuid import uuid4

import boto3

from .config import settings


ALLOWED_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".webp", ".csv", ".xlsx", ".docx", ".txt",
}
MAX_BYTES = settings.max_upload_mb * 1024 * 1024


def validate_upload(filename: str, content: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Upload type is not supported")
    if not content or len(content) > MAX_BYTES:
        raise ValueError(f"Upload must be between 1 byte and {settings.max_upload_mb} MB")
    signatures = {
        ".pdf": content.startswith(b"%PDF"),
        ".png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": content.startswith(b"\xff\xd8\xff"),
        ".jpeg": content.startswith(b"\xff\xd8\xff"),
        ".webp": content.startswith(b"RIFF") and content[8:12] == b"WEBP",
    }
    if ext in signatures and not signatures[ext]:
        raise ValueError("File contents do not match the filename type")
    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return mime


def save_upload(filename: str, content: bytes) -> tuple[str, str]:
    ext = Path(filename).suffix.lower()
    key = f"uploads/{uuid4().hex}{ext}"
    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    if settings.s3_bucket:
        boto3.client("s3", region_name=settings.aws_region).put_object(
            Bucket=settings.s3_bucket, Key=key, Body=content, ContentType=mime,
            ServerSideEncryption="AES256",
        )
    else:
        root = Path(settings.local_upload_dir).resolve()
        path = root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return key, mime


def read_upload(key: str) -> bytes:
    if settings.s3_bucket:
        response = boto3.client("s3", region_name=settings.aws_region).get_object(Bucket=settings.s3_bucket, Key=key)
        return response["Body"].read(MAX_BYTES + 1)
    root = Path(settings.local_upload_dir).resolve()
    path = (root / key).resolve()
    if root not in path.parents:
        raise ValueError("Invalid storage key")
    return path.read_bytes()


def delete_upload(key: str) -> None:
    if settings.s3_bucket:
        client = boto3.client("s3", region_name=settings.aws_region)
        versions = client.list_object_versions(Bucket=settings.s3_bucket, Prefix=key)
        objects = [{"Key": item["Key"], "VersionId": item["VersionId"]}
                   for item in versions.get("Versions", []) + versions.get("DeleteMarkers", [])
                   if item["Key"] == key]
        if objects:
            client.delete_objects(Bucket=settings.s3_bucket, Delete={"Objects": objects, "Quiet": True})
        else:
            client.delete_object(Bucket=settings.s3_bucket, Key=key)
        return
    root = Path(settings.local_upload_dir).resolve()
    path = (root / key).resolve()
    if root in path.parents:
        path.unlink(missing_ok=True)


def download_url(key: str) -> str:
    if settings.s3_bucket:
        return boto3.client("s3", region_name=settings.aws_region).generate_presigned_url(
            "get_object", Params={"Bucket": settings.s3_bucket, "Key": key}, ExpiresIn=300,
        )
    return f"/api/files/{key.rsplit('/', 1)[-1]}"
