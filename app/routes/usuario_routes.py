from flask import Blueprint, jsonify, request
from app.database import db
from app.models import Usuario, Rol, Cliente
from app.auth.decorators import jwt_requerido, rol_requerido
from datetime import datetime
import re

usuario_bp = Blueprint('usuarios', __name__)
EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
ROLES_CRITICOS = ['admin', 'superadmin']


# ── Listar todos (solo con token) ────────────────────────────────────────────
@usuario_bp.route('', methods=['GET'])
@jwt_requerido
def get_usuarios():
    try:
        return jsonify([u.to_dict() for u in Usuario.query.all()])
    except Exception as e:
        return jsonify({"error": f"Error al obtener usuarios: {str(e)}"}), 500


# ── GET individual (solo con token) ─────────────────────────────────────────
@usuario_bp.route('/<int:id>', methods=['GET'])
@jwt_requerido
def get_usuario(id):
    try:
        usuario = Usuario.query.get(id)
        if not usuario:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
        return jsonify({"success": True, "usuario": usuario.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── GET completo con datos de cliente (solo con token) ───────────────────────
@usuario_bp.route('/<int:id>/completo', methods=['GET'])
@jwt_requerido
def get_usuario_completo(id):
    try:
        usuario = Usuario.query.get(id)
        if not usuario:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
        respuesta = {"usuario": usuario.to_dict(), "cliente": None}
        if usuario.cliente_id:
            cliente = Cliente.query.get(usuario.cliente_id)
            if cliente:
                respuesta["cliente"] = cliente.to_dict()
        return jsonify({"success": True, "data": respuesta})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── GET por email — sin token (usado por recuperación de contraseña) ─────────
@usuario_bp.route('/email/<string:email>', methods=['GET'])
def get_usuario_por_email(email):
    try:
        usuario = Usuario.query.filter_by(correo=email.strip().lower()).first()
        if not usuario:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
        return jsonify({
            "success": True,
            "usuario": {
                "id": usuario.id,
                "nombre": usuario.nombre,
                "correo": usuario.correo,
                "rol_id": usuario.rol_id,
                "cliente_id": usuario.cliente_id
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── Crear usuario (POST público para clientes; admins requieren token) ────────
# El registro de clientes lo hace /auth/register (con verificación de email).
# Este endpoint lo usa el panel admin para crear empleados/admins.
@usuario_bp.route('', methods=['POST'])
@rol_requerido('admin', 'superadmin')
def create_usuario():
    try:
        data = request.get_json()
        required = ['nombre', 'correo', 'contrasenia', 'rol_id']
        for field in required:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        correo = data['correo'].strip().lower()
        if not EMAIL_REGEX.match(correo):
            return jsonify({"error": "Formato de correo inválido"}), 400
        if len(data['contrasenia']) < 6:
            return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400
        if Usuario.query.filter_by(correo=correo).first():
            return jsonify({"success": False, "error": "El correo ya está registrado"}), 400

        rol = Rol.query.get(data['rol_id'])
        if not rol:
            return jsonify({"error": "El rol especificado no existe"}), 400
        if not rol.estado:
            return jsonify({"error": "No puedes asignar un rol inactivo"}), 400

        from werkzeug.security import generate_password_hash
        contrasenia_hash = generate_password_hash(data['contrasenia'])
        cliente_id = None

        # Si es rol cliente (id 2), crear también el registro en tabla cliente
        if data['rol_id'] == 2:
            nombre_parts = data['nombre'].split(' ', 1)
            cliente = Cliente(
                nombre=nombre_parts[0],
                apellido=nombre_parts[1] if len(nombre_parts) > 1 else '',
                correo=correo,
                numero_documento=data.get('numero_documento', 'PENDIENTE'),
                fecha_nacimiento=data.get('fecha_nacimiento', datetime.now().date()),
                genero=data.get('genero'),
                telefono=data.get('telefono'),
                municipio=data.get('municipio'),
                direccion=data.get('direccion'),
                ocupacion=data.get('ocupacion'),
                telefono_emergencia=data.get('telefono_emergencia'),
                estado=True
            )
            db.session.add(cliente)
            db.session.flush()
            cliente_id = cliente.id

        usuario = Usuario(
            nombre=data['nombre'],
            correo=correo,
            contrasenia=contrasenia_hash,
            rol_id=data['rol_id'],
            estado=data.get('estado', True),
            cliente_id=cliente_id
        )
        db.session.add(usuario)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Usuario creado exitosamente",
            "usuario": usuario.to_dict(),
            "cliente_id": cliente_id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Error al crear usuario: {str(e)}"}), 500


# ── Actualizar (solo admin) ──────────────────────────────────────────────────
@usuario_bp.route('/<int:id>', methods=['PUT'])
@rol_requerido('admin', 'superadmin')
def update_usuario(id):
    try:
        usuario = Usuario.query.get(id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        data = request.get_json()

        if 'correo' in data:
            correo = data['correo'].strip().lower()
            if not EMAIL_REGEX.match(correo):
                return jsonify({"error": "Formato de correo inválido"}), 400
            existente = Usuario.query.filter_by(correo=correo).first()
            if existente and existente.id != id:
                return jsonify({"error": "El correo ya está registrado"}), 400
            usuario.correo = correo

        if 'nombre' in data: usuario.nombre = data['nombre']
        if 'contrasenia' in data:
            if len(data['contrasenia']) < 6:
                return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400
            from werkzeug.security import generate_password_hash
            usuario.contrasenia = generate_password_hash(data['contrasenia'])
        if 'rol_id' in data:
            rol = Rol.query.get(data['rol_id'])
            if not rol or not rol.estado:
                return jsonify({"error": "Rol inválido o inactivo"}), 400
            usuario.rol_id = data['rol_id']
        if 'estado' in data: usuario.estado = data['estado']

        db.session.commit()
        return jsonify({"message": "Usuario actualizado", "usuario": usuario.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar usuario"}), 500


# ── Eliminar (solo admin, usuario debe estar inactivo) ───────────────────────
@usuario_bp.route('/<int:id>', methods=['DELETE'])
@rol_requerido('admin', 'superadmin')
def delete_usuario(id):
    try:
        usuario = Usuario.query.get(id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        if usuario.estado:
            return jsonify({"error": "Debes desactivar el usuario antes de eliminarlo"}), 400
        db.session.delete(usuario)
        db.session.commit()
        return jsonify({"message": "Usuario eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar usuario"}), 500
