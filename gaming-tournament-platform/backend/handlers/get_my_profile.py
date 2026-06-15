from handlers.auth import get_user_id
from handlers.common import response, table


def lambda_handler(event, context):
    user_id = get_user_id(event)
    if not user_id:
        return response(401, {"message": "Unauthorized"})

    result = table.get_item(Key={"PK": f"USER#{user_id}", "SK": "PROFILE"})
    item = result.get("Item")

    if not item:
        return response(404, {"message": "Profile not found"})

    return response(200, {"profile": item})
