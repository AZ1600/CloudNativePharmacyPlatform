import json
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    batch_item_failures = []

    for record in event.get("Records", []):
        message_id = record.get("messageId", "")

        try:
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
                        "message_id": message_id,
                    }
                )
            )
        except (KeyError, TypeError, json.JSONDecodeError):
            logger.exception(
                "Failed to process low stock message %s",
                message_id,
            )
            batch_item_failures.append(
                {
                    "itemIdentifier": message_id,
                }
            )

    return {
        "batchItemFailures": batch_item_failures,
    }