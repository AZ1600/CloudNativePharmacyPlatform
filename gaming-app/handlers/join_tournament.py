from handlers.common import now_iso, parse_body, response, table


def lambda_handler(event, context):
    tournament_id = event.get("pathParameters", {}).get("tournament_id")
    body = parse_body(event)
    user_id = str(body.get("user_id", "")).strip()

    if not tournament_id or not user_id:
        return response(400, {"message": "tournament_id and user_id are required"})

    item = {
        "PK": f"TOURNAMENT#{tournament_id}",
        "SK": f"PLAYER#{user_id}",
        "entity_type": "TOURNAMENT_PARTICIPANT",
        "tournament_id": tournament_id,
        "user_id": user_id,
        "joined_at": now_iso(),
    }

    table.put_item(Item=item)
    return response(200, {"message": "Joined tournament", "tournament_id": tournament_id})
