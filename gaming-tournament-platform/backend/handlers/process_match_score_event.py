import logging

from handlers.common import table


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    detail = event.get("detail", {})
    match_id = detail.get("match_id")

    if not match_id:
        return {"statusCode": 400, "message": "match_id is required"}

    table.update_item(
        Key={"PK": f"MATCH#{match_id}", "SK": "METADATA"},
        UpdateExpression="SET leaderboard_processed = :leaderboard_processed",
        ExpressionAttributeValues={":leaderboard_processed": True},
    )

    logger.info(
        {
            "message": "Processed MatchScoreUpdated event",
            "match_id": match_id,
            "player_one_score": detail.get("player_one_score"),
            "player_two_score": detail.get("player_two_score"),
        }
    )

    return {
        "statusCode": 200,
        "message": "Match score event processed",
        "match_id": match_id,
    }
