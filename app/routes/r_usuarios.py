"""
Rutas relacionadas con usuarios (perfil propio y administración).
Los endpoints administrativos usan permisos CRUD granulares.
"""

from flask import jsonify, request
from app.database import db
from app.Models.models import Usuario, Rol, Cliente
from app.auth.decorators import jwt_requerido, permiso_requerido, get_usuario_actual
from werkzeug.security import generate_password_hash, check_password_hash
from app.routes import main_bp
from datetime import datetime
import re

EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
PASSWORD_REGEX = re.compile(r'^(?=.*[A-Z])(?=.*\d).{6,}$')

# ============================================================
# PERFIL PROPIO (cualquier usuario autenticado)
# ============================================================

@main_bp.route('/usuario/perfil', methods=['GET'])
@jwt_requerido
def get_mi_perfil_usuario():
    """Obtener el perfil del usuario autenticado."""
    try:
        claims = get_usuario_actual()
        usuario = Usuario.query.get(claims.get('id'))
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        return jsonify({
            "id": usuario.id,
            "correo": usuario.correo,
            "rol_id": usuario.rol_id,
            "rol_nombre": usuario.rol.nombre if usuario.rol else None,
            "permisos": claims.get('permisos', []),
            "estado": usuario.estado,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "telefono": usuario.telefono,
            "tipo_documento": usuario.tipo_documento,
            "numero_documento": usuario.numero_documento,
            "fecha_nacimiento": usuario.fecha_nacimiento.isoformat() if usuario.fecha_nacimiento else None,
            "cliente": usuario.cliente.to_dict() if usuario.cliente else None
        })
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

