import json
import os
from datetime import datetime, timezone

import boto3


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["APP_TABLE_NAME"])
events = boto3.client("events")


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


def publish_domain_event(detail_type, detail):
    event_bus_name = os.environ.get("EVENT_BUS_NAME", "default")
    return events.put_events(
        Entries=[
            {
                "Source": "gaming.tournaments",
                "DetailType": detail_type,
                "Detail": json.dumps(detail),
                "EventBusName": event_bus_name,
            }
        ]
    )
