import json
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    detail = event.get("detail", {})

    logger.info(
        json.dumps(
            {
                "message": "Processing EventBridge low stock event",
                "event_type": detail.get("event_type"),
                "tenant_id": detail.get("tenant_id"),
                "drug_id": detail.get("drug_id"),
                "drug_name": detail.get("drug_name"),
                "quantity": detail.get("quantity"),
                "reorder_level": detail.get("reorder_level"),
            }
        )
    )

    return {
        "statusCode": 200,
        "processed_records": 1,
        "item": {
            "drug_id": detail.get("drug_id"),
            "tenant_id": detail.get("tenant_id"),
        },
    }
