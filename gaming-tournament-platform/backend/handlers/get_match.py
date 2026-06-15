from handlers.common import response, table


def lambda_handler(event, context):
    match_id = event.get("pathParameters", {}).get("match_id")

    if not match_id:
        return response(400, {"message": "match_id is required"})

    result = table.get_item(Key={"PK": f"MATCH#{match_id}", "SK": "METADATA"})
    item = result.get("Item")

    if not item:
        return response(404, {"message": "Match not found"})

    return response(200, {"match": item})
