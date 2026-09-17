from functools import cached_property
from io import BytesIO
from urllib.parse import quote

import boto3
from botocore.client import BaseClient

from app.core.config import settings


class R2ConfigurationError(RuntimeError):
    pass


class R2Storage:
    def _required_setting(
        self,
        value: str,
        name: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise R2ConfigurationError(f"{name} is required for R2 storage.")

        return normalized

    @cached_property
    def bucket_name(self) -> str:
        return self._required_setting(
            settings.r2_bucket_name,
            "R2_BUCKET_NAME",
        )

    @cached_property
    def client(self) -> BaseClient:
        account_id = self._required_setting(
            settings.r2_account_id,
            "R2_ACCOUNT_ID",
        )
        access_key_id = self._required_setting(
            settings.r2_access_key_id,
            "R2_ACCESS_KEY_ID",
        )
        secret_access_key = self._required_setting(
            settings.r2_secret_access_key,
            "R2_SECRET_ACCESS_KEY",
        )

        return boto3.client(
            "s3",
            endpoint_url=(f"https://{account_id}.r2.cloudflarestorage.com"),
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )

    def upload(
        self,
        *,
        key: str,
        content: bytes,
        content_type: str,
    ) -> None:
        self.client.upload_fileobj(
            BytesIO(content),
            self.bucket_name,
            key,
            ExtraArgs={
                "ContentType": content_type,
            },
        )

    def delete(self, key: str) -> None:
        self.client.delete_object(
            Bucket=self.bucket_name,
            Key=key,
        )

    def public_url(self, key: str) -> str:
        base_url = self._required_setting(
            settings.r2_public_base_url,
            "R2_PUBLIC_BASE_URL",
        ).rstrip("/")

        encoded_key = quote(
            key.lstrip("/"),
            safe="/",
        )

        return f"{base_url}/{encoded_key}"


r2_storage = R2Storage()
