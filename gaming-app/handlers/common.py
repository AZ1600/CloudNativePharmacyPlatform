import json
import os
from datetime import datetime, timezone

import boto3


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["APP_TABLE_NAME"])


def parse_body(event):
    body = event.get("body")
    if body is None:
        return {}
    if isinstance(body, str):
        return json.loads(body)
    return body


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body),
    }


def now_iso():
    return datetime.now(timezone.utc).isoformat()
