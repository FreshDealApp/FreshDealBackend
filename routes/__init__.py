from .auth.login import login_bp
from .auth.register import register_bp


def init_app(app):
    # Version 1 Blueprints
    app.register_blueprint(login_bp, url_prefix='/v1/')
    app.register_blueprint(register_bp, url_prefix='/v1/')
