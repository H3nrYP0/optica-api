from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Rol, Permiso, Usuario
from optica_app.auth.decorators import jwt_requerido, rol_requerido

rol_bp = Blueprint('roles', __name__)
ROLES_CRITICOS = ['admin', 'superadmin']

@rol_bp.route('', methods=['GET'])
@jwt_requerido
def get_roles():
    try:
        return jsonify([r.to_dict() for r in Rol.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener roles"}), 500

@rol_bp.route('', methods=['POST'])
@rol_requerido('admin', 'superadmin')
def create_rol():
    try:
        data = request.get_json()
        if not data or not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400
        nombre = data['nombre'].strip()
        if len(nombre) < 3 or len(nombre) > 25:
            return jsonify({"error": "El nombre debe tener entre 3 y 25 caracteres"}), 400
        if nombre.lower() in ROLES_CRITICOS:
            return jsonify({"error": "No puedes crear un rol con ese nombre"}), 403
        if Rol.query.filter_by(nombre=nombre).first():
            return jsonify({"error": "Ya existe un rol con ese nombre"}), 400

        permisos_ids = data.get('permisos', [])
        permisos = Permiso.query.filter(Permiso.id.in_(permisos_ids)).all() if permisos_ids else []
        if len(permisos) != len(permisos_ids):
            return jsonify({"error": "Uno o más permisos no existen"}), 400

        estado = data.get('estado', True)
        if isinstance(estado, str):
            estado = estado == "activo"

        rol = Rol(nombre=nombre, descripcion=data.get('descripcion', '').strip(), estado=estado)
        rol.permisos = permisos
        db.session.add(rol)
        db.session.commit()
        return jsonify({"message": "Rol creado", "rol": rol.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear rol"}), 500

@rol_bp.route('/<int:id>', methods=['PUT'])
@rol_requerido('admin', 'superadmin')
def update_rol(id):
    try:
        rol = Rol.query.get(id)
        if not rol:
            return jsonify({"error": "Rol no encontrado"}), 404
        if rol.nombre.lower() in ROLES_CRITICOS:
            return jsonify({"error": "No puedes modificar este rol"}), 403
        data = request.get_json()

        if 'nombre' in data:
            nombre = data['nombre'].strip()
            if len(nombre) < 3 or len(nombre) > 25:
                return jsonify({"error": "El nombre debe tener entre 3 y 25 caracteres"}), 400
            existente = Rol.query.filter_by(nombre=nombre).first()
            if existente and existente.id != id:
                return jsonify({"error": "Ya existe un rol con ese nombre"}), 400
            rol.nombre = nombre

        if 'descripcion' in data: rol.descripcion = data['descripcion'].strip()
        if 'estado' in data:
            nuevo_estado = data['estado']
            if isinstance(nuevo_estado, str):
                nuevo_estado = nuevo_estado == "activo"
            if not nuevo_estado:
                activos = Usuario.query.filter_by(rol_id=id, estado=True).count()
                if activos > 0:
                    return jsonify({"error": f"No puedes desactivar este rol: tiene {activos} usuario(s) activo(s)"}), 400
            rol.estado = nuevo_estado

        if 'permisos' in data:
            permisos_ids = list(set(data['permisos']))
            permisos = Permiso.query.filter(Permiso.id.in_(permisos_ids)).all() if permisos_ids else []
            if len(permisos) != len(permisos_ids):
                return jsonify({"error": "Uno o más permisos no existen"}), 400
            rol.permisos = permisos

        db.session.commit()
        return jsonify({"message": "Rol actualizado", "rol": rol.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar rol"}), 500

@rol_bp.route('/<int:id>', methods=['DELETE'])
@rol_requerido('admin', 'superadmin')
def delete_rol(id):
    try:
        rol = Rol.query.get(id)
        if not rol:
            return jsonify({"error": "Rol no encontrado"}), 404
        if rol.nombre.lower() in ROLES_CRITICOS:
            return jsonify({"error": "No puedes eliminar este rol"}), 403
        if rol.estado:
            return jsonify({"error": "Debes desactivar el rol antes de eliminarlo"}), 400
        if Usuario.query.filter_by(rol_id=id).count() > 0:
            return jsonify({"error": "No puedes eliminar este rol: tiene usuarios asignados"}), 400
        db.session.delete(rol)
        db.session.commit()
        return jsonify({"message": "Rol eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar rol"}), 500