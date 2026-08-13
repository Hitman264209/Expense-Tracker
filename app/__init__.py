"""
Application factory for the Expense Tracker Flask app.
"""

from pathlib import Path

from flask import Flask

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "templates"),
        static_folder=str(PROJECT_ROOT / "static"),
    )

    from .routes import api
    app.register_blueprint(api)

    return app
