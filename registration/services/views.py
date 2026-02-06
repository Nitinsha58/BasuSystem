"""Partner login initiation (server-to-server).

This is NOT a webhook receiver.
We generate a short-lived HS256 JWT and call the partner API over mTLS,
then redirect the browser to the returned handoff URL.
"""

import uuid
import re
import time
from urllib.parse import urlparse
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import requests
from .xpsolv import generate_login_jwt


PHONE_RE = re.compile(r"^[6-9]\d{9}$")


@login_required
@require_POST
def xpsolv_login_init(request):
    phone = (getattr(request.user, 'phone', None) or '').strip()
    surface = getattr(settings, 'XPSOLV_SURFACE', 'A')

    # Very small session-based throttle to reduce accidental double clicks.
    now = int(time.time())
    last = int(request.session.get('xpsolv_last_init_ts', 0) or 0)
    if now - last < 2:
        return JsonResponse({"error": "TOO_MANY_REQUESTS"}, status=429)
    request.session['xpsolv_last_init_ts'] = now

    # Validate phone (DO NOT TRUST FRONTEND)
    if not PHONE_RE.fullmatch(phone):
        return JsonResponse({"error": "INVALID_PHONE"}, status=400)

    request_id = str(uuid.uuid4())

    if not getattr(settings, 'XPSOLV_CLIENT_ID', None):
        return JsonResponse({"error": "MISCONFIGURED_CLIENT"}, status=500)
    if not getattr(settings, 'XPSOLV_JWT_SECRET_B64', None):
        return JsonResponse({"error": "MISCONFIGURED_JWT_SECRET"}, status=500)
    if not getattr(settings, 'XPSOLV_LOGIN_URL', None):
        return JsonResponse({"error": "MISCONFIGURED_LOGIN_URL"}, status=500)
    if not getattr(settings, 'XPSOLV_CERT_PATH', None) or not getattr(settings, 'XPSOLV_KEY_PATH', None):
        return JsonResponse({"error": "MISCONFIGURED_MTLS"}, status=500)

    def _make_token() -> str:
        return generate_login_jwt(
            client_id=settings.XPSOLV_CLIENT_ID,
            phone=phone,
            surface=surface,
            request_id=request_id,
            secret_b64=settings.XPSOLV_JWT_SECRET_B64,
        )

    payload = {
        "phone": phone,
        "clientId": settings.XPSOLV_CLIENT_ID,
        "requestId": request_id,
        "surface": surface,
    }

    try:
        resp = requests.post(
            settings.XPSOLV_LOGIN_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {_make_token()}",
            },
            cert=(settings.XPSOLV_CERT_PATH, settings.XPSOLV_KEY_PATH),
            timeout=(3.05, 7.0),
        )
    except (requests.Timeout, requests.ConnectionError):
        # Retry once with SAME requestId (idempotency) but a fresh JWT (new jti).
        try:
            resp = requests.post(
                settings.XPSOLV_LOGIN_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {_make_token()}",
                },
                cert=(settings.XPSOLV_CERT_PATH, settings.XPSOLV_KEY_PATH),
                timeout=(3.05, 7.0),
            )
        except requests.RequestException:
            return JsonResponse({"error": "UPSTREAM_UNREACHABLE"}, status=502)
    except requests.RequestException:
        return JsonResponse({"error": "UPSTREAM_UNREACHABLE"}, status=502)

    if resp.status_code != 200:
        try:
            return JsonResponse(resp.json(), status=resp.status_code)
        except ValueError:
            return JsonResponse({"error": "UPSTREAM_ERROR", "status": resp.status_code}, status=resp.status_code)

    data = resp.json()
    redirect_url = data.get('redirectUrl')
    if not redirect_url:
        return JsonResponse({"error": "INVALID_UPSTREAM_RESPONSE", "data": data}, status=502)

    parsed = urlparse(redirect_url)
    if parsed.scheme != 'https' or not parsed.netloc:
        return JsonResponse({"error": "UNSAFE_REDIRECT_URL"}, status=502)

    allowed_hosts = getattr(settings, 'XPSOLV_REDIRECT_HOST_ALLOWLIST', None)
    if allowed_hosts:
        host = parsed.hostname or ''
        if host not in set(allowed_hosts):
            return JsonResponse({"error": "UNSAFE_REDIRECT_HOST"}, status=502)

    # If this endpoint is called from a normal button click, redirect.
    # If called via AJAX/HTMX, client can still use the JSON.
    if request.headers.get('HX-Request') == 'true' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(data)

    return redirect(redirect_url)
