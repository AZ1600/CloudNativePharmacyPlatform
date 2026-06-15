from uuid import uuid4

from handlers.common import now_iso, parse_body, publish_domain_event, response, table


def lambda_handler(event, context):
    body = parse_body(event)

    title = str(body.get("title", "")).strip()
    game = str(body.get("game", "")).strip()
    region = str(body.get("region", "")).strip()
    frequency = str(body.get("frequency", "")).strip().lower()
    draw_at = str(body.get("draw_at", "")).strip()

    if (
        not title
        or not game
        or not region
        or frequency not in {"weekly", "monthly"}
        or not draw_at
    ):
        return response(
            400,
            {
                "message": "title, game, region, draw_at, and frequency (weekly or monthly) are required"
            },
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
        "draw_at": draw_at,
        "status": "OPEN",
        "fixtures_generated": False,
        "created_at": now_iso(),
    }

    table.put_item(Item=item)
    publish_domain_event(
        "TournamentCreated",
        {
            "event_type": "TournamentCreated",
            "tournament_id": tournament_id,
            "title": title,
            "game": game,
            "region": region,
            "frequency": frequency,
            "draw_at": draw_at,
            "status": "OPEN",
            "created_at": item["created_at"],
        },
    )
    return response(201, {"message": "Tournament created", "tournament_id": tournament_id})
