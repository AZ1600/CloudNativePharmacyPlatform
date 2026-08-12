import json
import logging
import os
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ALLOWED_ROLES = {"HospitalAdmin", "Pharmacist", "Viewer"}


def lambda_handler(event, context):
    try:
        claims = get_claims(event)
        tenant_id = get_tenant_id(claims)
        role = claims["custom:role"]
        if role not in ALLOWED_ROLES:
            return response(403, {"message": "Unauthorized"})

        result = table.query(
            IndexName="GSI1",
            KeyConditionExpression="GSI1PK = :gsi1pk",
            ExpressionAttributeValues={
                ":gsi1pk": f"TENANT#{tenant_id}#ENTITY#AUDIT",
            },
            ScanIndexForward=False,
            Limit=100,
        )
        items = [serialize_audit_item(item) for item in result.get("Items", [])]
        return response(200, {"items": items, "count": len(items)})
    except KeyError as exc:
        return response(400, {"message": f"Missing required claim: {exc.args[0]}"})
    except ValueError as exc:
        return response(400, {"message": str(exc)})
    except ClientError:
        logger.exception("Database operation failed while reading audit history")
        return response(500, {"message": "Unable to load audit history."})
    except Exception:
        logger.exception("Unexpected error while reading audit history")
        return response(500, {"message": "Internal server error"})


def get_claims(event):
    return event["requestContext"]["authorizer"]["jwt"]["claims"]


def get_tenant_id(claims):
    tenant_id = claims.get("custom:tenant_id") or claims.get("custom:hospital_id")
    if not tenant_id:
        raise ValueError("Missing tenant identifier in token")
    return tenant_id


def serialize_audit_item(item):
    return {
        "id": item["adjustment_id"],
        "drug_id": item["drug_id"],
        "drug_name": item["drug_name"],
        "batch_number": item["batch_number"],
        "adjustment_type": item["adjustment_type"],
        "quantity_change": int(item["quantity_change"]),
        "previous_quantity": int(item["previous_quantity"]),
        "new_quantity": int(item["new_quantity"]),
        "reason": item["reason"],
        "created_at": item["created_at"],
        "created_by": item["created_by"],
    }


def json_default(value):
    if isinstance(value, Decimal):
        return int(value)
    raise TypeError(f"Cannot serialize value of type {type(value).__name__}")


def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,GET",
        },
        "body": json.dumps(body, default=json_default),
    }
