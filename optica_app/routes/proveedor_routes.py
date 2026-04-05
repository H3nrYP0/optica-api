from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Proveedor, Compra, DetalleCompra

proveedor_bp = Blueprint('proveedores', __name__)

@proveedor_bp.route('', methods=['GET'])
def get_proveedores():
    try:
        return jsonify([p.to_dict() for p in Proveedor.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener proveedores"}), 500

@proveedor_bp.route('', methods=['POST'])
def create_proveedor():
    try:
        data = request.get_json()
        if not data.get('razon_social_o_nombre'):
            return jsonify({"error": "La razón social o nombre es requerido"}), 400
        proveedor = Proveedor(
            tipo_proveedor=data.get('tipo_proveedor'),
            tipo_documento=data.get('tipo_documento'),
            documento=data.get('documento'),
            razon_social_o_nombre=data['razon_social_o_nombre'],
            contacto=data.get('contacto'),
            telefono=data.get('telefono'),
            correo=data.get('correo'),
            departamento=data.get('departamento'),
            municipio=data.get('municipio'),
            direccion=data.get('direccion'),
            estado=data.get('estado', True)
        )
        db.session.add(proveedor)
        db.session.commit()
        return jsonify({"message": "Proveedor creado", "proveedor": proveedor.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear proveedor"}), 500

@proveedor_bp.route('/<int:id>', methods=['PUT'])
def update_proveedor(id):
    try:
        proveedor = Proveedor.query.get(id)
        if not proveedor:
            return jsonify({"error": "Proveedor no encontrado"}), 404
        data = request.get_json()
        if 'tipo_proveedor' in data: proveedor.tipo_proveedor = data['tipo_proveedor']
        if 'tipo_documento' in data: proveedor.tipo_documento = data['tipo_documento']
        if 'documento' in data: proveedor.documento = data['documento']
        if 'razon_social_o_nombre' in data: proveedor.razon_social_o_nombre = data['razon_social_o_nombre']
        if 'contacto' in data: proveedor.contacto = data['contacto']
        if 'telefono' in data: proveedor.telefono = data['telefono']
        if 'correo' in data: proveedor.correo = data['correo']
        if 'departamento' in data: proveedor.departamento = data['departamento']
        if 'municipio' in data: proveedor.municipio = data['municipio']
        if 'direccion' in data: proveedor.direccion = data['direccion']
        if 'estado' in data: proveedor.estado = data['estado']
        db.session.commit()
        return jsonify({"message": "Proveedor actualizado", "proveedor": proveedor.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar proveedor"}), 500

@proveedor_bp.route('/<int:id>', methods=['DELETE'])
def delete_proveedor(id):
    try:
        proveedor = Proveedor.query.get(id)
        if not proveedor:
            return jsonify({"error": "Proveedor no encontrado"}), 404
        db.session.delete(proveedor)
        db.session.commit()
        return jsonify({"message": "Proveedor eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar proveedor"}), 500