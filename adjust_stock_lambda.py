import base64
import json
import logging
import os
from datetime import datetime, timezone
from uuid import uuid4

import boto3
from boto3.dynamodb.types import TypeSerializer
from botocore.exceptions import ClientError


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
client = boto3.client("dynamodb")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ALLOWED_ROLES = {"HospitalAdmin", "Pharmacist"}
ADJUSTMENT_TYPES = {"RECEIPT", "DISPENSE", "CORRECTION", "QUARANTINE"}


def lambda_handler(event, context):
    try:
        claims = get_claims(event)
        tenant_id = get_tenant_id(claims)
        role = claims["custom:role"]

        if role not in ALLOWED_ROLES:
            return response(403, {"message": "Unauthorized"})

        drug_id = event.get("pathParameters", {}).get("drug_id")
        if not drug_id:
            raise ValueError("drug_id is required")

        body = parse_body(event)
        adjustment_type = require_adjustment_type(body)
        quantity = require_quantity(body, adjustment_type)
        reason = require_non_empty_string(body, "reason", maximum_length=500)
        delta = calculate_delta(adjustment_type, quantity)

        drug_key = {
            "PK": f"TENANT#{tenant_id}",
            "SK": f"DRUG#{drug_id}",
        }
        current = table.get_item(Key=drug_key, ConsistentRead=True).get("Item")

        if not current:
            return response(404, {"message": "Medicine was not found"})

        previous_quantity = int(current["quantity"])
        new_quantity = previous_quantity + delta
        if new_quantity < 0:
            return response(
                409,
                {
                    "message": (
                        "Adjustment would make stock negative. "
                        f"Only {previous_quantity} units are available."
                    )
                },
            )

        now = utc_now()
        adjustment_id = str(uuid4())
        user_id = claims.get("sub", "unknown")
        audit_item = {
            "PK": f"TENANT#{tenant_id}",
            "SK": f"AUDIT#{now}#{adjustment_id}",
            "GSI1PK": f"TENANT#{tenant_id}#ENTITY#AUDIT",
            "GSI1SK": f"{now}#{adjustment_id}",
            "entity_type": "AUDIT",
            "tenant_id": tenant_id,
            "adjustment_id": adjustment_id,
            "drug_id": drug_id,
            "drug_name": current["drug_name"],
            "batch_number": current["batch_number"],
            "adjustment_type": adjustment_type,
            "quantity_change": delta,
            "previous_quantity": previous_quantity,
            "new_quantity": new_quantity,
            "reason": reason,
            "created_at": now,
            "created_by": user_id,
        }

        client.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "TableName": table.name,
                        "Key": serialize_values(drug_key),
                        "UpdateExpression": (
                            "SET quantity = :new_quantity, updated_at = :updated_at, "
                            "updated_by = :updated_by"
                        ),
                        "ConditionExpression": (
                            "attribute_exists(PK) AND attribute_exists(SK) "
                            "AND quantity = :previous_quantity"
                        ),
                        "ExpressionAttributeValues": serialize_values(
                            {
                                ":new_quantity": new_quantity,
                                ":previous_quantity": previous_quantity,
                                ":updated_at": now,
                                ":updated_by": user_id,
                            }
                        ),
                    }
                },
                {
                    "Put": {
                        "TableName": table.name,
                        "Item": serialize_values(audit_item),
                        "ConditionExpression": (
                            "attribute_not_exists(PK) AND attribute_not_exists(SK)"
                        ),
                    }
                },
            ]
        )

        return response(
            200,
            {
                "message": "Stock adjusted",
                "adjustment_id": adjustment_id,
                "drug_id": drug_id,
                "previous_quantity": previous_quantity,
                "new_quantity": new_quantity,
                "quantity_change": delta,
                "adjustment_type": adjustment_type,
                "created_at": now,
            },
        )
    except KeyError as exc:
        return response(400, {"message": f"Missing required claim: {exc.args[0]}"})
    except ValueError as exc:
        return response(400, {"message": str(exc)})
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code == "TransactionCanceledException":
            return response(
                409,
                {"message": "Inventory changed during this request. Please try again."},
            )

        logger.exception("Database operation failed while adjusting stock")
        return response(500, {"message": "Unable to adjust stock. Please try again."})
    except Exception:
        logger.exception("Unexpected error while adjusting stock")
        return response(500, {"message": "Internal server error"})


def get_claims(event):
    return event["requestContext"]["authorizer"]["jwt"]["claims"]


def get_tenant_id(claims):
    tenant_id = claims.get("custom:tenant_id") or claims.get("custom:hospital_id")
    if not tenant_id:
        raise ValueError("Missing tenant identifier in token")
    return tenant_id


def parse_body(event):
    body = event.get("body")
    if body is None:
        raise ValueError("Request body is required")
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            raise ValueError("Request body must be valid JSON")
    if not isinstance(body, dict):
        raise ValueError("Unsupported request body format")
    return body


def require_adjustment_type(body):
    adjustment_type = require_non_empty_string(body, "adjustment_type").upper()
    if adjustment_type not in ADJUSTMENT_TYPES:
        raise ValueError(
            "adjustment_type must be RECEIPT, DISPENSE, CORRECTION, or QUARANTINE"
        )
    return adjustment_type


def require_quantity(body, adjustment_type):
    if "quantity" not in body:
        raise ValueError("quantity is required")
    quantity = body["quantity"]
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise ValueError("quantity must be a whole number")
    if adjustment_type == "CORRECTION" and quantity == 0:
        raise ValueError("Correction quantity cannot be zero")
    if adjustment_type != "CORRECTION" and quantity <= 0:
        raise ValueError("quantity must be greater than zero")
    return quantity


def calculate_delta(adjustment_type, quantity):
    if adjustment_type == "RECEIPT":
        return quantity
    if adjustment_type in {"DISPENSE", "QUARANTINE"}:
        return -quantity
    return quantity


def require_non_empty_string(body, field_name, maximum_length=100):
    if field_name not in body:
        raise ValueError(f"{field_name} is required")
    value = str(body[field_name]).strip()
    if not value:
        raise ValueError(f"{field_name} cannot be empty")
    if len(value) > maximum_length:
        raise ValueError(f"{field_name} must be {maximum_length} characters or fewer")
    return value


def serialize_values(values):
    serializer = TypeSerializer()
    return {key: serializer.serialize(value) for key, value in values.items()}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


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
