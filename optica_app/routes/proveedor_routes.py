from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Proveedor

proveedor_bp = Blueprint('proveedores', __name__)

@proveedor_bp.route('', methods=['GET'])
def get_proveedores():
    try:
        # Devuelve la lista completa para la tabla del Front
        return jsonify([p.to_dict() for p in Proveedor.query.all()]), 200
    except Exception:
        return jsonify({"error": "Error al obtener proveedores"}), 500

@proveedor_bp.route('', methods=['POST'])
def create_proveedor():
    try:
        data = request.get_json()
        
        # 1. VALIDACIÓN: Campos obligatorios
        documento = data.get('documento', '').strip()
        nombre = data.get('razon_social_o_nombre', '').strip()
        
        if not documento or not nombre:
            return jsonify({"error": "Documento y Razón Social son obligatorios"}), 400

        # 2. VALIDACIÓN: No duplicar NIT/Cédula
        if Proveedor.query.filter_by(documento=documento).first():
            return jsonify({"error": f"Ya existe un proveedor con el documento {documento}"}), 400

        nuevo = Proveedor(
            tipo_proveedor=data.get('tipo_provider'),
            tipo_documento=data.get('tipo_documento'),
            documento=documento,
            razon_social_o_nombre=nombre,
            contacto=data.get('contacto'),
            telefono=data.get('telefono'),
            correo=data.get('correo'),
            departamento=data.get('departamento'),
            municipio=data.get('municipio'),
            direccion=data.get('direccion'),
            estado=data.get('estado', True)
        )
        
        db.session.add(nuevo)
        db.session.commit()
        
        # RESPUESTA LIMPIA: Objeto directo, no lista
        return jsonify(nuevo.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@proveedor_bp.route('/<int:id>', methods=['PUT'])
def update_proveedor(id):
    try:
        prov = db.session.get(Proveedor, id)
        if not prov:
            return jsonify({"error": "Proveedor no encontrado"}), 404
            
        data = request.get_json()
        
        # Actualización dinámica de todos los campos
        campos = [
            'tipo_proveedor', 'tipo_documento', 'documento', 
            'razon_social_o_nombre', 'contacto', 'telefono', 
            'correo', 'departamento', 'municipio', 'direccion', 'estado'
        ]
        
        for campo in campos:
            if campo in data:
                valor = data[campo]
                # Validación real: no dejar nombres vacíos al editar
                if campo == 'razon_social_o_nombre' and not str(valor).strip():
                    continue 
                setattr(prov, campo, valor)
        
        # Corrección del "Estado Null": Aseguramos que sea booleano
        if 'estado' in data:
            prov.estado = bool(data['estado'])

        db.session.commit()
        
        # Devolvemos el objeto actualizado para que React refresque la fila correctamente
        return jsonify(prov.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@proveedor_bp.route('/<int:id>', methods=['DELETE'])
def delete_proveedor(id):
    try:
        prov = db.session.get(Proveedor, id)
        if not prov:
            return jsonify({"error": "Proveedor no encontrado"}), 404

        # REGLA DE NEGOCIO: No borrar si ya le compramos algo (Integridad Contable)
        if len(prov.compras) > 0:
            return jsonify({
                "error": "No se puede eliminar: Este proveedor tiene historial de compras. Desactívelo para ocultarlo."
            }), 400

        db.session.delete(prov)
        db.session.commit()
        return jsonify({"message": "Proveedor eliminado correctamente"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error de integridad al intentar eliminar"}), 500
    