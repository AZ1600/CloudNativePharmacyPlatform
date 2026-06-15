from boto3.dynamodb.conditions import Key

from handlers.common import response, table


def lambda_handler(event, context):
    tournament_id = event.get("pathParameters", {}).get("tournament_id")

    if not tournament_id:
        return response(400, {"message": "tournament_id is required"})

    result = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq(f"TOURNAMENT#{tournament_id}")
        & Key("GSI1SK").begins_with("MATCH#"),
    )

    matches = [
        item for item in result.get("Items", []) if item.get("entity_type") == "MATCH"
    ]

    return response(
        200,
        {
            "tournament_id": tournament_id,
            "matches": matches,
        },
    )
