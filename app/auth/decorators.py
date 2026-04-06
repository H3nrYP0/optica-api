from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def jwt_requerido(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception:
            return jsonify({"success": False, "error": "Sesión inválida"}), 401
    return decorated

def permiso_requerido(modulo):
    """
    Verifica acceso al módulo completo.
    Si el rol es 'dev', ignora la verificación y permite pasar.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                
                # 1. Superusuario Bypass
                if claims.get('rol') == 'dev':
                    return f(*args, **kwargs)

                # 2. Verificación de Módulo
                permisos_usuario = claims.get('permisos', [])
                if modulo not in permisos_usuario:
                    return jsonify({
                        "success": False,
                        "error": f"No tienes acceso al módulo de {modulo}"
                    }), 403
                    
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({"success": False, "error": "Error de permisos", "details": str(e)}), 401
        return decorated
    return decorator