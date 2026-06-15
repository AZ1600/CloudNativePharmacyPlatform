from handlers.auth import get_user_id
from handlers.common import now_iso, publish_domain_event, response, table


def lambda_handler(event, context):
    tournament_id = event.get("pathParameters", {}).get("tournament_id")
    user_id = get_user_id(event)

    if not tournament_id or not user_id:
        return response(400, {"message": "tournament_id and user_id are required"})

    joined_at = now_iso()
    item = {
        "PK": f"TOURNAMENT#{tournament_id}",
        "SK": f"PLAYER#{user_id}",
        "entity_type": "TOURNAMENT_PARTICIPANT",
        "tournament_id": tournament_id,
        "user_id": user_id,
        "joined_at": joined_at,
    }

    table.put_item(Item=item)
    publish_domain_event(
        "PlayerJoinedTournament",
        {
            "event_type": "PlayerJoinedTournament",
            "tournament_id": tournament_id,
            "user_id": user_id,
            "joined_at": joined_at,
        },
    )
    return response(200, {"message": "Joined tournament", "tournament_id": tournament_id})
