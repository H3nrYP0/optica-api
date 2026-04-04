from .routes import auth_bp
from .callbacks import init_callbacks


def init_auth(app):
    """Inicializa el módulo de autenticación"""
    init_callbacks(app)
    app.register_blueprint(auth_bp, url_prefix="/auth")


