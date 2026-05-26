"""
Módulo de middlewares de la aplicación.
Actualmente solo contiene el middleware de autenticación.
"""

from .auth_middleware import cargar_usuario_desde_token

__all__ = ['cargar_usuario_desde_token']