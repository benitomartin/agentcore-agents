import base64
import json
from typing import Any


def decode_jwt_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        return {}

    payload = parts[1]
    padding = len(payload) % 4
    if padding:
        payload += "=" * (4 - padding)

    try:
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return {}


def extract_user_identity(access_token: str) -> dict[str, str]:
    jwt_payload = decode_jwt_payload(access_token)

    sub = jwt_payload.get("sub", "")
    username = jwt_payload.get("username", "")
    email = jwt_payload.get("email", "")

    return {
        "actor_id": sub or username,
        "username": username,
        "email": email,
        "user_sub": sub,
    }


def get_actor_id_from_token(access_token: str) -> str:
    identity = extract_user_identity(access_token)
    return identity["actor_id"]
