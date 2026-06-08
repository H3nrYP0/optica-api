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

MAX_PER_PAGE = 10

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
    """
    Listar usuarios administrativos con paginación y filtros opcionales.

    Query params opcionales:
        page      (int)  – página actual, default 1
        per_page  (int)  – registros por página, máx 10
        search    (str)  – busca en nombre, apellido y correo
        rol_id    (int)  – filtra por rol
        estado    (str)  – 'true' | 'false'
    """
    try:
        db.session.expire_all()

        page     = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        search   = request.args.get('search', '', type=str).strip()
        rol_id   = request.args.get('rol_id', type=int)
        estado   = request.args.get('estado', '', type=str)

        query = Usuario.query.options(
            db.joinedload(Usuario.rol)
        ).filter(Usuario.rol_id.isnot(None))

        if rol_id:
            query = query.filter(Usuario.rol_id == rol_id)

        if estado != '':
            estado_bool = estado.lower() == 'true'
            query = query.filter(Usuario.estado == estado_bool)

        if search:
            t = f"%{search}%"
            query = query.filter(
                db.or_(
                    Usuario.nombre.ilike(t),
                    Usuario.apellido.ilike(t),
                    Usuario.correo.ilike(t),
                )
            )

        query = query.order_by(Usuario.nombre.asc())

        # Si no viene 'page' en la URL se devuelve todo (compatible con código anterior)
        if 'page' not in request.args and 'per_page' not in request.args \
                and not search and not rol_id and estado == '':
            usuarios = query.all()
            return jsonify([u.to_dict() for u in usuarios])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        result = []
        for u in pagination.items:
            result.append({
                'id':        u.id,
                'nombre':    u.nombre,
                'apellido':  u.apellido,
                'correo':    u.correo,
                'telefono':  u.telefono,
                'estado':    u.estado,
                'rol_id':    u.rol_id,
                'rol_nombre': u.rol.nombre if u.rol else None,
            })

        return jsonify({
            'data': result,
            'pagination': {
                'current_page': pagination.page,
                'per_page':     per_page,
                'total':        pagination.total,
                'total_pages':  pagination.pages,
                'has_next':     pagination.has_next,
                'has_prev':     pagination.has_prev,
            }
        })
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
# ROLES (paginación y filtros consolidados)
# ============================================================

@main_bp.route('/roles', methods=['GET'])
@permiso_requerido("ver_roles")
def get_roles_admin():
    """
    Listar roles con paginación y filtros opcionales.

    Query params opcionales:
        page      (int)  – página actual, default 1
        per_page  (int)  – registros por página, máx 10
        search    (str)  – busca en nombre
        estado    (str)  – 'true' | 'false'
    """
    try:
        page     = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        search   = request.args.get('search', '', type=str).strip()
        estado   = request.args.get('estado', '', type=str)

        query = Rol.query

        if estado != '' and hasattr(Rol, 'estado'):
            estado_bool = estado.lower() == 'true'
            query = query.filter(Rol.estado == estado_bool)

        if search:
            query = query.filter(Rol.nombre.ilike(f"%{search}%"))

        query = query.order_by(Rol.nombre.asc())

        # Sin parámetros → compatible con código anterior
        if 'page' not in request.args and 'per_page' not in request.args \
                and not search and estado == '':
            roles = query.all()
            return jsonify([r.to_dict() for r in roles])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        result = []
        for r in pagination.items:
            result.append({
                'id':          r.id,
                'nombre':      r.nombre,
                'descripcion': r.descripcion if hasattr(r, 'descripcion') else None,
                'estado':      r.estado if hasattr(r, 'estado') else None,
            })

        return jsonify({
            'data': result,
            'pagination': {
                'current_page': pagination.page,
                'per_page':     per_page,
                'total':        pagination.total,
                'total_pages':  pagination.pages,
                'has_next':     pagination.has_next,
                'has_prev':     pagination.has_prev,
            }
        })
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

# ============================================================
# CLIENTES (paginación y filtros consolidados)
# ============================================================

@main_bp.route('/clientes', methods=['GET'])
@permiso_requerido("ver_clientes")
def get_clientes_admin():
    """
    Listar clientes con paginación y filtros opcionales.

    Query params opcionales:
        page      (int)  – página actual, default 1
        per_page  (int)  – registros por página, máx 10
        search    (str)  – busca en nombre, apellido, correo y número de documento
        estado    (str)  – 'true' | 'false'
    """
    try:
        page     = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        search   = request.args.get('search', '', type=str).strip()
        estado   = request.args.get('estado', '', type=str)

        query = Cliente.query

        if estado != '':
            estado_bool = estado.lower() == 'true'
            query = query.filter(Cliente.estado == estado_bool)

        if search:
            t = f"%{search}%"
            query = query.filter(
                db.or_(
                    Cliente.nombre.ilike(t),
                    Cliente.apellido.ilike(t),
                    Cliente.correo.ilike(t),
                    Cliente.numero_documento.ilike(t),
                )
            )

        query = query.order_by(Cliente.nombre.asc())

        # Sin parámetros → compatible con código anterior
        if 'page' not in request.args and 'per_page' not in request.args \
                and not search and estado == '':
            clientes = query.all()
            return jsonify([c.to_dict() for c in clientes])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'data': [c.to_dict() for c in pagination.items],
            'pagination': {
                'current_page': pagination.page,
                'per_page':     per_page,
                'total':        pagination.total,
                'total_pages':  pagination.pages,
                'has_next':     pagination.has_next,
                'has_prev':     pagination.has_prev,
            }
        })
    except Exception as e:
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

            for field in ['municipio', 'direccion', 'barrio', 'codigo_postal',
                          'ocupacion', 'telefono_emergencia', 'departamento']:
                if field in cliente_data:
                    value = cliente_data[field]
                    setattr(cliente, field, value.strip() if value else None)

        db.session.commit()

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