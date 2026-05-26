"""
Decoradores para control de acceso basado en JWT, roles y permisos.
Todos utilizan g.usuario_actual cargado por el middleware de autenticación.
"""

from functools import wraps
from flask import jsonify, g
import os

AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"

def jwt_requerido(f):
    """Requiere que el usuario esté autenticado (token válido)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not AUTH_ENABLED:
            return f(*args, **kwargs)
        if not g.token_valido or g.usuario_actual is None:
            return jsonify({
                "success": False,
                "error": "Token requerido o inválido",
                "message": "Debes iniciar sesión para acceder a este recurso"
            }), 401
        return f(*args, **kwargs)
    return decorated

def rol_requerido(*roles_permitidos):
    """Requiere que el usuario tenga al menos uno de los roles especificados."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not AUTH_ENABLED:
                return f(*args, **kwargs)
            if not g.token_valido or g.usuario_actual is None:
                return jsonify({
                    "success": False,
                    "error": "Token requerido",
                    "message": "Debes iniciar sesión"
                }), 401
            rol_usuario = g.usuario_actual.get('rol', '').lower()
            if rol_usuario not in [r.lower() for r in roles_permitidos]:
                return jsonify({
                    "success": False,
                    "error": "Acceso denegado",
                    "message": f"No tienes el rol necesario. Requerido: {', '.join(roles_permitidos)}"
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def permiso_requerido(permiso: str):
    """Requiere que el usuario tenga un permiso específico (ej: 'ver_usuarios')."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not AUTH_ENABLED:
                return f(*args, **kwargs)
            if not g.token_valido or g.usuario_actual is None:
                return jsonify({
                    "success": False,
                    "error": "Token requerido",
                    "message": "Debes iniciar sesión"
                }), 401
            permisos = g.usuario_actual.get('permisos', [])
            if permiso not in permisos:
                return jsonify({
                    "success": False,
                    "error": "Permiso insuficiente",
                    "message": f"No tienes el permiso '{permiso}' para acceder a este recurso."
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def requiere_empleado(f):
    """Requiere que el usuario NO sea cliente (es decir, tenga rol de empleado/admin)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not AUTH_ENABLED:
            return f(*args, **kwargs)
        if not g.token_valido or g.usuario_actual is None:
            return jsonify({
                "success": False,
                "error": "Token requerido",
                "message": "Debes iniciar sesión"
            }), 401
        if g.usuario_actual.get('es_cliente', True):
            return jsonify({
                "success": False,
                "error": "Acceso denegado",
                "message": "Esta ruta solo es accesible para empleados del sistema"
            }), 403
        return f(*args, **kwargs)
    return decorated

def get_usuario_actual() -> dict:
    """Retorna los claims del usuario autenticado (desde g)."""
    return g.usuario_actual or {}