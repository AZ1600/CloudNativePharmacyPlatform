from uuid import uuid4

from handlers.common import now_iso, parse_body, response, table


def lambda_handler(event, context):
    body = parse_body(event)

    title = str(body.get("title", "")).strip()
    game = str(body.get("game", "")).strip()
    region = str(body.get("region", "")).strip()
    frequency = str(body.get("frequency", "")).strip().lower()

    if not title or not game or not region or frequency not in {"weekly", "monthly"}:
        return response(
            400,
            {"message": "title, game, region, and frequency (weekly or monthly) are required"},
        )

    tournament_id = str(uuid4())
    item = {
        "PK": f"TOURNAMENT#{tournament_id}",
        "SK": "METADATA",
        "GSI1PK": f"GAME#{game.upper()}#REGION#{region.upper()}",
        "GSI1SK": f"TOURNAMENT#{title.upper()}",
        "entity_type": "TOURNAMENT",
        "tournament_id": tournament_id,
        "title": title,
        "game": game,
        "region": region,
        "frequency": frequency,
        "status": "OPEN",
        "created_at": now_iso(),
    }

    table.put_item(Item=item)
    return response(201, {"message": "Tournament created", "tournament_id": tournament_id})
