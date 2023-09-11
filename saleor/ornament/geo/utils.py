import gzip
import logging
import os

import boto3
from django.conf import settings

logger = logging.getLogger(__name__)


def get_s3_client():
    session = boto3.session.Session()
    return session.client(
        "s3",
        region_name=settings.ORNAMENT_S3_REGION_NAME,
        endpoint_url=settings.ORNAMENT_S3_ENDPOINT_URL,
        aws_access_key_id=settings.ORNAMENT_S3_AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.ORNAMENT_S3_AWS_SECRET_ACCESS_KEY,
    )


def decompress_file_content(compressed_file_path) -> bool:
    with open(compressed_file_path, "rb") as compressed_file:
        compressed_content = compressed_file.read()

    decompressed_content = gzip.decompress(compressed_content)

    with open(settings.GEO_LITE_DB_FILE_PATH, "wb") as decompressed_file:
        decompressed_file.write(decompressed_content)

    return True


def download_geo_lite_db() -> bool:
    error_message = "Download GeoLite City DB from S3 failed!"
    file_path = settings.GEO_LITE_DB_FILE_PATH_COMPRESSED

    try:
        if os.path.exists(settings.GEO_LITE_DB_FILE_PATH):
            return True

        client = get_s3_client()
        client.download_file(
            settings.ORNAMENT_S3_BUCKET,
            "GeoLite2-City.mmdb.gz",
            file_path,
        )

        if os.path.exists(file_path):
            decompress_file_content(file_path)

            if os.path.exists(settings.GEO_LITE_DB_FILE_PATH):
                os.remove(file_path)
                return True

            raise Exception(error_message)
        raise Exception(error_message)
    except Exception as e:
        logger.error(f"{error_message} Exception: {e}")
        raise Exception(error_message)
