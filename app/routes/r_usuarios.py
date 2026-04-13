from flask import jsonify, request
from app.database import db
from app.Models.models import Usuario, Rol
from app.auth.decorators import jwt_requerido, permiso_requerido, get_usuario_actual
from werkzeug.security import generate_password_hash, check_password_hash
from app.routes import main_bp
import re

EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


# ============================================================
# CUALQUIER USUARIO AUTENTICADO (con permiso 'configuracion')
# ============================================================

@main_bp.route('/usuario/perfil', methods=['GET'])
@jwt_requerido
def get_mi_perfil_usuario():
    """Cualquier usuario autenticado ve su propio perfil"""
    try:
        claims = get_usuario_actual()
        usuario_id = claims.get('id')
        
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        return jsonify({
            "id": usuario.id,
            "nombre": usuario.nombre,
            "correo": usuario.correo,
            "rol_id": usuario.rol_id,
            "rol_nombre": usuario.rol.nombre if usuario.rol else None,
            "permisos": claims.get('permisos', []),
            "telefono": usuario.telefono,
            "estado": usuario.estado
        })
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500


@main_bp.route('/usuario/perfil', methods=['PUT'])
@jwt_requerido
def update_mi_perfil_usuario():
    """Usuario edita su propia información"""
    try:
        claims = get_usuario_actual()
        usuario_id = claims.get('id')
        
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        data = request.get_json()
        
        if 'nombre' in data:
            usuario.nombre = data['nombre'].strip()
        if 'telefono' in data:
            usuario.telefono = data['telefono'].strip() if data['telefono'] else None
        
        db.session.commit()
        return jsonify({"success": True, "message": "Perfil actualizado"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error: {str(e)}"}), 500


@main_bp.route('/usuario/cambiar-contrasenia', methods=['POST'])
@jwt_requerido
def cambiar_mi_contrasenia_usuario():
    """Usuario cambia su propia contraseña"""
    try:
        claims = get_usuario_actual()
        usuario_id = claims.get('id')
        
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        data = request.get_json()
        
        if not check_password_hash(usuario.contrasenia, data.get('contrasenia_actual', '')):
            return jsonify({"error": "Contraseña actual incorrecta"}), 401
        
        nueva_contrasenia = data.get('nueva_contrasenia', '')
        if len(nueva_contrasenia) < 6:
            return jsonify({"error": "La nueva contraseña debe tener al menos 6 caracteres"}), 400
        
        usuario.contrasenia = generate_password_hash(nueva_contrasenia)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Contraseña actualizada"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error: {str(e)}"}), 500


# ============================================================
# SOLO USUARIOS CON PERMISO 'usuarios' (Admin, Dev, etc.)
# ============================================================

@main_bp.route('/admin/usuarios', methods=['GET'])
@permiso_requerido('usuarios')
def get_usuarios():
    """Listar usuarios - requiere permiso 'usuarios'"""
    try:
        usuarios = Usuario.query.all()
        return jsonify([u.to_dict() for u in usuarios])
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500


@main_bp.route('/admin/usuarios', methods=['POST'])
@permiso_requerido('usuarios')
def create_usuario():
    """Crear usuario - requiere permiso 'usuarios'"""
    try:
        data = request.get_json()
        
        required_fields = ['nombre', 'correo', 'contrasenia', 'rol_id']
        for field in required_fields:
            if field not in data:
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
        
        contrasenia_hash = generate_password_hash(data['contrasenia'])
        
        usuario = Usuario(
            nombre=data['nombre'],
            correo=correo,
            contrasenia=contrasenia_hash,
            rol_id=data['rol_id'],
            estado=data.get('estado', True),
            telefono=data.get('telefono'),
            cliente_id=data.get('cliente_id')
        )
        
        db.session.add(usuario)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Usuario creado", "usuario": usuario.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error: {str(e)}"}), 500


@main_bp.route('/admin/usuarios/<int:id>', methods=['GET'])
@permiso_requerido('usuarios')
def get_usuario(id):
    """Ver usuario específico - requiere permiso 'usuarios'"""
    try:
        usuario = Usuario.query.get(id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify(usuario.to_dict())
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500


@main_bp.route('/admin/usuarios/<int:id>', methods=['PUT'])
@permiso_requerido('usuarios')
def update_usuario(id):
    """Editar usuario - requiere permiso 'usuarios'"""
    try:
        usuario = Usuario.query.get(id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        data = request.get_json()
        
        if 'nombre' in data:
            usuario.nombre = data['nombre']
        
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
            rol = Rol.query.get(data['rol_id'])
            if not rol:
                return jsonify({"error": "El rol especificado no existe"}), 400
            usuario.rol_id = data['rol_id']
        
        if 'estado' in data:
            usuario.estado = data['estado']
        
        if 'telefono' in data:
            usuario.telefono = data['telefono']
        
        if 'cliente_id' in data:
            usuario.cliente_id = data['cliente_id']
        
        db.session.commit()
        return jsonify({"success": True, "message": "Usuario actualizado", "usuario": usuario.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error: {str(e)}"}), 500


@main_bp.route('/admin/usuarios/<int:id>', methods=['DELETE'])
@permiso_requerido('usuarios')
def delete_usuario(id):
    """Eliminar usuario - requiere permiso 'usuarios'"""
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