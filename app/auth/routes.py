from flask import Blueprint, jsonify, request
import re

from app.database import db
from app.models import Usuario
from .helpers import (
    verificar_contrasenia,
    generar_token,
    log_login_exitoso,
    log_login_fallido,
    log_cuenta_inactiva
)

auth_bp = Blueprint('auth', __name__)

# ── Regex para validar formato de correo ──
EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

# =============================================
# POST /auth/login
# Recibe: { "correo": "...", "contrasenia": "..." }
# Devuelve: { "token": "...", "usuario": { ... } }
# =============================================
@auth_bp.route('/login', methods=['POST'])
def login():
    ip_cliente = request.remote_addr

    try:
        data = request.get_json()

        # ── Validar campos requeridos ──
        if not data or not data.get('correo') or not data.get('contrasenia'):
            return jsonify({
                "success": False,
                "error": "Correo y contraseña son requeridos"
            }), 400

        correo = data['correo'].strip().lower()
        contrasenia = data['contrasenia']

        # ── Validar formato de correo ──
        if not EMAIL_REGEX.match(correo):
            return jsonify({
                "success": False,
                "error": "Formato de correo inválido"
            }), 400

        # ── Validar longitud mínima de contraseña ──
        if len(contrasenia.strip()) < 6:
            return jsonify({
                "success": False,
                "error": "La contraseña debe tener al menos 6 caracteres"
            }), 400

        # ── Buscar usuario por correo ──
        usuario = Usuario.query.filter_by(correo=correo).first()

        if not usuario:
            log_login_fallido("correo no existe", correo, ip_cliente)
            # Mensaje genérico — no revelar si el correo existe o no
            return jsonify({
                "success": False,
                "error": "Correo o contraseña incorrectos"
            }), 401

        # ── Verificar cuenta activa ──
        if not usuario.estado:
            log_cuenta_inactiva(correo, ip_cliente)
            return jsonify({
                "success": False,
                "error": "Tu cuenta está inactiva. Contacta al administrador."
            }), 403

        # ── Verificar contraseña ──
        contrasenia_valida = verificar_contrasenia(
            contrasenia,
            usuario.contrasenia,
            usuario.id,
            db
        )

        if not contrasenia_valida:
            log_login_fallido("contraseña incorrecta", correo, ip_cliente)
            return jsonify({
                "success": False,
                "error": "Correo o contraseña incorrectos"
            }), 401

        # ── Obtener rol y permisos ──
        permisos = []
        nombre_rol = "usuario"

        if usuario.rol:
            nombre_rol = usuario.rol.nombre.lower()
            permisos = [p.nombre for p in usuario.rol.permisos]

        # ── Generar JWT ──
        token = generar_token(usuario, permisos, nombre_rol)

        log_login_exitoso(usuario.id, nombre_rol, ip_cliente)

        return jsonify({
            "success": True,
            "token": token,
            "usuario": {
                "id": usuario.id,
                "nombre": usuario.nombre,
                "correo": usuario.correo,
                "rol": nombre_rol,
                "rol_id": usuario.rol_id,
                "permisos": permisos,
            }
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Error interno del servidor"
        }), 500