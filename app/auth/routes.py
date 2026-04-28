import re
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from app.database import db
from app.Models.models import Cliente, Usuario, Empleado, Rol
from werkzeug.security import generate_password_hash, check_password_hash
from app.services.email_service import enviar_codigo_verificacion, enviar_codigo_reset
from .helpers import verificar_contrasenia, generar_token, log_login_exitoso, log_login_fallido, log_cuenta_inactiva
from .decorators import get_usuario_actual, jwt_requerido

auth_bp = Blueprint('auth', __name__)
EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

codigos_verificacion: dict = {}
codigos_reset: dict = {}
EXPIRACION_MINUTOS = 15


def _codigo_expirado(registro: dict) -> bool:
    return datetime.utcnow() > registro.get("expira", datetime.utcnow())


# ============================================================
# LOGIN - Distingue cliente de admin
# ============================================================
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

        usuario = Usuario.query.filter_by(correo=correo).first()
        if not usuario:
            log_login_fallido("correo no existe", correo, ip_cliente)
            return jsonify({"success": False, "error": "Correo o contraseña incorrectos"}), 401

        if not usuario.estado:
            log_cuenta_inactiva(correo, ip_cliente)
            return jsonify({"success": False, "error": "Cuenta inactiva"}), 403

        if not check_password_hash(usuario.contrasenia, contrasenia):
            log_login_fallido("contraseña incorrecta", correo, ip_cliente)
            return jsonify({"success": False, "error": "Correo o contraseña incorrectos"}), 401

        # CRÍTICO: Determinar tipo de usuario
        es_cliente = False
        nombre_completo = ""
        permisos = []
        rol_nombre = None
        empleado_id = None

        if usuario.empleado_id and usuario.rol_id:
            # Empleado administrativo
            empleado = usuario.empleado
            nombre_completo = f"{empleado.nombre} {empleado.apellido}"
            permisos = [p.nombre for p in usuario.rol.permisos] if usuario.rol.permisos else []
            rol_nombre = usuario.rol.nombre
            empleado_id = empleado.id
            es_cliente = False
        elif usuario.cliente_id:
            # Cliente registrado (sin rol)
            cliente = usuario.cliente
            nombre_completo = f"{cliente.nombre} {cliente.apellido}"
            permisos = []
            rol_nombre = None
            es_cliente = True
        else:
            return jsonify({"success": False, "error": "Configuración de usuario inválida"}), 401

        token = generar_token(usuario, permisos, rol_nombre, nombre_completo, es_cliente, empleado_id)
        log_login_exitoso(usuario.id, rol_nombre or "cliente", ip_cliente)

        return jsonify({
            "success": True,
            "token": token,
            "usuario": {
                "id": usuario.id,
                "nombre": nombre_completo,
                "correo": usuario.correo,
                "rol": rol_nombre,
                "es_admin": not es_cliente,
                "es_cliente": es_cliente,
                "permisos": permisos
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": "Error interno"}), 500


# ============================================================
# REGISTRO - Crea Cliente + Usuario (sin rol)
# ============================================================
@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Datos requeridos"}), 400

        required = ['nombre', 'apellido', 'correo', 'contrasenia', 'numeroDocumento', 'fechaNacimiento']
        for field in required:
            if not data.get(field):
                return jsonify({"success": False, "error": f"Campo {field} requerido"}), 400

        correo = data['correo'].strip().lower()
        if not EMAIL_REGEX.match(correo):
            return jsonify({"success": False, "error": "Correo inválido"}), 400

        if len(data['contrasenia']) < 6:
            return jsonify({"success": False, "error": "Contraseña mínimo 6 caracteres"}), 400

        if Usuario.query.filter_by(correo=correo).first():
            return jsonify({"success": False, "error": "Correo ya registrado"}), 400

        codigo = str(secrets.randbelow(900000) + 100000)
        codigos_verificacion[correo] = {
            "codigo": codigo,
            "data": data,
            "expira": datetime.utcnow() + timedelta(minutes=EXPIRACION_MINUTOS)
        }

        enviado = enviar_codigo_verificacion(correo, f"{data['nombre']} {data['apellido']}", codigo)
        if not enviado:
            del codigos_verificacion[correo]
            return jsonify({"success": False, "error": "No se pudo enviar el código"}), 500

        return jsonify({"success": True, "message": "Código enviado"}), 200

    except Exception as e:
        return jsonify({"success": False, "error": "Error interno"}), 500


# ============================================================
# VERIFY REGISTER - Crea Cliente + Usuario (CRÍTICO)
# ============================================================
@auth_bp.route('/verify-register', methods=['POST'])
def verify_register():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Datos requeridos"}), 400

        correo = data.get('correo', '').strip().lower()
        codigo = data.get('codigo', '').strip()

        if correo not in codigos_verificacion:
            return jsonify({"success": False, "error": "No hay registro pendiente"}), 400

        registro = codigos_verificacion[correo]
        if _codigo_expirado(registro):
            del codigos_verificacion[correo]
            return jsonify({"success": False, "error": "Código expirado"}), 400

        if registro['codigo'] != codigo:
            return jsonify({"success": False, "error": "Código incorrecto"}), 400

        form = registro['data']

        # CRÍTICO: Crear Cliente
        cliente = Cliente(
            nombre=form['nombre'].strip(),
            apellido=form['apellido'].strip(),
            correo=correo,
            numero_documento=str(form['numeroDocumento']).strip(),
            tipo_documento=form.get('tipoDocumento', 'CC'),
            fecha_nacimiento=datetime.strptime(form['fechaNacimiento'], '%Y-%m-%d').date(),
            telefono=form.get('telefono', ''),
            genero=form.get('genero', ''),
            direccion=form.get('direccion', ''),
            departamento=form.get('departamento', ''),
            municipio=form.get('municipio', ''),
            barrio=form.get('barrio', ''),
            codigo_postal=form.get('codigoPostal', ''),
            ocupacion=form.get('ocupacion', ''),
            telefono_emergencia=form.get('telefonoEmergencia', ''),
            estado=True
        )
        db.session.add(cliente)
        db.session.flush()

        # CRÍTICO: Crear Usuario SIN rol (rol_id = NULL)
        usuario = Usuario(
            correo=correo,
            contrasenia=generate_password_hash(form['contrasenia']),
            rol_id=None,           # Cliente NO tiene rol
            cliente_id=cliente.id,
            empleado_id=None,
            estado=True
        )
        db.session.add(usuario)
        db.session.commit()

        del codigos_verificacion[correo]

        # CRÍTICO: Generar JWT para el cliente
        nombre_completo = f"{cliente.nombre} {cliente.apellido}"
        token = generar_token(usuario, [], None, nombre_completo, es_cliente=True, empleado_id=None)

        return jsonify({
            "success": True,
            "message": "Cliente registrado exitosamente",
            "token": token,
            "usuario": {
                "id": usuario.id,
                "nombre": nombre_completo,
                "correo": usuario.correo,
                "es_cliente": True,
                "cliente_id": cliente.id
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Error: {str(e)}"}), 500


# ============================================================
# RECUPERACIÓN DE CONTRASEÑA (solo para admins)
# ============================================================
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json(silent=True)
        correo = data.get('correo', '').strip().lower() if data else ''

        if not correo or not EMAIL_REGEX.match(correo):
            return jsonify({"success": False, "error": "Correo inválido"}), 400

        usuario = Usuario.query.filter_by(correo=correo).first()
        respuesta = {"success": True, "message": "Si el correo existe, recibirás un código"}

        if not usuario or not usuario.empleado_id:
            return jsonify(respuesta), 200

        empleado = usuario.empleado
        codigo = str(secrets.randbelow(900000) + 100000)
        codigos_reset[correo] = {
            "codigo": codigo,
            "usuario_id": usuario.id,
            "expira": datetime.utcnow() + timedelta(minutes=EXPIRACION_MINUTOS)
        }

        enviado = enviar_codigo_reset(correo, f"{empleado.nombre} {empleado.apellido}", codigo)
        if not enviado:
            del codigos_reset[correo]

        return jsonify(respuesta), 200

    except Exception:
        return jsonify({"success": False, "error": "Error interno"}), 500


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Datos requeridos"}), 400

        correo = data.get('correo', '').strip().lower()
        codigo = data.get('codigo', '').strip()
        nueva = data.get('nueva_contrasenia', '')

        if not all([correo, codigo, nueva]) or len(nueva) < 6:
            return jsonify({"success": False, "error": "Datos inválidos"}), 400

        if correo not in codigos_reset:
            return jsonify({"success": False, "error": "No hay solicitud pendiente"}), 400

        reset = codigos_reset[correo]
        if _codigo_expirado(reset):
            del codigos_reset[correo]
            return jsonify({"success": False, "error": "Código expirado"}), 400

        if reset['codigo'] != codigo:
            return jsonify({"success": False, "error": "Código incorrecto"}), 400

        usuario = Usuario.query.get(reset['usuario_id'])
        if not usuario:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404

        usuario.contrasenia = generate_password_hash(nueva)
        db.session.commit()
        del codigos_reset[correo]

        return jsonify({"success": True, "message": "Contraseña actualizada"}), 200

    except Exception:
        db.session.rollback()
        return jsonify({"success": False, "error": "Error interno"}), 500


# ============================================================
# LOGOUT Y ME
# ============================================================
@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({"success": True, "message": "Sesión cerrada"}), 200


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
            "permisos": claims.get("permisos", []),
            "es_cliente": claims.get("es_cliente", False)
        }
    }), 200