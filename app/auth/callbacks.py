from flask import jsonify
from flask_jwt_extended import JWTManager

jwt = JWTManager()


def init_callbacks(app):
    """
    Registra todos los callbacks de error de JWT en la app Flask.
    Llamar una sola vez desde init_auth(app).
    """
    jwt.init_app(app)

    # ── Sin token en la petición ──────────────────────────────
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({
            "success": False,
            "error": "Token requerido",
            "message": "Debes iniciar sesión para acceder a este recurso"
        }), 401

    # ── Token con formato incorrecto ──────────────────────────
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            "success": False,
            "error": "Token inválido",
            "message": "El token no tiene el formato correcto"
        }), 401

    # ── Token expirado ────────────────────────────────────────
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({
            "success": False,
            "error": "Token expirado",
            "message": "Tu sesión ha expirado, inicia sesión nuevamente"
        }), 401

    # ── Token revocado (blacklist futura) ─────────────────────
    # Cuando implementes logout con blacklist, este callback
    # devolverá 401 automáticamente para tokens revocados.
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_data):
        return jsonify({
            "success": False,
            "error": "Token revocado",
            "message": "Tu sesión fue cerrada. Inicia sesión nuevamente"
        }), 401


    # ── Tipo de token incorrecto (ej: refresh en lugar de access) ──
    #@jwt.wrong_token_type_loader
    #def wrong_token_type_callback(error):
        return jsonify({
            "success": False,
            "error": "Tipo de token incorrecto",
            "message": "El tipo de token enviado no es válido para este endpoint"
        }), 422