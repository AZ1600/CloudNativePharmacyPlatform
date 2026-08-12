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

        items = query_tenant_inventory(tenant_id)
        drugs = [serialize_drug(item) for item in items]

        return response(
            200,
            {
                "items": drugs,
                "count": len(drugs),
            },
        )
    except KeyError as exc:
        return response(
            400,
            {"message": f"Missing required claim: {exc.args[0]}"},
        )
    except ValueError as exc:
        return response(400, {"message": str(exc)})
    except ClientError:
        logger.exception("Database operation failed while reading inventory")
        return response(
            500,
            {"message": "Unable to load inventory. Please try again."},
        )
    except Exception:
        logger.exception("Unexpected error while reading inventory")
        return response(
            500,
            {"message": "Internal server error"},
        )


def get_claims(event):
    return event["requestContext"]["authorizer"]["jwt"]["claims"]


def get_tenant_id(claims):
    tenant_id = claims.get("custom:tenant_id") or claims.get(
        "custom:hospital_id"
    )

    if not tenant_id:
        raise ValueError(
            "Missing tenant identifier in token. "
            "Expected custom:tenant_id or custom:hospital_id"
        )

    return tenant_id


def query_tenant_inventory(tenant_id):
    query_arguments = {
        "IndexName": "GSI1",
        "KeyConditionExpression": "GSI1PK = :gsi1pk",
        "ExpressionAttributeValues": {
            ":gsi1pk": f"TENANT#{tenant_id}#ENTITY#DRUG",
        },
    }

    items = []

    while True:
        result = table.query(**query_arguments)
        items.extend(result.get("Items", []))

        last_evaluated_key = result.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break

        query_arguments["ExclusiveStartKey"] = last_evaluated_key

    return items


def serialize_drug(item):
    return {
        "id": item["drug_id"],
        "drug_name": item["drug_name"],
        "batch_number": item["batch_number"],
        "quantity": int(item["quantity"]),
        "reorder_level": int(item["reorder_level"]),
        "expiry_date": item["expiry_date"],
        "supplier": item.get("supplier", ""),
        "category": item.get("category", "Uncategorised"),
        "location": item.get("location", "Not assigned"),
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
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
        },
        "body": json.dumps(body, default=json_default),
    }
