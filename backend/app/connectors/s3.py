import boto3
from botocore.config import Config
from app.core.config import settings
from typing import BinaryIO, Optional
import hashlib
from uuid import uuid4


class S3Connector:
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            config=Config(signature_version='s3v4'),
        )
        self.bucket = settings.MINIO_BUCKET

    def upload_file(
        self,
        file_obj: BinaryIO,
        key: str,
        content_type: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """Upload file to S3/MinIO and return the object URI."""
        extra_args = {'ContentType': content_type}
        if metadata:
            extra_args['Metadata'] = {k: str(v) for k, v in metadata.items()}

        self.client.upload_fileobj(file_obj, self.bucket, key, ExtraArgs=extra_args)
        return f"s3://{self.bucket}/{key}"

    def download_file(self, key: str) -> bytes:
        """Download file from S3/MinIO."""
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response['Body'].read()

    def delete_file(self, key: str) -> bool:
        """Delete file from S3/MinIO."""
        self.client.delete_object(Bucket=self.bucket, Key=key)
        return True

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for authorized access."""
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=expiration,
        )

    def file_exists(self, key: str) -> bool:
        """Check if file exists in S3/MinIO."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except self.client.exceptions.ClientError:
            return False


def compute_checksum(file_obj: BinaryIO) -> str:
    """Compute SHA256 checksum of file content."""
    hasher = hashlib.sha256()
    for chunk in iter(lambda: file_obj.read(8192), b''):
        hasher.update(chunk)
    file_obj.seek(0)
    return hasher.hexdigest()


def generate_object_key(org_id: str, source_id: str, filename: str) -> str:
    """Generate S3 object key with org/source scoping."""
    return f"orgs/{org_id}/sources/{source_id}/{uuid4().hex}_{filename}"