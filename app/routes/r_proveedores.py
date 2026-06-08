"""
Módulo de proveedores: gestión de proveedores (CRUD completo).
Permisos granulares:
- Proveedores: ver_proveedores, crear_proveedores, editar_proveedores, eliminar_proveedores
"""

from flask import jsonify, request
from app.database import db
from app.Models.models import Proveedor, Compra
from app.routes import main_bp
from app.auth.decorators import permiso_requerido
import re

EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
PHONE_REGEX = re.compile(r'^\d{7,15}$')
MAX_PER_PAGE = 10

# ============================================================
# MÓDULO: PROVEEDORES (CRUD)
# ============================================================

@main_bp.route('/proveedores', methods=['GET'])
@permiso_requerido("ver_proveedores")
def get_proveedores():
    """
    Listar proveedores con paginación, búsqueda y filtros.
    Query params:
        page            (int) – página actual
        per_page        (int) – registros por página (máx 10)
        search          (str) – busca en razón social, documento, contacto, correo
        tipo_proveedor  (str) – 'Persona Natural' o 'Persona Jurídica'
        estado          (str) – 'true' o 'false'
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        search = request.args.get('search', '', type=str).strip()
        tipo_proveedor = request.args.get('tipo_proveedor', '', type=str).strip()
        estado = request.args.get('estado', '', type=str).strip().lower()

        query = Proveedor.query

        if tipo_proveedor:
            query = query.filter(Proveedor.tipo_proveedor == tipo_proveedor)
        if estado != '':
            estado_bool = estado == 'true'
            query = query.filter(Proveedor.estado == estado_bool)
        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(
                    Proveedor.razon_social_o_nombre.ilike(like),
                    Proveedor.documento.ilike(like),
                    Proveedor.contacto.ilike(like),
                    Proveedor.correo.ilike(like)
                )
            )
        query = query.order_by(Proveedor.razon_social_o_nombre.asc())

        # Compatibilidad hacia atrás: si no hay parámetros de paginación ni filtros, devolver todo
        has_pagination = 'page' in request.args or 'per_page' in request.args
        has_filters = search or tipo_proveedor or estado != ''
        if not has_pagination and not has_filters:
            proveedores = query.all()
            return jsonify([proveedor.to_dict() for proveedor in proveedores])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [proveedor.to_dict() for proveedor in pagination.items],
            'pagination': {
                'current_page': pagination.page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
        })
    except Exception as e:
        return jsonify({"error": f"Error al obtener proveedores: {str(e)}"}), 500


@main_bp.route('/proveedores', methods=['POST'])
@permiso_requerido("crear_proveedores")
def create_proveedor():
    try:
        data = request.get_json()
        razon_social = data.get('razon_social_o_nombre', '').strip()
        documento = data.get('documento', '').strip()
        if not razon_social:
            return jsonify({"error": "La razón social o nombre del proveedor es requerido"}), 400
        if not documento:
            return jsonify({"error": "El documento (NIT/Cédula) del proveedor es requerido"}), 400
        tipo_proveedor = data.get('tipo_proveedor')
        if tipo_proveedor and tipo_proveedor not in ['Persona Natural', 'Persona Jurídica']:
            return jsonify({"error": "Tipo de proveedor inválido. Opciones: 'Persona Natural' o 'Persona Jurídica'"}), 400
        tipo_documento = data.get('tipo_documento', '').strip()
        if tipo_documento and tipo_documento not in ['CC', 'NIT', 'CE', 'Pasaporte']:
            return jsonify({"error": "Tipo de documento inválido. Opciones: CC, NIT, CE, Pasaporte"}), 400
        if Proveedor.query.filter_by(documento=documento).first():
            return jsonify({"error": f"Ya existe un proveedor con el documento {documento}"}), 400
        correo = data.get('correo', '').strip()
        if correo and not EMAIL_REGEX.match(correo):
            return jsonify({"error": "Formato de correo electrónico inválido"}), 400
        telefono = data.get('telefono', '').strip()
        if telefono and not PHONE_REGEX.match(telefono):
            return jsonify({"error": "El teléfono debe contener solo números (7-15 dígitos)"}), 400
        contacto = data.get('contacto', '').strip()
        if contacto and len(contacto) > 50:
            return jsonify({"error": "El nombre de contacto no puede tener más de 50 caracteres"}), 400
        if len(razon_social) > 100:
            return jsonify({"error": "La razón social no puede tener más de 100 caracteres"}), 400
        if len(documento) > 20:
            return jsonify({"error": "El documento no puede tener más de 20 caracteres"}), 400
        proveedor = Proveedor(
            tipo_proveedor=tipo_proveedor,
            tipo_documento=tipo_documento if tipo_documento else None,
            documento=documento,
            razon_social_o_nombre=razon_social,
            contacto=contacto if contacto else None,
            telefono=telefono if telefono else None,
            correo=correo if correo else None,
            departamento=data.get('departamento', '').strip() or None,
            municipio=data.get('municipio', '').strip() or None,
            direccion=data.get('direccion', '').strip() or None,
            estado=data.get('estado', True)
        )
        db.session.add(proveedor)
        db.session.commit()
        return jsonify({"message": "Proveedor creado", "proveedor": proveedor.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear proveedor: {str(e)}"}), 500


@main_bp.route('/proveedores/<int:id>', methods=['PUT'])
@permiso_requerido("editar_proveedores")
def update_proveedor(id):
    try:
        proveedor = Proveedor.query.get(id)
        if not proveedor:
            return jsonify({"error": "Proveedor no encontrado"}), 404
        data = request.get_json()
        if 'tipo_proveedor' in data:
            tipo = data['tipo_proveedor']
            if tipo and tipo not in ['Persona Natural', 'Persona Jurídica']:
                return jsonify({"error": "Tipo de proveedor inválido. Opciones: 'Persona Natural' o 'Persona Jurídica'"}), 400
            proveedor.tipo_proveedor = tipo
        if 'tipo_documento' in data:
            tipo_doc = data['tipo_documento'].strip() if data['tipo_documento'] else None
            if tipo_doc and tipo_doc not in ['CC', 'NIT', 'CE', 'Pasaporte']:
                return jsonify({"error": "Tipo de documento inválido. Opciones: CC, NIT, CE, Pasaporte"}), 400
            proveedor.tipo_documento = tipo_doc
        if 'documento' in data:
            nuevo_documento = data['documento'].strip()
            if not nuevo_documento:
                return jsonify({"error": "El documento no puede estar vacío"}), 400
            existente = Proveedor.query.filter(Proveedor.documento == nuevo_documento, Proveedor.id != id).first()
            if existente:
                return jsonify({"error": f"Ya existe otro proveedor con el documento {nuevo_documento}"}), 400
            proveedor.documento = nuevo_documento
        if 'razon_social_o_nombre' in data:
            razon = data['razon_social_o_nombre'].strip()
            if not razon:
                return jsonify({"error": "La razón social no puede estar vacía"}), 400
            if len(razon) > 100:
                return jsonify({"error": "La razón social no puede tener más de 100 caracteres"}), 400
            proveedor.razon_social_o_nombre = razon
        if 'contacto' in data:
            contacto = data['contacto'].strip() if data['contacto'] else None
            if contacto and len(contacto) > 50:
                return jsonify({"error": "El nombre de contacto no puede tener más de 50 caracteres"}), 400
            proveedor.contacto = contacto
        if 'correo' in data:
            correo = data['correo'].strip() if data['correo'] else None
            if correo and not EMAIL_REGEX.match(correo):
                return jsonify({"error": "Formato de correo electrónico inválido"}), 400
            proveedor.correo = correo
        if 'telefono' in data:
            telefono = data['telefono'].strip() if data['telefono'] else None
            if telefono and not PHONE_REGEX.match(telefono):
                return jsonify({"error": "El teléfono debe contener solo números (7-15 dígitos)"}), 400
            proveedor.telefono = telefono
        if 'estado' in data and not data['estado']:
            compras_asociadas = Compra.query.filter_by(proveedor_id=id).first()
            if compras_asociadas:
                return jsonify({"error": "No se puede desactivar un proveedor que tiene compras asociadas"}), 400
            proveedor.estado = data['estado']
        elif 'estado' in data:
            proveedor.estado = data['estado']
        if 'departamento' in data:
            proveedor.departamento = data['departamento'].strip() if data['departamento'] else None
        if 'municipio' in data:
            proveedor.municipio = data['municipio'].strip() if data['municipio'] else None
        if 'direccion' in data:
            proveedor.direccion = data['direccion'].strip() if data['direccion'] else None
        db.session.commit()
        return jsonify({"message": "Proveedor actualizado", "proveedor": proveedor.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar proveedor: {str(e)}"}), 500


@main_bp.route('/proveedores/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_proveedores")
def delete_proveedor(id):
    try:
        proveedor = Proveedor.query.get(id)
        if not proveedor:
            return jsonify({"error": "Proveedor no encontrado"}), 404
        compras_asociadas = Compra.query.filter_by(proveedor_id=id).first()
        if compras_asociadas:
            return jsonify({"error": "No se puede eliminar: Este proveedor tiene historial de compras. Desactívelo para ocultarlo."}), 400
        if proveedor.estado:
            return jsonify({"error": "Debes desactivar el proveedor antes de eliminarlo"}), 400
        db.session.delete(proveedor)
        db.session.commit()
        return jsonify({"message": "Proveedor eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar proveedor: {str(e)}"}), 500