from boto3.dynamodb.conditions import Key

from handlers.common import response, table


def lambda_handler(event, context):
    query = event.get("queryStringParameters") or {}
    game = str(query.get("game", "")).strip()
    region = str(query.get("region", "")).strip()

    if game and region:
        result = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(
                f"GAME#{game.upper()}#REGION#{region.upper()}"
            ),
        )
        tournaments = [
            item
            for item in result.get("Items", [])
            if item.get("entity_type") == "TOURNAMENT"
        ]
        return response(200, {"tournaments": tournaments})

    result = table.scan(
        FilterExpression="entity_type = :entity_type",
        ExpressionAttributeValues={":entity_type": "TOURNAMENT"},
    )
    return response(200, {"tournaments": result.get("Items", [])})
