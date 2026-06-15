def get_claims(event):
    return (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )


def get_user_id(event):
    claims = get_claims(event)
    return claims.get("sub", "")
