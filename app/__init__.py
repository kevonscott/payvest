import os
import warnings
from flask import Flask
import secrets


def create_app() -> Flask:
    """Application factory for the payvest app."""
    app = Flask(__name__, static_folder="static", template_folder="templates")
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        # Warn in logs for development, but do not use in production
        warnings.warn(
            "SECRET_KEY not set in environment; generating a random key for "
            "development. Sessions and CSRF tokens will be invalidated on "
            "each restart. Set SECRET_KEY for production."
        )
        secret_key = secrets.token_hex(32)
    app.config.from_mapping(
        SECRET_KEY=secret_key,
    )

    # Register blueprints/routes
    from .routes import bp as main_bp

    app.register_blueprint(main_bp)

    return app
