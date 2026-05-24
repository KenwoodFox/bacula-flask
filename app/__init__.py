import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from .auth import init_auth

# Project-root .env; override stale shell exports (e.g. old PSQL_USER typo).
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)


def create_app():
    app = Flask(__name__)

    required = ("PSQL_HOST", "PSQL_USER", "PSQL_PASSWORD")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        logging.warning("Missing database env vars: %s", ", ".join(missing))

    init_auth(app)

    from .routes import bp as main_bp

    app.register_blueprint(main_bp)
    return app
