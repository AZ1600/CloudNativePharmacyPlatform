from itertools import zip_longest
from uuid import uuid4

from boto3.dynamodb.conditions import Key

from handlers.common import now_iso, publish_domain_event, response, table


def lambda_handler(event, context):
    now = now_iso()
    tournaments = table.scan(
        FilterExpression="entity_type = :entity_type AND #status = :status AND draw_at <= :draw_at",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":entity_type": "TOURNAMENT",
            ":status": "OPEN",
            ":draw_at": now,
        },
    ).get("Items", [])

    generated = []

    for tournament in tournaments:
        tournament_id = tournament["tournament_id"]
        participants = table.query(
            KeyConditionExpression=Key("PK").eq(f"TOURNAMENT#{tournament_id}")
            & Key("SK").begins_with("PLAYER#")
        ).get("Items", [])

        user_ids = [item["user_id"] for item in participants]
        if len(user_ids) < 2:
            table.update_item(
                Key={"PK": f"TOURNAMENT#{tournament_id}", "SK": "METADATA"},
                UpdateExpression="SET #status = :status, fixtures_generated = :fixtures_generated, updated_at = :updated_at",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": "INSUFFICIENT_PLAYERS",
                    ":fixtures_generated": True,
                    ":updated_at": now,
                },
            )
            generated.append(
                {
                    "tournament_id": tournament_id,
                    "matches_created": 0,
                    "status": "INSUFFICIENT_PLAYERS",
                }
            )
            continue

        created_match_ids = []
        matches_created = 0
        for player_one, player_two in zip_longest(user_ids[::2], user_ids[1::2]):
            if not player_one or not player_two:
                continue

            match_id = str(uuid4())
            created_match_ids.append(match_id)
            table.put_item(
                Item={
                    "PK": f"MATCH#{match_id}",
                    "SK": "METADATA",
                    "GSI1PK": f"TOURNAMENT#{tournament_id}",
                    "GSI1SK": f"MATCH#{match_id}",
                    "entity_type": "MATCH",
                    "match_id": match_id,
                    "tournament_id": tournament_id,
                    "player_one": player_one,
                    "player_two": player_two,
                    "player_one_score": None,
                    "player_two_score": None,
                    "stream_url": "",
                    "status": "SCHEDULED",
                    "created_at": now,
                }
            )
            matches_created += 1

        table.update_item(
            Key={"PK": f"TOURNAMENT#{tournament_id}", "SK": "METADATA"},
            UpdateExpression="SET #status = :status, fixtures_generated = :fixtures_generated, updated_at = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "DRAWN",
                ":fixtures_generated": True,
                ":updated_at": now,
            },
        )
        publish_domain_event(
            "FixturesGenerated",
            {
                "event_type": "FixturesGenerated",
                "tournament_id": tournament_id,
                "draw_at": tournament.get("draw_at"),
                "matches_created": matches_created,
                "match_ids": created_match_ids,
                "status": "DRAWN",
                "generated_at": now,
            },
        )

        generated.append(
            {
                "tournament_id": tournament_id,
                "matches_created": matches_created,
                "status": "DRAWN",
            }
        )

    return response(
        200,
        {
            "message": "Fixture generation run complete",
            "processed_tournaments": len(generated),
            "results": generated,
        },
    )
