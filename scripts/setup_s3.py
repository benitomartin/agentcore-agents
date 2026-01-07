import boto3
from botocore.exceptions import ClientError
from loguru import logger

from agentcore_agents.config import settings


def main() -> None:
    bucket_name = settings.s3.documents_bucket
    region = settings.aws.region

    logger.info(f"Setting up S3 bucket: {bucket_name}")
    logger.info(f"Region: {region}")

    s3_client = boto3.client("s3", region_name=region)

    try:
        s3_client.head_bucket(Bucket=bucket_name)
        logger.info(f"Bucket '{bucket_name}' already exists")
        return
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code != "404":
            logger.error(f"Error checking bucket: {e}")
            return

    logger.info(f"Creating bucket '{bucket_name}' in region '{region}'...")

    try:
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": region},
        )
        logger.info(f"✓ Bucket '{bucket_name}' created successfully")
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "BucketAlreadyExists":
            logger.info(f"Bucket '{bucket_name}' already exists (created by another user)")
        else:
            logger.error(f"Error creating bucket: {e}")
            raise


if __name__ == "__main__":
    main()

