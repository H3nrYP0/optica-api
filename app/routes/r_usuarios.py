from flask import jsonify, request
from app.database import db
from app.Models.models import Usuario, Rol, Empleado
from app.auth.decorators import permiso_requerido, get_usuario_actual
from werkzeug.security import generate_password_hash, check_password_hash
from app.routes import main_bp
import re

EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


# ============================================================
# PERFIL PROPIO — cualquier usuario autenticado
# ============================================================

@main_bp.route('/usuario/perfil', methods=['GET'])
def get_mi_perfil_usuario():
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
            "empleado": usuario.empleado.to_dict() if usuario.empleado else None
        })
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500


@main_bp.route('/usuario/cambiar-contrasenia', methods=['POST'])
def cambiar_mi_contrasenia_usuario():
    try:
        claims = get_usuario_actual()
        usuario = Usuario.query.get(claims.get('id'))
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        data = request.get_json()
        if not check_password_hash(usuario.contrasenia, data.get('contrasenia_actual', '')):
            return jsonify({"error": "Contraseña actual incorrecta"}), 401

        nueva = data.get('nueva_contrasenia', '')
        if len(nueva) < 6:
            return jsonify({"error": "La nueva contraseña debe tener al menos 6 caracteres"}), 400

        usuario.contrasenia = generate_password_hash(nueva)
        db.session.commit()
        return jsonify({"success": True, "message": "Contraseña actualizada"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error: {str(e)}"}), 500


# ============================================================
# ADMINISTRACIÓN — requiere permiso 'usuarios'
# ============================================================

@main_bp.route('/admin/usuarios', methods=['GET'])
@permiso_requerido("usuarios")
def get_usuarios():
    try:
        usuarios = Usuario.query.all()
        return jsonify([u.to_dict() for u in usuarios])
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500


@main_bp.route('/admin/usuarios', methods=['POST'])
@permiso_requerido("usuarios")
def create_usuario():
    """
    Crea un usuario de acceso al sistema.
    Campos requeridos: correo, contrasenia, rol_id
    Campos opcionales: estado, empleado_id
    Regla: si el rol NO es 'Cliente', empleado_id es obligatorio.
    """
    try:
        data = request.get_json()

        # Campos mínimos obligatorios
        for field in ['correo', 'contrasenia', 'rol_id']:
            if not data.get(field):
                return jsonify({"error": f"El campo '{field}' es requerido"}), 400

        correo = data['correo'].strip().lower()
        if not EMAIL_REGEX.match(correo):
            return jsonify({"error": "Formato de correo inválido"}), 400

        if len(data['contrasenia']) < 6:
            return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

        if Usuario.query.filter_by(correo=correo).first():
            return jsonify({"error": "El correo ya está registrado"}), 400

        rol = Rol.query.get(data['rol_id'])
        if not rol:
            return jsonify({"error": "El rol especificado no existe"}), 400

        # Si el rol no es Cliente, debe tener empleado vinculado
        empleado_id = data.get('empleado_id')
        es_cliente = rol.nombre.lower() == 'cliente'

        if not es_cliente and not empleado_id:
            return jsonify({
                "error": "Los usuarios administradores deben tener un empleado vinculado (empleado_id).",
                "codigo": "EMPLEADO_REQUERIDO"
            }), 400

        if empleado_id:
            empleado = Empleado.query.get(empleado_id)
            if not empleado:
                return jsonify({"error": f"No existe un empleado con ID {empleado_id}"}), 400
            if empleado.usuario:
                return jsonify({
                    "error": f"El empleado '{empleado.nombre} {empleado.apellido}' ya tiene un usuario asignado.",
                    "codigo": "EMPLEADO_YA_TIENE_USUARIO"
                }), 400

        usuario = Usuario(
            correo=correo,
            contrasenia=generate_password_hash(data['contrasenia']),
            rol_id=data['rol_id'],
            estado=data.get('estado', True),
            empleado_id=empleado_id
        )

        db.session.add(usuario)
        db.session.commit()
        return jsonify({"success": True, "message": "Usuario creado", "usuario": usuario.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error: {str(e)}"}), 500


@main_bp.route('/admin/usuarios/<int:id>', methods=['GET'])
@permiso_requerido("usuarios")
def get_usuario(id):
    try:
        usuario = Usuario.query.get(id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify(usuario.to_dict())
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500


@main_bp.route('/admin/usuarios/<int:id>', methods=['PUT'])
@permiso_requerido("usuarios")
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

        if 'contrasenia' in data and data['contrasenia']:
            if len(data['contrasenia']) < 6:
                return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400
            usuario.contrasenia = generate_password_hash(data['contrasenia'])

        if 'rol_id' in data:
            if not Rol.query.get(data['rol_id']):
                return jsonify({"error": "El rol especificado no existe"}), 400
            usuario.rol_id = data['rol_id']

        if 'empleado_id' in data:
            nuevo_emp_id = data['empleado_id']
            if nuevo_emp_id:
                empleado = Empleado.query.get(nuevo_emp_id)
                if not empleado:
                    return jsonify({"error": f"No existe un empleado con ID {nuevo_emp_id}"}), 400
                # Verificar que no esté ya asignado a otro usuario
                if empleado.usuario and empleado.usuario.id != id:
                    return jsonify({
                        "error": f"El empleado '{empleado.nombre} {empleado.apellido}' ya tiene otro usuario asignado.",
                        "codigo": "EMPLEADO_YA_TIENE_USUARIO"
                    }), 400
            usuario.empleado_id = nuevo_emp_id

        if 'estado' in data:
            usuario.estado = data['estado']

        db.session.commit()
        return jsonify({"success": True, "message": "Usuario actualizado", "usuario": usuario.to_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error: {str(e)}"}), 500


@main_bp.route('/admin/usuarios/<int:id>', methods=['DELETE'])
@permiso_requerido("usuarios")
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
        return jsonify({"error": f"Error: {str(e)}"}), 500