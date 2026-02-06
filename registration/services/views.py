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


def _get_client_ip(request):
    xff = (request.META.get('HTTP_X_FORWARDED_FOR') or '').strip()
    if xff:
        # XFF can be a list: client, proxy1, proxy2
        return xff.split(',')[0].strip() or None
    return (request.META.get('REMOTE_ADDR') or '').strip() or None


def _sanitize_upstream_json(data):
    if not isinstance(data, dict):
        return data
    cleaned = dict(data)
    redirect_url = cleaned.get('redirectUrl')
    if isinstance(redirect_url, str) and redirect_url:
        parsed = urlparse(redirect_url)
        # Avoid storing query/fragment (could contain sensitive tokens)
        cleaned['redirectUrl'] = f"{parsed.scheme}://{parsed.netloc}{parsed.path}" if parsed.scheme and parsed.netloc else "<redacted>"
    return cleaned


@login_required
@require_POST
def xpsolv_login_init(request):
    posted_phone = (request.POST.get('phone', '') or '').strip()
    user_phone = (getattr(request.user, 'phone', None) or '').strip()
    phone = posted_phone or user_phone
    surface = getattr(settings, 'XPSOLV_SURFACE', 'A')

    request_id = uuid.uuid4()

    # Best-effort audit log (must not break the login flow if DB/migrations are not ready)
    log = None
    try:
        from registration.models import XPSolvLoginInitLog

        log = XPSolvLoginInitLog.objects.create(
            request_id=request_id,
            user=request.user,
            phone=phone,
            client_id=(getattr(settings, 'XPSOLV_CLIENT_ID', None) or ''),
            surface=surface,
            ip_address=_get_client_ip(request),
            user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:2000],
            is_hx=(request.headers.get('HX-Request') == 'true'),
            session_key=(request.session.session_key or ''),
        )
    except Exception:
        log = None

    def _finalize(**kwargs):
        nonlocal log
        if not log:
            return
        try:
            for k, v in kwargs.items():
                setattr(log, k, v)
            log.save(update_fields=list(kwargs.keys()) + ["updated_at"])
        except Exception:
            pass

    # Very small session-based throttle to reduce accidental double clicks.
    now = int(time.time())
    last = int(request.session.get('xpsolv_last_init_ts', 0) or 0)
    if now - last < 2:
        _finalize(status_code=429, success=False, error_code="TOO_MANY_REQUESTS")
        return JsonResponse({"error": "TOO_MANY_REQUESTS"}, status=429)
    request.session['xpsolv_last_init_ts'] = now

    # Validate phone (DO NOT TRUST FRONTEND)
    if not PHONE_RE.fullmatch(phone):
        _finalize(status_code=400, success=False, error_code="INVALID_PHONE")
        return JsonResponse({"error": "INVALID_PHONE"}, status=400)

    request_id_str = str(request_id)

    if not getattr(settings, 'XPSOLV_CLIENT_ID', None):
        _finalize(status_code=500, success=False, error_code="MISCONFIGURED_CLIENT")
        return JsonResponse({"error": "MISCONFIGURED_CLIENT"}, status=500)
    if not getattr(settings, 'XPSOLV_JWT_SECRET_B64', None):
        _finalize(status_code=500, success=False, error_code="MISCONFIGURED_JWT_SECRET")
        return JsonResponse({"error": "MISCONFIGURED_JWT_SECRET"}, status=500)
    if not getattr(settings, 'XPSOLV_LOGIN_URL', None):
        _finalize(status_code=500, success=False, error_code="MISCONFIGURED_LOGIN_URL")
        return JsonResponse({"error": "MISCONFIGURED_LOGIN_URL"}, status=500)
    if not getattr(settings, 'XPSOLV_CERT_PATH', None) or not getattr(settings, 'XPSOLV_KEY_PATH', None):
        _finalize(status_code=500, success=False, error_code="MISCONFIGURED_MTLS")
        return JsonResponse({"error": "MISCONFIGURED_MTLS"}, status=500)

    def _make_token() -> str:
        return generate_login_jwt(
            client_id=settings.XPSOLV_CLIENT_ID,
            phone=phone,
            surface=surface,
            request_id=request_id_str,
            secret_b64=settings.XPSOLV_JWT_SECRET_B64,
        )

    payload = {
        "phone": phone,
        "clientId": settings.XPSOLV_CLIENT_ID,
        "requestId": request_id_str,
        "surface": surface,
    }

    t0 = time.monotonic()
    attempts = 1
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
        attempts = 2
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
            _finalize(
                status_code=502,
                success=False,
                error_code="UPSTREAM_UNREACHABLE",
                attempts=attempts,
                duration_ms=int((time.monotonic() - t0) * 1000),
            )
            return JsonResponse({"error": "UPSTREAM_UNREACHABLE"}, status=502)
    except requests.RequestException:
        _finalize(
            status_code=502,
            success=False,
            error_code="UPSTREAM_UNREACHABLE",
            attempts=attempts,
            duration_ms=int((time.monotonic() - t0) * 1000),
        )
        return JsonResponse({"error": "UPSTREAM_UNREACHABLE"}, status=502)

    duration_ms = int((time.monotonic() - t0) * 1000)

    if resp.status_code != 200:
        try:
            upstream = resp.json()
            _finalize(
                status_code=resp.status_code,
                success=False,
                error_code="UPSTREAM_ERROR",
                attempts=attempts,
                duration_ms=duration_ms,
                upstream_response=_sanitize_upstream_json(upstream),
            )
            return JsonResponse(upstream, status=resp.status_code)
        except ValueError:
            _finalize(
                status_code=resp.status_code,
                success=False,
                error_code="UPSTREAM_ERROR",
                attempts=attempts,
                duration_ms=duration_ms,
            )
            return JsonResponse({"error": "UPSTREAM_ERROR", "status": resp.status_code}, status=resp.status_code)

    data = resp.json()
    redirect_url = data.get('redirectUrl')
    if not redirect_url:
        _finalize(
            status_code=502,
            success=False,
            error_code="INVALID_UPSTREAM_RESPONSE",
            attempts=attempts,
            duration_ms=duration_ms,
            upstream_response=_sanitize_upstream_json(data),
        )
        return JsonResponse({"error": "INVALID_UPSTREAM_RESPONSE", "data": data}, status=502)

    parsed = urlparse(redirect_url)
    if parsed.scheme != 'https' or not parsed.netloc:
        _finalize(
            status_code=502,
            success=False,
            error_code="UNSAFE_REDIRECT_URL",
            attempts=attempts,
            duration_ms=duration_ms,
            upstream_response=_sanitize_upstream_json(data),
        )
        return JsonResponse({"error": "UNSAFE_REDIRECT_URL"}, status=502)

    allowed_hosts = getattr(settings, 'XPSOLV_REDIRECT_HOST_ALLOWLIST', None)
    if allowed_hosts:
        host = parsed.hostname or ''
        if host not in set(allowed_hosts):
            _finalize(
                status_code=502,
                success=False,
                error_code="UNSAFE_REDIRECT_HOST",
                attempts=attempts,
                duration_ms=duration_ms,
                upstream_response=_sanitize_upstream_json(data),
            )
            return JsonResponse({"error": "UNSAFE_REDIRECT_HOST"}, status=502)

    _finalize(
        status_code=200,
        success=True,
        attempts=attempts,
        duration_ms=duration_ms,
        redirect_host=(parsed.hostname or ''),
        redirect_path=(parsed.path or ''),
        upstream_response=_sanitize_upstream_json(data),
    )

    # If this endpoint is called from a normal button click, redirect.
    # If called via AJAX/HTMX, client can still use the JSON.
    if request.headers.get('HX-Request') == 'true' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(data)

    return redirect(redirect_url)
