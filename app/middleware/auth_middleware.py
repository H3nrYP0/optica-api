"""
Middleware de autenticación: intenta cargar el usuario desde el JWT
y lo guarda en flask.g.usuario_actual.
NUNCA rechaza una petición, solo deja disponible la información.
"""

from flask import g, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
import logging

logger = logging.getLogger(__name__)

def cargar_usuario_desde_token():
    """
    Carga los claims del usuario autenticado en g.usuario_actual.
    Si no hay token o es inválido, g.usuario_actual = None.
    """
    g.usuario_actual = None
    g.token_valido = False

    if request.method == 'OPTIONS':
        return

    try:
        # optional=True evita excepciones si no hay token
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        claims = get_jwt()
        if identity and claims:
            g.usuario_actual = {
                'id': claims.get('id'),
                'nombre': claims.get('nombre'),
                'correo': claims.get('correo'),
                'rol': claims.get('rol'),
                'rol_id': claims.get('rol_id'),
                'permisos': claims.get('permisos', []),
                'es_cliente': claims.get('es_cliente', True),
                'cliente_id': claims.get('cliente_id'),
                'empleado_id': claims.get('empleado_id')
            }
            g.token_valido = True
            logger.debug(f"Usuario autenticado: {g.usuario_actual['correo']}")
    except Exception as e:
        logger.debug(f"Token inválido o ausente: {e}")