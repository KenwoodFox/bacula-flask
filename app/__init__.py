import os
import logging
import subprocess

from flask import Flask


def create_app():
    app = Flask(__name__)

    # Import and register routes
    from .routes import bp as main_bp

    app.register_blueprint(main_bp)

    if os.getenv("GIT_COMMIT"):
        # Setup/load templates
        subprocess.run("cd templates && ./inject.sh", shell=True)
    else:
        logging.warn("NOT applying production template!")

    return app
