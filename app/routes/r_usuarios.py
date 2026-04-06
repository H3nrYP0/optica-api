from flask import Blueprint, jsonify, request
from app.database import db
from app.models import Usuario, Rol, Permiso
from app.auth.decorators import jwt_requerido, rol_requerido
import re

# Definición del Blueprint
main_bp = Blueprint('acceso', __name__)

# Configuración de seguridad
ROLES_CRITICOS = ['admin', 'superadmin']
EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

# GESTIÓN DE ROLES 

@main_bp.route('/roles', methods=['GET'])
@jwt_requerido
def get_roles():
    try: 
        roles = Rol.query.all()
        return jsonify([rol.to_dict() for rol in roles]), 200
    except Exception as e:
        return jsonify({"error": "Error al obtener roles"}), 500

@main_bp.route('/roles', methods=['POST'])
@rol_requerido('admin', 'superadmin')
def create_rol():
    try:
        data = request.get_json()
        if not data or not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400

        nombre = data['nombre'].strip()
        if nombre.lower() in ROLES_CRITICOS:
            return jsonify({"error": "No puedes crear un rol con ese nombre"}), 403

        if Rol.query.filter_by(nombre=nombre).first():
            return jsonify({"error": "Ya existe un rol con ese nombre"}), 400

        # Lógica de permisos al crear
        permisos_ids = data.get('permisos', [])
        permisos = []
        if permisos_ids:
            permisos = Permiso.query.filter(Permiso.id.in_(permisos_ids)).all()
        
        rol = Rol(
            nombre=nombre,
            descripcion=data.get('descripcion', '').strip(),
            estado=data.get('estado', True)
        )
        rol.permisos = permisos
        db.session.add(rol)
        db.session.commit()
        return jsonify({"message": "Rol creado", "rol": rol.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear rol"}), 500

# (Aquí irían tus rutas PUT y DELETE de roles que ya tienes...)

# ==============================================================================
# SECCIÓN 2: GESTIÓN DE USUARIOS
# ==============================================================================

@main_bp.route('/usuarios', methods=['GET'])
@jwt_requerido
def get_usuarios():
    """Lista todos los usuarios con su información de rol."""
    try:
        usuarios = Usuario.query.all()
        return jsonify([u.to_dict() for u in usuarios]), 200
    except Exception as e:
        return jsonify({"error": "Error al obtener usuarios"}), 500

@main_bp.route('/usuarios', methods=['POST'])
@rol_requerido('admin', 'superadmin')
def create_usuario():
    """Crea un nuevo usuario con validaciones de correo y duplicados."""
    try:
        data = request.get_json()
        
        # Validaciones de campos obligatorios
        if not all(k in data for k in ('nombre', 'correo', 'contrasenia', 'rol_id')):
            return jsonify({"error": "Faltan datos obligatorios"}), 400

        correo = data['correo'].strip().lower()
        
        # Validar formato de email
        if not EMAIL_REGEX.match(correo):
            return jsonify({"error": "Formato de correo inválido"}), 400

        # Validar duplicados
        if Usuario.query.filter_by(correo=correo).first():
            return jsonify({"error": "Este correo ya está registrado"}), 400

        # Validar existencia del rol
        if not Rol.query.get(data['rol_id']):
            return jsonify({"error": "El rol especificado no existe"}), 404

        nuevo_usuario = Usuario(
            nombre=data['nombre'].strip(),
            correo=correo,
            contrasenia=data['contrasenia'], # Nota: Aplicar hash en el modelo/auth
            rol_id=data['rol_id'],
            estado=data.get('estado', True)
        )

        db.session.add(nuevo_usuario)
        db.session.commit()
        return jsonify({"message": "Usuario creado", "usuario": nuevo_usuario.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear usuario"}), 500

@main_bp.route('/usuarios/<int:id>', methods=['PUT'])
@rol_requerido('admin', 'superadmin')
def update_usuario(id):
    """Actualiza datos de usuario, permitiendo cambiar rol o estado."""
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
                return jsonify({"error": "Correo inválido"}), 400
            existente = Usuario.query.filter_by(correo=correo).first()
            if existente and existente.id != id:
                return jsonify({"error": "El correo ya está en uso"}), 400
            usuario.correo = correo

        if 'rol_id' in data:
            if not Rol.query.get(data['rol_id']):
                return jsonify({"error": "Rol no existe"}), 404
            usuario.rol_id = data['rol_id']

        if 'estado' in data:
            usuario.estado = bool(data['estado'])

        db.session.commit()
        return jsonify({"message": "Usuario actualizado", "usuario": usuario.to_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar usuario"}), 500

# GESTIÓN DE PERMISOS 

@main_bp.route('/permisos', methods=['GET'])
@jwt_requerido
def get_permisos():
    """Obtiene el catálogo de todos los permisos definidos en el sistema."""
    try:
        permisos = Permiso.query.all()
        return jsonify([p.to_dict() for p in permisos]), 200
    except Exception as e:
        return jsonify({"error": "Error al obtener catálogo de permisos"}), 500