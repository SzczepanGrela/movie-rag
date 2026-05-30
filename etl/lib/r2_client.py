import boto3

from lib.config import EtlSettings

_CACHE_CONTROL = "public, max-age=31536000, immutable"


class R2Client:
    def __init__(self, settings: EtlSettings) -> None:
        missing = [
            name
            for name in ("r2_account_id", "r2_access_key_id", "r2_secret_access_key")
            if getattr(settings, name) is None
        ]
        if missing:
            raise RuntimeError(f"R2 credentials missing in infra/.env: {', '.join(missing)}")

        self._bucket = settings.r2_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
        )

    def put_jpeg(self, key: str, data: bytes) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType="image/jpeg",
            CacheControl=_CACHE_CONTROL,
        )
