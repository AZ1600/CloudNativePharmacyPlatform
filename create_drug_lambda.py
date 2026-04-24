import base64
import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
sqs = boto3.client("sqs")
sns = boto3.client("sns")
kinesis = boto3.client("kinesis")
events = boto3.client("events")
low_stock_queue_url = os.environ.get("LOW_STOCK_QUEUE_URL")
low_stock_topic_arn = os.environ.get("LOW_STOCK_TOPIC_ARN")
low_stock_stream_name = os.environ.get("LOW_STOCK_STREAM_NAME")
event_bus_name = os.environ.get("EVENT_BUS_NAME")

ALLOWED_ROLES = {"HospitalAdmin", "Pharmacist"}
REQUIRED_FIELDS = {
    "drug_name",
    "batch_number",
    "quantity",
    "reorder_level",
    "expiry_date",
}


def lambda_handler(event, context):
    try:
        claims = get_claims(event)
        tenant_id, hospital_id = get_tenant_context(claims)
        role = claims["custom:role"]
        user_id = claims.get("sub", "unknown")

        if role not in ALLOWED_ROLES:
            return response(403, {"message": "Unauthorized"})

        body = parse_body(event)
        validate_required_fields(body)

        drug_name = require_non_empty_string(body, "drug_name")
        batch_number = require_non_empty_string(body, "batch_number")
        expiry_date = require_non_empty_string(body, "expiry_date")
        supplier = str(body.get("supplier", "")).strip()
        quantity = require_non_negative_int(body, "quantity")
        reorder_level = require_non_negative_int(body, "reorder_level")

        drug_id = str(uuid4())
        now = utc_now()

        item = {
            "PK": f"TENANT#{tenant_id}",
            "SK": f"DRUG#{drug_id}",
            "GSI1PK": f"TENANT#{tenant_id}#ENTITY#DRUG",
            "GSI1SK": f"DRUG#{drug_name.upper()}#{drug_id}",
            "entity_type": "DRUG",
            "tenant_id": tenant_id,
            "hospital_id": hospital_id,
            "drug_id": drug_id,
            "drug_name": drug_name,
            "batch_number": batch_number,
            "quantity": quantity,
            "reorder_level": reorder_level,
            "expiry_date": expiry_date,
            "supplier": supplier,
            "created_at": now,
            "updated_at": now,
            "created_by": user_id,
            "updated_by": user_id,
        }

        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
        )

        low_stock_event_sent = False
        sns_event_sent = False
        eventbridge_event_sent = False
        kinesis_event_sent = False
        if quantity <= reorder_level:
            if low_stock_queue_url:
                publish_low_stock_event(item)
                low_stock_event_sent = True
            if low_stock_topic_arn:
                publish_low_stock_event_to_sns(item)
                sns_event_sent = True
            if event_bus_name:
                publish_low_stock_event_to_eventbridge(item)
                eventbridge_event_sent = True
            if low_stock_stream_name:
                publish_low_stock_event_to_kinesis(item)
                kinesis_event_sent = True

        return response(
            201,
            {
                "message": "Drug created",
                "drug_id": drug_id,
                "tenant_id": tenant_id,
                "low_stock_event_sent": low_stock_event_sent,
                "sns_event_sent": sns_event_sent,
                "eventbridge_event_sent": eventbridge_event_sent,
                "kinesis_event_sent": kinesis_event_sent,
            },
        )
    except KeyError as exc:
        return response(400, {"message": f"Missing required field: {exc.args[0]}"})
    except ValueError as exc:
        return response(400, {"message": str(exc)})
    except ClientError as exc:
        return response(
            500,
            {
                "message": "Database operation failed",
                "error": exc.response["Error"]["Message"],
            },
        )
    except Exception as exc:
        return response(500, {"message": "Internal server error", "error": str(exc)})


def get_claims(event):
    return event["requestContext"]["authorizer"]["jwt"]["claims"]


def get_tenant_context(claims):
    tenant_id = claims.get("custom:tenant_id") or claims.get("custom:hospital_id")
    hospital_id = claims.get("custom:hospital_id")

    if not tenant_id:
        raise ValueError(
            "Missing tenant identifier in token. Expected custom:tenant_id or custom:hospital_id"
        )

    return tenant_id, hospital_id


def parse_body(event):
    body = event.get("body")
    if body is None:
        raise ValueError("Request body is required")

    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            raise ValueError("Request body must be valid JSON")

    if isinstance(body, dict):
        return body

    raise ValueError("Unsupported request body format")


def validate_required_fields(body):
    missing_fields = sorted(field for field in REQUIRED_FIELDS if field not in body)
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")


def require_non_empty_string(body, field_name):
    value = str(body[field_name]).strip()
    if not value:
        raise ValueError(f"{field_name} cannot be empty")
    return value


def require_non_negative_int(body, field_name):
    try:
        value = int(body[field_name])
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid integer")

    if value < 0:
        raise ValueError(f"{field_name} must be zero or greater")

    return value


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def publish_low_stock_event(item):
    message = low_stock_message(item)

    sqs.send_message(
        QueueUrl=low_stock_queue_url,
        MessageBody=json.dumps(message),
        MessageAttributes={
            "event_type": {
                "DataType": "String",
                "StringValue": "LOW_STOCK_DETECTED",
            },
            "tenant_id": {
                "DataType": "String",
                "StringValue": item["tenant_id"],
            },
        },
    )


def publish_low_stock_event_to_eventbridge(item):
    message = low_stock_message(item)
    response = events.put_events(
        Entries=[
            {
                "Source": "pharmacy.inventory",
                "DetailType": "LowStockDetected",
                "Detail": json.dumps(message),
                "EventBusName": event_bus_name,
            }
        ]
    )

    if response["FailedEntryCount"] > 0:
        raise ValueError("Failed to publish low-stock event to EventBridge")


def publish_low_stock_event_to_sns(item):
    message = low_stock_message(item)
    sns.publish(
        TopicArn=low_stock_topic_arn,
        Subject="Low stock detected",
        Message=json.dumps(message),
        MessageAttributes={
            "event_type": {
                "DataType": "String",
                "StringValue": "LOW_STOCK_DETECTED",
            },
            "tenant_id": {
                "DataType": "String",
                "StringValue": item["tenant_id"],
            },
        },
    )


def publish_low_stock_event_to_kinesis(item):
    message = low_stock_message(item)
    kinesis.put_record(
        StreamName=low_stock_stream_name,
        Data=json.dumps(message),
        PartitionKey=item["tenant_id"],
    )


def low_stock_message(item):
    return {
        "event_type": "LOW_STOCK_DETECTED",
        "tenant_id": item["tenant_id"],
        "hospital_id": item["hospital_id"],
        "drug_id": item["drug_id"],
        "drug_name": item["drug_name"],
        "quantity": item["quantity"],
        "reorder_level": item["reorder_level"],
        "batch_number": item["batch_number"],
        "created_at": item["created_at"],
    }


def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST",
        },
        "body": json.dumps(body),
    }
