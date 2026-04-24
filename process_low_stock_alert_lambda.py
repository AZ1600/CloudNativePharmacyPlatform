import json
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    processed = []

    for record in event.get("Records", []):
        body = json.loads(record["body"])
        logger.info(
            json.dumps(
                {
                    "message": "Processing low stock alert",
                    "event_type": body.get("event_type"),
                    "tenant_id": body.get("tenant_id"),
                    "drug_id": body.get("drug_id"),
                    "drug_name": body.get("drug_name"),
                    "quantity": body.get("quantity"),
                    "reorder_level": body.get("reorder_level"),
                }
            )
        )
        processed.append(
            {
                "message_id": record["messageId"],
                "drug_id": body.get("drug_id"),
            }
        )

    return {
        "statusCode": 200,
        "processed_records": len(processed),
        "items": processed,
    }
