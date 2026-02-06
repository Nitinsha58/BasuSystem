import base64
import uuid
import time
import json
import hmac
import hashlib


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def generate_login_jwt(*, client_id, phone, surface, request_id, secret_b64):
    iat = int(time.time())
    exp = iat + 120

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": client_id,
        "aud": "partner-api.xpsolv.ai",
        "iat": iat,
        "exp": exp,
        "jti": str(uuid.uuid4()),
        "phone": phone,
        "requestId": request_id,
        "surface": surface,
    }

    key = base64.b64decode(secret_b64)

    h = _b64url(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url(json.dumps(payload, separators=(",", ":")).encode())

    sig = hmac.new(
        key,
        f"{h}.{p}".encode(),
        hashlib.sha256
    ).digest()

    return f"{h}.{p}.{_b64url(sig)}"
