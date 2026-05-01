"""
Blueprint de autenticación: /auth

Rutas:
    POST /auth/login            → login con JWT
    POST /auth/register         → inicia registro, envía código por Brevo
    POST /auth/verify-register  → verifica código y crea el cliente + usuario (con rol Cliente)
    POST /auth/forgot-password  → envía código de recuperación por Brevo (solo para usuarios con rol)
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
from .decorators import get_usuario_actual, jwt_requerido

auth_bp = Blueprint('auth', __name__)

EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

# Almacenamiento temporal de códigos en memoria RAM.
codigos_verificacion: dict = {}
codigos_reset: dict = {}

EXPIRACION_MINUTOS = 15


def _codigo_expirado(registro: dict) -> bool:
    return datetime.utcnow() > registro.get("expira", datetime.utcnow())


def _obtener_rol_cliente():
    """Retorna el objeto Rol correspondiente a 'Cliente' o None si no existe."""
    return Rol.query.filter_by(nombre='Cliente').first()


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

        # ============================================================
        # NUEVA LÓGICA UNIFICADA (SIN empleado_id)
        # ============================================================
        nombre_completo = f"{usuario.nombre or ''} {usuario.apellido or ''}".strip()
        if not nombre_completo:
            nombre_completo = usuario.correo

        permisos = []
        rol_nombre = None
        if usuario.rol:
            rol_nombre = usuario.rol.nombre
            permisos = [p.nombre for p in usuario.rol.permisos] if usuario.rol.permisos else []

        # Determinar si es cliente (por nombre de rol)
        es_cliente = (rol_nombre == 'Cliente')

        token = generar_token(
            usuario=usuario,
            permisos=permisos,
            nombre_rol=rol_nombre,
            nombre_completo=nombre_completo,
            es_cliente=es_cliente,
            empleado_id=None   # Ya no se usa, pero se mantiene por compatibilidad
        )
        log_login_exitoso(usuario.id, rol_nombre or "cliente", ip_cliente)

        return jsonify({
            "success": True,
            "token": token,
            "usuario": {
                "id": usuario.id,
                "nombre": nombre_completo,
                "correo": usuario.correo,
                "rol": rol_nombre,
                "rol_id": usuario.rol_id,
                "permisos": permisos,
                "es_cliente": es_cliente
                # empleado_id omitido
            }
        }), 200

    except Exception as e:
        # Para depuración, puedes imprimir el error real
        # print(f"Error en login: {str(e)}")
        return jsonify({"success": False, "error": "Error interno del servidor"}), 500


# =============================================
# POST /auth/register - Registro de CLIENTE
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
# POST /auth/verify-register - CREA CLIENTE + USUARIO (CON ROL CLIENTE)
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

        # ============================================================
        # 1. CREAR CLIENTE
        # ============================================================
        cliente = Cliente(
            nombre=form_data['nombre'].strip(),
            apellido=form_data['apellido'].strip(),
            correo=correo,
            numero_documento=str(form_data['numeroDocumento']).strip(),
            tipo_documento=form_data.get('tipoDocumento', 'CC'),
            fecha_nacimiento=datetime.strptime(form_data['fechaNacimiento'], '%Y-%m-%d').date(),
            telefono=form_data.get('telefono', ''),
            genero=form_data.get('genero', ''),
            direccion=form_data.get('direccion', ''),
            departamento=form_data.get('departamento', ''),
            municipio=form_data.get('municipio', ''),
            barrio=form_data.get('barrio', ''),
            codigo_postal=form_data.get('codigoPostal', ''),
            ocupacion=form_data.get('ocupacion', ''),
            telefono_emergencia=form_data.get('telefonoEmergencia', ''),
            estado=True
        )
        db.session.add(cliente)
        db.session.flush()  # Para obtener el ID del cliente

        # ============================================================
        # 2. CREAR USUARIO CON ROL "Cliente"
        # ============================================================
        rol_cliente = _obtener_rol_cliente()
        if not rol_cliente:
            # Si por algún motivo no existe el rol Cliente, se puede crear automáticamente
            # o lanzar un error. Por seguridad, lo creamos.
            rol_cliente = Rol(nombre='Cliente', descripcion='Rol para clientes registrados', estado=True)
            db.session.add(rol_cliente)
            db.session.flush()

        usuario = Usuario(
            correo=correo,
            contrasenia=generate_password_hash(form_data['contrasenia']),
            rol_id=rol_cliente.id,
            estado=True,
            cliente_id=cliente.id
        )
        # Guardar datos personales directamente en usuario
        usuario.nombre = form_data['nombre'].strip()
        usuario.apellido = form_data['apellido'].strip()
        usuario.telefono = form_data.get('telefono', '')
        usuario.tipo_documento = form_data.get('tipoDocumento', 'CC')
        usuario.numero_documento = str(form_data['numeroDocumento']).strip()
        try:
            usuario.fecha_nacimiento = datetime.strptime(form_data['fechaNacimiento'], '%Y-%m-%d').date()
        except:
            usuario.fecha_nacimiento = None

        db.session.add(usuario)
        db.session.commit()

        # Limpiar código
        del codigos_verificacion[correo]

        # ============================================================
        # 3. GENERAR JWT PARA EL CLIENTE
        # ============================================================
        nombre_completo = f"{cliente.nombre} {cliente.apellido}"
        token = generar_token(
            usuario=usuario,
            permisos=[],   # El rol Cliente no tiene permisos por defecto
            nombre_rol='Cliente',
            nombre_completo=nombre_completo,
            es_cliente=True,
            empleado_id=None
        )

        return jsonify({
            "success": True,
            "message": "Cliente registrado exitosamente",
            "token": token,
            "usuario": {
                "id": usuario.id,
                "nombre": nombre_completo,
                "correo": usuario.correo,
                "rol": "Cliente",
                "rol_id": usuario.rol_id,
                "permisos": [],
                "es_cliente": True,
                "cliente_id": cliente.id
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"No se pudo crear el cliente: {str(e)}"}), 500


# =============================================
# POST /auth/forgot-password (solo para usuarios con rol, no clientes)
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

        # Solo permitir recuperación a usuarios que tienen rol (administrativos)
        # Si quieres permitir también a clientes, cambia esta condición.
        if usuario.rol_id is None:
            return jsonify(RESPUESTA_GENERICA), 200

        # Generar código
        codigo = str(secrets.randbelow(900000) + 100000)
        codigos_reset[correo] = {
            "codigo": codigo,
            "usuario_id": usuario.id,
            "expira": datetime.utcnow() + timedelta(minutes=EXPIRACION_MINUTOS)
        }

        # Obtener nombre completo desde los campos directos
        nombre_completo = f"{usuario.nombre or ''} {usuario.apellido or ''}".strip()
        if not nombre_completo:
            nombre_completo = usuario.correo

        enviado = enviar_codigo_reset(
            correo=correo,
            nombre=nombre_completo,
            codigo=codigo
        )

        if not enviado:
            del codigos_reset[correo]

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
@jwt_requerido
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
            "es_cliente": claims.get("es_cliente", False)
            # empleado_id ya no se incluye
        }
    }), 200