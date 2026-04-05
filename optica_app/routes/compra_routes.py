from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Compra, DetalleCompra

compra_bp = Blueprint('compras', __name__)

@compra_bp.route('', methods=['GET'])
def get_compras():
    try:
        return jsonify([c.to_dict() for c in Compra.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener compras"}), 500

@compra_bp.route('', methods=['POST'])
def create_compra():
    try:
        data = request.get_json()
        if 'proveedor_id' not in data or 'total' not in data:
            return jsonify({"error": "proveedor_id y total son requeridos"}), 400
        compra = Compra(
            proveedor_id=data['proveedor_id'],
            total=float(data['total']),
            estado_compra=data.get('estado_compra', True)
        )
        db.session.add(compra)
        db.session.commit()
        return jsonify({"message": "Compra creada", "compra": compra.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear compra"}), 500

@compra_bp.route('/<int:id>', methods=['PUT'])
def update_compra(id):
    try:
        compra = Compra.query.get(id)
        if not compra:
            return jsonify({"error": "Compra no encontrada"}), 404
        data = request.get_json()
        if 'proveedor_id' in data: compra.proveedor_id = data['proveedor_id']
        if 'total' in data: compra.total = float(data['total'])
        if 'estado_compra' in data: compra.estado_compra = data['estado_compra']
        db.session.commit()
        return jsonify({"message": "Compra actualizada", "compra": compra.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar compra"}), 500

@compra_bp.route('/<int:id>', methods=['DELETE'])
def delete_compra(id):
    try:
        compra = Compra.query.get(id)
        if not compra:
            return jsonify({"error": "Compra no encontrada"}), 404
        db.session.delete(compra)
        db.session.commit()
        return jsonify({"message": "Compra eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar compra"}), 500

@compra_bp.route('/<int:compra_id>/detalles', methods=['GET'])
def get_detalles_compra(compra_id):
    try:
        detalles = DetalleCompra.query.filter_by(compra_id=compra_id).all()
        return jsonify([d.to_dict() for d in detalles])
    except Exception as e:
        return jsonify({"error": "Error al obtener detalles de la compra"}), 500