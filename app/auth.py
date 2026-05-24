import hashlib
import os
import secrets
from urllib.parse import urlparse

from flask import redirect, request, session, url_for


SESSION_KEY = "auth_ok"


def password_enabled():
    return bool(os.getenv("FLASK_PASSWORD"))


def is_authenticated():
    return not password_enabled() or session.get(SESSION_KEY)


def _secret_key():
    if key := os.getenv("FLASK_SECRET_KEY"):
        return key
    if pw := os.getenv("FLASK_PASSWORD"):
        return hashlib.sha256(pw.encode()).hexdigest()
    return os.urandom(24).hex()


def _safe_next(url):
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return None
    if not url.startswith("/") or url.startswith("//"):
        return None
    return url


def init_auth(app):
    app.secret_key = _secret_key()

    @app.before_request
    def require_password():
        if not password_enabled() or is_authenticated():
            return None
        if request.endpoint == "main.login":
            return None
        next_url = request.path
        if request.query_string:
            next_url += "?" + request.query_string.decode()
        return redirect(url_for("main.login", next=next_url))


def check_password(submitted: str) -> bool:
    expected = os.getenv("FLASK_PASSWORD", "")
    if not expected:
        return True
    return secrets.compare_digest(submitted or "", expected)
