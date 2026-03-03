from flask import jsonify
from flask_jwt_extended import JWTManager

jwt = JWTManager()

def init_callbacks(app):
    """Registra todos los callbacks de JWT en la app"""
    jwt.init_app(app)

    # ── Sin token en la petición ──
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({
            "success": False,
            "error": "Token requerido",
            "message": "Debes iniciar sesión para acceder a este recurso"
        }), 401

    # ── Token mal formado ──
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            "success": False,
            "error": "Token inválido",
            "message": "El token proporcionado no es válido"
        }), 401

    # ── Token expirado (pasaron las 8 horas) ──
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({
            "success": False,
            "error": "Token expirado",
            "message": "Tu sesión ha expirado, inicia sesión nuevamente"
        }), 401