@main_bp.route('/usuario/cambiar-contrasenia', methods=['POST'])
@jwt_requerido
def cambiar_mi_contrasenia_usuario():
    """Cambiar la contraseña del usuario autenticado."""
    try:
        claims = get_usuario_actual()
        usuario = Usuario.query.get(claims.get('id'))
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        data = request.get_json()
        if not check_password_hash(usuario.contrasenia, data.get('contrasenia_actual', '')):
            return jsonify({"error": "Contraseña actual incorrecta"}), 401

        nueva = data.get('nueva_contrasenia', '')
        if not PASSWORD_REGEX.match(nueva):
            return jsonify({"error": "La nueva contraseña debe tener al menos 6 caracteres, una mayúscula y un número"}), 400

        usuario.contrasenia = generate_password_hash(nueva)
        db.session.commit()
        return jsonify({"success": True, "message": "Contraseña actualizada"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error: {str(e)}"}), 500

# ============================================================
# ADMINISTRACIÓN DE USUARIOS (permisos CRUD granulares)
# ============================================================

@main_bp.route('/admin/usuarios', methods=['GET'])
@permiso_requerido("ver_usuarios")
def get_usuarios_admin():
    """Listar usuarios administrativos (con rol, excluyendo clientes)."""
    try:
        db.session.expire_all()
        usuarios = Usuario.query.filter(Usuario.rol_id.isnot(None)).all()
        return jsonify([u.to_dict() for u in usuarios])
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

@main_bp.route('/admin/usuarios', methods=['POST'])
@permiso_requerido("crear_usuarios")
def create_usuario_admin():
    """Crear un nuevo usuario administrativo."""
    try:
        data = request.get_json()
        required_fields = ['nombre', 'correo', 'contrasenia', 'rol_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"El campo '{field}' es requerido"}), 400

        correo = data['correo'].strip().lower()
        if not EMAIL_REGEX.match(correo):
            return jsonify({"error": "Formato de correo inválido"}), 400

        contrasenia = data['contrasenia']
        if not PASSWORD_REGEX.match(contrasenia):
            return jsonify({"error": "La contraseña debe tener al menos 6 caracteres, una mayúscula y un número"}), 400

        if Usuario.query.filter_by(correo=correo).first():
            return jsonify({"error": "El correo ya está registrado"}), 400

        rol = Rol.query.get(data['rol_id'])
        if not rol:
            return jsonify({"error": "El rol especificado no existe"}), 400

        usuario = Usuario(
            nombre=data['nombre'].strip(),
            correo=correo,
            contrasenia=generate_password_hash(contrasenia),
            rol_id=rol.id,
            cliente_id=None,
            estado=data.get('estado', True)
        )
        db.session.add(usuario)
        db.session.commit()
        return jsonify({"success": True, "message": "Usuario creado", "usuario": usuario.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error: {str(e)}"}), 500

@main_bp.route('/admin/usuarios/<int:id>', methods=['GET'])
@permiso_requerido("ver_usuarios")
def get_usuario(id):
    """Obtener un usuario administrativo por ID."""
    try:
        db.session.expire_all()
        usuario = Usuario.query.get(id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify(usuario.to_dict())
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

@main_bp.route('/admin/usuarios/<int:id>', methods=['PUT'])
@permiso_requerido("editar_usuarios")
def update_usuario_admin(id):
    """Actualizar un usuario administrativo."""
    try:
        usuario = Usuario.query.get(id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        data = request.get_json()
        if 'nombre' in data:
            usuario.nombre = data['nombre'].strip()
        if 'correo' in data:
            correo = data['correo'].strip().lower()
            if not EMAIL_REGEX.match(correo):
                return jsonify({"error": "Formato de correo inválido"}), 400
            existente = Usuario.query.filter_by(correo=correo).first()
            if existente and existente.id != id:
                return jsonify({"error": "El correo ya está registrado"}), 400
            usuario.correo = correo
        if 'contrasenia' in data and data['contrasenia']:
            if not PASSWORD_REGEX.match(data['contrasenia']):
                return jsonify({"error": "La contraseña debe tener al menos 6 caracteres, una mayúscula y un número"}), 400
            usuario.contrasenia = generate_password_hash(data['contrasenia'])
        if 'rol_id' in data:
            rol = Rol.query.get(data['rol_id'])
            if not rol:
                return jsonify({"error": "El rol especificado no existe"}), 400
            usuario.rol_id = data['rol_id']
        if 'estado' in data:
            usuario.estado = data['estado']

        db.session.commit()
        return jsonify({"success": True, "message": "Usuario actualizado", "usuario": usuario.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error: {str(e)}"}), 500

@main_bp.route('/admin/usuarios/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_usuarios")
def delete_usuario_admin(id):
    """Eliminar un usuario (solo si ya está desactivado)."""
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
        return jsonify({"error": f"Error: {str(e)}"}), 500
 
# ============================================================
# PERFIL UNIFICADO (usuario + cliente)
# ============================================================

@main_bp.route('/mi-perfil', methods=['GET'])
@jwt_requerido
def get_mi_perfil():
    """Obtiene los datos del usuario autenticado y su cliente asociado (si existe)."""
    try:
        claims = get_usuario_actual()
        usuario = Usuario.query.get(claims['id'])
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        cliente = None
        if usuario.cliente_id:
            cliente = Cliente.query.get(usuario.cliente_id)

        return jsonify({
            "usuario": usuario.to_dict(),
            "cliente": cliente.to_dict() if cliente else None
        })
    except Exception as e:
        return jsonify({"error": f"Error al obtener perfil: {str(e)}"}), 500


@main_bp.route('/mi-perfil', methods=['PUT'])
@jwt_requerido
def update_mi_perfil():
    """Actualiza los datos del usuario y/o cliente asociado."""
    try:
        claims = get_usuario_actual()
        usuario = Usuario.query.get(claims['id'])
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        data = request.get_json()
        usuario_data = data.get('usuario', {})
        cliente_data = data.get('cliente')  # puede ser None

        # ========== 1. Actualizar campos de Usuario ==========
        for field in ['nombre', 'apellido', 'tipo_documento', 'numero_documento', 'telefono', 'foto_url']:
            if field in usuario_data:
                value = usuario_data[field]
                setattr(usuario, field, value.strip() if value else None)

        if 'fecha_nacimiento' in usuario_data:
            fecha_str = usuario_data['fecha_nacimiento']
            if fecha_str:
                try:
                    usuario.fecha_nacimiento = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
            else:
                usuario.fecha_nacimiento = None

        # ========== 2. Manejar Cliente (si se envió la sección 'cliente') ==========
        if cliente_data is not None:
            # Si no tiene cliente_id, crear un nuevo cliente con los datos actuales del usuario
            if not usuario.cliente_id:
                nuevo_cliente = Cliente(
                    tipo_documento=usuario.tipo_documento,
                    numero_documento=usuario.numero_documento,
                    nombre=usuario.nombre,
                    apellido=usuario.apellido,
                    telefono=usuario.telefono,
                    correo=usuario.correo,
                    fecha_nacimiento=usuario.fecha_nacimiento,
                    estado=True
                )
                db.session.add(nuevo_cliente)
                db.session.flush()
                usuario.cliente_id = nuevo_cliente.id
                cliente = nuevo_cliente
            else:
                cliente = Cliente.query.get(usuario.cliente_id)

            # Actualizar campos específicos del cliente (los que no están en Usuario)
            for field in ['municipio', 'direccion', 'barrio', 'codigo_postal',
                          'ocupacion', 'telefono_emergencia', 'departamento']:
                if field in cliente_data:
                    value = cliente_data[field]
                    setattr(cliente, field, value.strip() if value else None)

        db.session.commit()

        # Retornar perfil actualizado
        cliente_actualizado = Cliente.query.get(usuario.cliente_id) if usuario.cliente_id else None
        return jsonify({
            "success": True,
            "message": "Perfil actualizado correctamente",
            "usuario": usuario.to_dict(),
            "cliente": cliente_actualizado.to_dict() if cliente_actualizado else None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar perfil: {str(e)}"}), 500