import os
from datetime import datetime
from typing import Any

import boto3
from loguru import logger

s3_client = boto3.client("s3")


def calculator(expression: str) -> str:
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e!s}"


def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def list_s3_files(bucket: str | None = None, prefix: str = "") -> str:
    if bucket is None:
        bucket = os.environ.get("S3_DOCUMENTS_BUCKET")
        if not bucket:
            return "Error: S3_DOCUMENTS_BUCKET environment variable not set"
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter="/")

        files = []
        if "Contents" in response:
            for obj in response["Contents"]:
                key = obj["Key"]
                size = obj["Size"]
                files.append(f"{key} ({size} bytes)")

        if not files:
            return f"No files found in s3://{bucket}/{prefix or 'root'}"

        return f"Files in s3://{bucket}/{prefix or 'root'}:\n" + "\n".join(files)

    except Exception as e:
        return f"Error listing files: {str(e)}"


def read_s3_document(bucket: str | None = None, key: str | None = None) -> str:
    if bucket is None:
        bucket = os.environ.get("S3_DOCUMENTS_BUCKET")
        if not bucket:
            return (
                "Error: S3_DOCUMENTS_BUCKET environment variable not set. "
                "Please configure it in the Lambda environment variables."
            )

    if key is None or key == "":
        return list_s3_files(bucket, prefix="")

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read()

        content_type = response.get("ContentType", "")

        if content_type.startswith("text/") or "json" in content_type:
            return content.decode("utf-8")
        else:
            return f"File content (binary, {len(content)} bytes). Content-Type: {content_type}"

    except s3_client.exceptions.NoSuchKey:
        return f"Error: File not found at s3://{bucket}/{key}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    delimiter = "___"

    tool_name_full = ""
    if (
        hasattr(context, "client_context")
        and context.client_context
        and hasattr(context.client_context, "custom")
    ):
        tool_name_full = context.client_context.custom.get("bedrockAgentCoreToolName", "")

    if not tool_name_full and hasattr(context, "bedrockAgentCoreToolName"):
        tool_name_full = context.bedrockAgentCoreToolName

    if delimiter in tool_name_full:
        tool_name = tool_name_full[tool_name_full.index(delimiter) + len(delimiter) :]
    else:
        tool_name = tool_name_full

    try:
        if tool_name == "calculator":
            expression = event.get("expression", "")
            if not expression:
                return {"error": "Missing required parameter: expression"}
            result = calculator(expression)
            return {"result": result}

        elif tool_name == "get_current_time":
            result = get_current_time()
            return {"result": result}

        elif tool_name == "read_s3_document":
            bucket = event.get("bucket", "")
            key = event.get("key", "")
            result = read_s3_document(bucket=bucket if bucket else None, key=key if key else None)
            return {"result": result}

        else:
            logger.error(f"Unknown tool: {tool_name}")
            return {"error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return {"error": str(e)}
