"""
Blueprint de autenticación: /auth

Rutas:
    POST /auth/login            → login con JWT
    POST /auth/register         → inicia registro, envía código por Brevo
    POST /auth/verify-register  → verifica código y crea el cliente (SOLO CLIENTE)
    POST /auth/forgot-password  → envía código de recuperación por Brevo
    POST /auth/reset-password   → verifica código y actualiza contraseña
    POST /auth/logout           → cierra sesión (instrucción al frontend)
    GET  /auth/me               → retorna datos del usuario autenticado
"""

import re
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from app.database import db
from app.Models.models import Usuario, Cliente, Empleado, Rol
from app.services.email_service import enviar_codigo_verificacion, enviar_codigo_reset
from .helpers import (
    verificar_contrasenia,
    generar_token,
    log_login_exitoso,
    log_login_fallido,
    log_cuenta_inactiva,
)
from .decorators import get_usuario_actual

auth_bp = Blueprint('auth', __name__)

EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

# Almacenamiento temporal de códigos
codigos_verificacion: dict = {}
codigos_reset: dict = {}

EXPIRACION_MINUTOS = 15


def _codigo_expirado(registro: dict) -> bool:
    return datetime.utcnow() > registro.get("expira", datetime.utcnow())


# =============================================
# POST /auth/login
# =============================================
@auth_bp.route('/login', methods=['POST'])
def login():
    ip_cliente = request.remote_addr

    try:
        data = request.get_json(silent=True)

        if not data or not data.get('correo') or not data.get('contrasenia'):
            return jsonify({"success": False, "error": "Correo y contraseña son requeridos"}), 400

        correo = data['correo'].strip().lower()
        contrasenia = data['contrasenia']

        if not EMAIL_REGEX.match(correo):
            return jsonify({"success": False, "error": "Formato de correo inválido"}), 400

        if len(contrasenia.strip()) < 6:
            return jsonify({"success": False, "error": "La contraseña debe tener al menos 6 caracteres"}), 400

        usuario = Usuario.query.filter_by(correo=correo).first()

        if not usuario:
            log_login_fallido("correo no existe", correo, ip_cliente)
            return jsonify({"success": False, "error": "Correo o contraseña incorrectos"}), 401

        if not usuario.estado:
            log_cuenta_inactiva(correo, ip_cliente)
            return jsonify({"success": False, "error": "Tu cuenta está inactiva. Contacta al administrador."}), 403

        # Verificar contraseña
        contrasenia_valida = verificar_contrasenia(
            contrasenia,
            usuario.contrasenia,
            usuario.id
        )
        if not contrasenia_valida:
            log_login_fallido("contraseña incorrecta", correo, ip_cliente)
            return jsonify({"success": False, "error": "Correo o contraseña incorrectos"}), 401

        # Obtener información según el tipo de usuario
        nombre_rol = "usuario"
        permisos = []
        nombre_completo = ""
        es_cliente = False
        empleado_id = None

        if usuario.rol:
            nombre_rol = usuario.rol.nombre.lower().strip()
            permisos = [p.nombre for p in usuario.rol.permisos]

        # Determinar si es cliente o empleado
        if usuario.empleado_id:
            # Es un empleado con usuario
            empleado = usuario.empleado
            if empleado:
                nombre_completo = f"{empleado.nombre} {empleado.apellido}"
                empleado_id = empleado.id
            es_cliente = False
        else:
            # Es un cliente (tiene cliente_id)
            cliente = Cliente.query.get(usuario.cliente_id) if usuario.cliente_id else None
            if cliente:
                nombre_completo = f"{cliente.nombre} {cliente.apellido}"
            es_cliente = True

        token = generar_token(
            usuario=usuario,
            permisos=permisos,
            nombre_rol=nombre_rol,
            nombre_completo=nombre_completo,
            es_cliente=es_cliente,
            empleado_id=empleado_id
        )
        log_login_exitoso(usuario.id, nombre_rol, ip_cliente)

        return jsonify({
            "success": True,
            "token": token,
            "usuario": {
                "id": usuario.id,
                "nombre": nombre_completo,
                "correo": usuario.correo,
                "rol": nombre_rol,
                "rol_id": usuario.rol_id,
                "permisos": permisos,
                "es_cliente": es_cliente,
                "empleado_id": empleado_id
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": "Error interno del servidor"}), 500


# =============================================
# POST /auth/register - SOLO PARA CLIENTES
# =============================================
@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Cuerpo de la petición inválido"}), 400

        required_fields = ['nombre', 'apellido', 'correo', 'contrasenia', 'numeroDocumento', 'fechaNacimiento']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"success": False, "error": f"El campo '{field}' es requerido"}), 400

        correo = data['correo'].strip().lower()
        nombre = data['nombre'].strip()
        apellido = data['apellido'].strip()

        if not EMAIL_REGEX.match(correo):
            return jsonify({"success": False, "error": "Formato de correo inválido"}), 400

        if len(data['contrasenia']) < 6:
            return jsonify({"success": False, "error": "La contraseña debe tener al menos 6 caracteres"}), 400

        if Usuario.query.filter_by(correo=correo).first():
            return jsonify({"success": False, "error": "El correo ya está registrado"}), 400

        codigo = str(secrets.randbelow(900000) + 100000)
        codigos_verificacion[correo] = {
            "codigo": codigo,
            "data": data,
            "expira": datetime.utcnow() + timedelta(minutes=EXPIRACION_MINUTOS)
        }

        enviado = enviar_codigo_verificacion(
            correo=correo,
            nombre=f"{nombre} {apellido}",
            codigo=codigo
        )

        if not enviado:
            del codigos_verificacion[correo]
            return jsonify({
                "success": False,
                "error": "No se pudo enviar el código. Verifica el correo e intenta de nuevo."
            }), 500

        return jsonify({"success": True, "message": "Código enviado al correo"}), 200

    except Exception as e:
        return jsonify({"success": False, "error": "No se pudo procesar el registro. Intenta de nuevo."}), 500


# =============================================
# POST /auth/verify-register - CREA CLIENTE (NO EMPLEADO)
# =============================================
@auth_bp.route('/verify-register', methods=['POST'])
def verify_register():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Cuerpo de la petición inválido"}), 400

        correo = data.get('correo', '').strip().lower()
        codigo = data.get('codigo', '').strip()

        if not correo or not codigo:
            return jsonify({"success": False, "error": "Correo y código son requeridos"}), 400

        if correo not in codigos_verificacion:
            return jsonify({"success": False, "error": "No hay un registro pendiente para este correo"}), 400

        registro = codigos_verificacion[correo]

        if _codigo_expirado(registro):
            del codigos_verificacion[correo]
            return jsonify({"success": False, "error": "El código ha expirado. Solicita uno nuevo."}), 400

        if registro['codigo'] != codigo:
            return jsonify({"success": False, "error": "Código incorrecto"}), 400

        form_data = registro['data']

        from werkzeug.security import generate_password_hash

        contrasenia_hash = generate_password_hash(form_data['contrasenia'])

        nombre = form_data['nombre'].strip()
        apellido = form_data['apellido'].strip()
        numero_documento = str(form_data['numeroDocumento']).strip()

        # Buscar o crear el rol CLIENTE
        rol_cliente = Rol.query.filter_by(nombre='Cliente').first()
        if not rol_cliente:
            rol_cliente = Rol(
                nombre='Cliente',
                descripcion='Cliente registrado desde landing page',
                estado=True
            )
            db.session.add(rol_cliente)
            db.session.commit()

        # Crear el cliente
        cliente = Cliente(
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            numero_documento=numero_documento,
            tipo_documento=form_data.get('tipoDocumento', 'CC'),
            fecha_nacimiento=datetime.strptime(form_data['fechaNacimiento'], '%Y-%m-%d').date(),
            telefono=form_data.get('telefono', ''),
            estado=True
        )
        db.session.add(cliente)
        db.session.flush()

        # Crear el usuario (SIN empleado_id, SOLO cliente_id)
        usuario = Usuario(
            correo=correo,
            contrasenia=contrasenia_hash,
            rol_id=rol_cliente.id,
            estado=True,
            cliente_id=cliente.id,  # Cliente vinculado
            empleado_id=None         # Cliente NO tiene empleado
        )
        db.session.add(usuario)
        db.session.commit()

        del codigos_verificacion[correo]

        return jsonify({"success": True, "message": "Cuenta creada exitosamente. Ya puedes iniciar sesión."}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": "No se pudo crear la cuenta. Intenta de nuevo."}), 500


# =============================================
# POST /auth/forgot-password
# =============================================
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json(silent=True)
        correo = (data.get('correo', '') if data else '').strip().lower()

        if not correo or not EMAIL_REGEX.match(correo):
            return jsonify({"success": False, "error": "Correo inválido"}), 400

        usuario = Usuario.query.filter_by(correo=correo).first()
        RESPUESTA_GENERICA = {"success": True, "message": "Si el correo existe, recibirás un código"}

        if not usuario:
            return jsonify(RESPUESTA_GENERICA), 200

        codigo = str(secrets.randbelow(900000) + 100000)
        
        # Obtener nombre para el correo
        nombre_usuario = ""
        if usuario.empleado_id and usuario.empleado:
            nombre_usuario = f"{usuario.empleado.nombre} {usuario.empleado.apellido}"
        elif usuario.cliente_id:
            cliente = Cliente.query.get(usuario.cliente_id)
            if cliente:
                nombre_usuario = f"{cliente.nombre} {cliente.apellido}"
        
        codigos_reset[correo] = {
            "codigo": codigo,
            "usuario_id": usuario.id,
            "expira": datetime.utcnow() + timedelta(minutes=EXPIRACION_MINUTOS)
        }

        enviado = enviar_codigo_reset(
            correo=correo,
            nombre=nombre_usuario,
            codigo=codigo
        )

        if not enviado:
            del codigos_reset[correo]
            return jsonify({"success": False, "error": "No se pudo enviar el código. Intenta de nuevo."}), 500

        return jsonify(RESPUESTA_GENERICA), 200

    except Exception:
        return jsonify({"success": False, "error": "No se pudo procesar la solicitud. Intenta de nuevo."}), 500


# =============================================
# POST /auth/reset-password
# =============================================
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Cuerpo de la petición inválido"}), 400

        correo = data.get('correo', '').strip().lower()
        codigo = data.get('codigo', '').strip()
        nueva_contrasenia = data.get('nueva_contrasenia', '')

        if not all([correo, codigo, nueva_contrasenia]):
            return jsonify({"success": False, "error": "Todos los campos son requeridos"}), 400

        if len(nueva_contrasenia) < 6:
            return jsonify({"success": False, "error": "La contraseña debe tener al menos 6 caracteres"}), 400

        if correo not in codigos_reset:
            return jsonify({"success": False, "error": "No hay una solicitud de recuperación para este correo"}), 400

        reset = codigos_reset[correo]

        if _codigo_expirado(reset):
            del codigos_reset[correo]
            return jsonify({"success": False, "error": "El código ha expirado. Solicita uno nuevo."}), 400

        if reset['codigo'] != codigo:
            return jsonify({"success": False, "error": "Código incorrecto"}), 400

        from werkzeug.security import generate_password_hash
        usuario = Usuario.query.get(reset['usuario_id'])
        if not usuario:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404

        usuario.contrasenia = generate_password_hash(nueva_contrasenia)
        db.session.commit()

        del codigos_reset[correo]

        return jsonify({"success": True, "message": "Contraseña actualizada correctamente"}), 200

    except Exception:
        db.session.rollback()
        return jsonify({"success": False, "error": "No se pudo actualizar la contraseña. Intenta de nuevo."}), 500


# =============================================
# POST /auth/logout
# =============================================
@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({
        "success": True,
        "message": "Sesión cerrada correctamente"
    }), 200


# =============================================
# GET /auth/me
# =============================================
@auth_bp.route('/me', methods=['GET'])
def me():
    claims = get_usuario_actual()
    return jsonify({
        "success": True,
        "usuario": {
            "id": claims.get("id"),
            "nombre": claims.get("nombre"),
            "correo": claims.get("correo"),
            "rol": claims.get("rol"),
            "rol_id": claims.get("rol_id"),
            "permisos": claims.get("permisos", []),
            "es_cliente": claims.get("es_cliente", False),
            "empleado_id": claims.get("empleado_id")
        }
    }), 200