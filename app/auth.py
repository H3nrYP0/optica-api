from flask import jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from app.database import db
from app.models import Usuario

jwt = JWTManager()

def init_auth(app):
    jwt.init_app(app)

@jwt.user_identity_loader
def user_identity_lookup(usuario):
    return usuario.id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return Usuario.query.get(identity)

@jwt.unauthorized_loader
def unauthorized_callback(error):
    return jsonify({
        "error": "Token requerido",
        "message": "Debes iniciar sesión para acceder a este recurso"
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        "error": "Token inválido",
        "message": "El token proporcionado no es válido"
    }), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_data):
    return jsonify({
        "error": "Token expirado",
        "message": "El token ha expirado, inicia sesión nuevamente"
    }), 401