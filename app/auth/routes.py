from flask import Blueprint, jsonify, request
from flask_mail import Message
import re
import secrets

from app.database import db
from app.models import Usuario, Cliente
from app.auth import mail
from .helpers import (
    verificar_contrasenia,
    generar_token,
    log_login_exitoso,
    log_login_fallido,
    log_cuenta_inactiva
)

auth_bp = Blueprint('auth', __name__)

EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

# Almacenamiento temporal de códigos (en memoria)
codigos_verificacion = {}
codigos_reset = {}

# =============================================
# POST /auth/login
# =============================================
@auth_bp.route('/login', methods=['POST'])
def login():
    ip_cliente = request.remote_addr

    try:
        data = request.get_json()

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

        contrasenia_valida = verificar_contrasenia(
            contrasenia,
            usuario.contrasenia,
            usuario.id,
            db
        )

        if not contrasenia_valida:
            log_login_fallido("contraseña incorrecta", correo, ip_cliente)
            return jsonify({"success": False, "error": "Correo o contraseña incorrectos"}), 401

        permisos = []
        nombre_rol = "usuario"

        if usuario.rol:
            nombre_rol = usuario.rol.nombre.lower()
            permisos = [p.nombre for p in usuario.rol.permisos]

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
        return jsonify({"success": False, "error": "Error interno del servidor"}), 500


# =============================================
# POST /auth/register
# Envía código de verificación al correo
# =============================================
@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()

        required_fields = ['nombre', 'correo', 'contrasenia', 'numeroDocumento', 'fechaNacimiento']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"success": False, "error": f"El campo {field} es requerido"}), 400

        correo = data['correo'].strip().lower()

        if not EMAIL_REGEX.match(correo):
            return jsonify({"success": False, "error": "Formato de correo inválido"}), 400

        if len(data['contrasenia']) < 6:
            return jsonify({"success": False, "error": "La contraseña debe tener al menos 6 caracteres"}), 400

        if Usuario.query.filter_by(correo=correo).first():
            return jsonify({"success": False, "error": "El correo ya está registrado"}), 400

        # Generar código de 6 dígitos y guardar datos temporalmente
        codigo = str(secrets.randbelow(900000) + 100000)
        codigos_verificacion[correo] = {
            "codigo": codigo,
            "data": data
        }

        msg = Message(
            subject="Código de verificación - Visual Outlet",
            sender="eyessetting@gmail.com",
            recipients=[correo]
        )
        msg.body = (
            f"Hola {data['nombre']},\n\n"
            f"Tu código de verificación es: {codigo}\n\n"
            f"Si no solicitaste este registro, ignora este mensaje.\n\n"
            f"Visual Outlet"
        )
        mail.send(msg)

        return jsonify({"success": True, "message": "Código enviado al correo"}), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Error al enviar código: {str(e)}"}), 500


# =============================================
# POST /auth/verify-register
# Verifica código y crea el usuario
# =============================================
@auth_bp.route('/verify-register', methods=['POST'])
def verify_register():
    try:
        data = request.get_json()
        correo = data.get('correo', '').strip().lower()
        codigo = data.get('codigo', '')

        if correo not in codigos_verificacion:
            return jsonify({"success": False, "error": "No hay un registro pendiente para este correo"}), 400

        registro = codigos_verificacion[correo]

        if registro['codigo'] != codigo:
            return jsonify({"success": False, "error": "Código incorrecto"}), 400

        form_data = registro['data']

        from werkzeug.security import generate_password_hash
        from datetime import datetime

        contrasenia_hash = generate_password_hash(form_data['contrasenia'])

        # Crear cliente asociado
        nombre_parts = form_data['nombre'].split(' ', 1)
        primer_nombre = nombre_parts[0]
        apellido = nombre_parts[1] if len(nombre_parts) > 1 else ''

        cliente = Cliente(
            nombre=primer_nombre,
            apellido=apellido,
            correo=correo,
            numero_documento=form_data['numeroDocumento'],
            tipo_documento=form_data.get('tipoDocumento', 'CC'),
            fecha_nacimiento=datetime.strptime(form_data['fechaNacimiento'], '%Y-%m-%d').date(),
            telefono=form_data.get('telefono'),
            estado=True
        )
        db.session.add(cliente)
        db.session.flush()

        # Crear usuario con rol_id=2 (cliente)
        usuario = Usuario(
            nombre=form_data['nombre'],
            correo=correo,
            contrasenia=contrasenia_hash,
            rol_id=2,
            estado=True,
            cliente_id=cliente.id
        )
        db.session.add(usuario)
        db.session.commit()

        del codigos_verificacion[correo]

        return jsonify({"success": True, "message": "Cuenta creada exitosamente"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Error al crear usuario: {str(e)}"}), 500


# =============================================
# POST /auth/forgot-password
# Envía código de recuperación al correo
# =============================================
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        correo = data.get('correo', '').strip().lower()

        if not correo or not EMAIL_REGEX.match(correo):
            return jsonify({"success": False, "error": "Correo inválido"}), 400

        usuario = Usuario.query.filter_by(correo=correo).first()

        # Respuesta genérica para no revelar si el correo existe
        if not usuario:
            return jsonify({"success": True, "message": "Si el correo existe, recibirás un código"}), 200

        codigo = str(secrets.randbelow(900000) + 100000)
        codigos_reset[correo] = {
            "codigo": codigo,
            "usuario_id": usuario.id
        }

        msg = Message(
            subject="Recuperar contraseña - Visual Outlet",
            sender="eyessetting@gmail.com",
            recipients=[correo]
        )
        msg.body = (
            f"Hola {usuario.nombre},\n\n"
            f"Tu código para restablecer tu contraseña es: {codigo}\n\n"
            f"Si no solicitaste este cambio, ignora este mensaje.\n\n"
            f"Visual Outlet"
        )
        mail.send(msg)

        return jsonify({"success": True, "message": "Si el correo existe, recibirás un código"}), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Error al enviar correo: {str(e)}"}), 500


# =============================================
# POST /auth/reset-password
# Verifica código y actualiza contraseña
# =============================================
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        correo = data.get('correo', '').strip().lower()
        codigo = data.get('codigo', '')
        nueva_contrasenia = data.get('nueva_contrasenia', '')

        if not all([correo, codigo, nueva_contrasenia]):
            return jsonify({"success": False, "error": "Todos los campos son requeridos"}), 400

        if len(nueva_contrasenia) < 6:
            return jsonify({"success": False, "error": "La contraseña debe tener al menos 6 caracteres"}), 400

        if correo not in codigos_reset:
            return jsonify({"success": False, "error": "No hay una solicitud de recuperación para este correo"}), 400

        reset = codigos_reset[correo]

        if reset['codigo'] != codigo:
            return jsonify({"success": False, "error": "Código incorrecto"}), 400

        from werkzeug.security import generate_password_hash
        usuario = Usuario.query.get(reset['usuario_id'])
        usuario.contrasenia = generate_password_hash(nueva_contrasenia)
        db.session.commit()

        del codigos_reset[correo]

        return jsonify({"success": True, "message": "Contraseña actualizada correctamente"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Error al actualizar contraseña: {str(e)}"}), 500