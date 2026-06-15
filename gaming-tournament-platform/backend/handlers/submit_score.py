from handlers.common import now_iso, parse_body, publish_domain_event, response, table


def lambda_handler(event, context):
    match_id = event.get("pathParameters", {}).get("match_id")
    body = parse_body(event)

    player_one_score = body.get("player_one_score")
    player_two_score = body.get("player_two_score")
    stream_url = str(body.get("stream_url", "")).strip()

    if match_id is None or player_one_score is None or player_two_score is None:
        return response(400, {"message": "match_id and both scores are required"})

    updated_at = now_iso()
    item = {
        "PK": f"MATCH#{match_id}",
        "SK": "METADATA",
        "entity_type": "MATCH",
        "match_id": match_id,
        "player_one_score": int(player_one_score),
        "player_two_score": int(player_two_score),
        "stream_url": stream_url,
        "status": "COMPLETED",
        "updated_at": updated_at,
    }

    table.put_item(Item=item)
    publish_domain_event(
        "MatchScoreUpdated",
        {
            "event_type": "MatchScoreUpdated",
            "match_id": match_id,
            "player_one_score": int(player_one_score),
            "player_two_score": int(player_two_score),
            "stream_url": stream_url,
            "status": "COMPLETED",
            "updated_at": updated_at,
        },
    )
    return response(200, {"message": "Score submitted", "match_id": match_id})
