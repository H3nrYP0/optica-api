from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def jwt_requerido(f):
    """Verifica que el token JWT sea válido"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({
                "success": False,
                "error": "Token requerido o inválido"
            }), 401
        return f(*args, **kwargs)
    return decorated

def rol_requerido(*roles_permitidos):
    """Verifica que el usuario tenga uno de los roles permitidos"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                rol_usuario = claims.get('rol', '')

                if rol_usuario not in roles_permitidos:
                    return jsonify({
                        "success": False,
                        "error": "No tienes permisos para realizar esta acción"
                    }), 403
            except Exception:
                return jsonify({
                    "success": False,
                    "error": "Token requerido o inválido"
                }), 401
            return f(*args, **kwargs)
        return decorated
    return decorator

def permiso_requerido(permiso):
    """Verifica que el usuario tenga un permiso específico"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                permisos_usuario = claims.get('permisos', [])

                if permiso not in permisos_usuario:
                    return jsonify({
                        "success": False,
                        "error": f"Permiso requerido: {permiso}"
                    }), 403
            except Exception:
                return jsonify({
                    "success": False,
                    "error": "Token requerido o inválido"
                }), 401
            return f(*args, **kwargs)
        return decorated
    return decorator