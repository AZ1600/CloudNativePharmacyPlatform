from uuid import uuid4

from handlers.common import now_iso, parse_body, response, table


def lambda_handler(event, context):
    body = parse_body(event)

    gamer_tag = str(body.get("gamer_tag", "")).strip()
    region = str(body.get("region", "")).strip()
    favorite_games = body.get("favorite_games", [])

    if not gamer_tag or not region:
        return response(400, {"message": "gamer_tag and region are required"})

    user_id = str(uuid4())
    item = {
        "PK": f"USER#{user_id}",
        "SK": "PROFILE",
        "GSI1PK": f"REGION#{region}",
        "GSI1SK": f"PROFILE#{gamer_tag.upper()}",
        "entity_type": "PROFILE",
        "user_id": user_id,
        "gamer_tag": gamer_tag,
        "region": region,
        "country": body.get("country", ""),
        "timezone": body.get("timezone", ""),
        "favorite_games": favorite_games,
        "stream_handle": body.get("stream_handle", ""),
        "created_at": now_iso(),
    }

    table.put_item(Item=item)
    return response(201, {"message": "Profile created", "user_id": user_id})
