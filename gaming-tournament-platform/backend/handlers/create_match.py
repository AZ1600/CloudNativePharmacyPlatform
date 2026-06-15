from uuid import uuid4

from handlers.common import now_iso, parse_body, response, table


def lambda_handler(event, context):
    body = parse_body(event)

    tournament_id = str(body.get("tournament_id", "")).strip()
    player_one = str(body.get("player_one", "")).strip()
    player_two = str(body.get("player_two", "")).strip()

    if not tournament_id or not player_one or not player_two:
        return response(
            400, {"message": "tournament_id, player_one, and player_two are required"}
        )

    match_id = str(uuid4())
    item = {
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
        "created_at": now_iso(),
    }

    table.put_item(Item=item)
    return response(
        201,
        {
            "message": "Match created",
            "match_id": match_id,
            "tournament_id": tournament_id,
        },
    )
