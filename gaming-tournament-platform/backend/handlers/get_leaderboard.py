from boto3.dynamodb.conditions import Key

from handlers.common import response, table


def lambda_handler(event, context):
    query = event.get("queryStringParameters") or {}
    game = str(query.get("game", "")).strip()
    region = str(query.get("region", "")).strip()

    if not game or not region:
        return response(400, {"message": "game and region query parameters are required"})

    result = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq(f"GAME#{game.upper()}#REGION#{region.upper()}")
    )

    tournaments = [
        item
        for item in result.get("Items", [])
        if item.get("entity_type") == "TOURNAMENT"
    ]

    return response(
        200,
        {
            "message": "Leaderboard context fetched",
            "game": game,
            "region": region,
            "tournaments": tournaments,
        },
    )
