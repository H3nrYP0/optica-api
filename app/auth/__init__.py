from app import mail
from .routes import auth_bp
from .callbacks import init_callbacks

def init_auth(app):
    """Inicializa el módulo de autenticación"""
    # Registrar callbacks de JWT (errores, expiración, etc.)
    init_callbacks(app)
    # Registrar blueprint con prefijo /auth
    app.register_blueprint(auth_bp, url_prefix="/auth")