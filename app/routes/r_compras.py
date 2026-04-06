from flask import jsonify, request
from app.database import db
from app.Models.models import Compra, DetalleCompra
from app.routes import main_bp

@main_bp.route('/compras', methods=['GET'])
def get_compras():
    try:
        compras = Compra.query.all()
        return jsonify([compra.to_dict() for compra in compras])
    except Exception as e:
        return jsonify({"error": "Error al obtener compras"}), 500

@main_bp.route('/compras', methods=['POST'])
def create_compra():
    try:
        data = request.get_json()
        required_fields = ['proveedor_id', 'total']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        compra = Compra(proveedor_id=data['proveedor_id'], total=float(data['total']), estado_compra=data.get('estado_compra', True))
        db.session.add(compra)
        db.session.commit()
        return jsonify({"message": "Compra creada", "compra": compra.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear compra"}), 500

@main_bp.route('/compras/<int:id>', methods=['PUT'])
def update_compra(id):
    try:
        compra = Compra.query.get(id)
        if not compra:
            return jsonify({"error": "Compra no encontrada"}), 404
        data = request.get_json()
        if 'proveedor_id' in data:
            compra.proveedor_id = data['proveedor_id']
        if 'total' in data:
            compra.total = float(data['total'])
        if 'estado_compra' in data:
            compra.estado_compra = data['estado_compra']
        db.session.commit()
        return jsonify({"message": "Compra actualizada", "compra": compra.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar compra"}), 500

@main_bp.route('/compras/<int:id>', methods=['DELETE'])
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

@main_bp.route('/detalle-compra', methods=['GET'])
def get_detalles_compra():
    try:
        detalles = DetalleCompra.query.all()
        return jsonify([detalle.to_dict() for detalle in detalles])
    except Exception as e:
        return jsonify({"error": "Error al obtener detalles de compra"}), 500

@main_bp.route('/detalle-compra', methods=['POST'])
def create_detalle_compra():
    try:
        data = request.get_json()
        required_fields = ['compra_id', 'producto_id', 'cantidad', 'precio_unidad']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        detalle = DetalleCompra(
            compra_id=data['compra_id'],
            producto_id=data['producto_id'],
            cantidad=data['cantidad'],
            precio_unidad=float(data['precio_unidad']),
            subtotal=float(data['cantidad']) * float(data['precio_unidad'])
        )
        db.session.add(detalle)
        db.session.commit()
        return jsonify({"message": "Detalle de compra creado", "detalle": detalle.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear detalle de compra"}), 500

@main_bp.route('/detalle-compra/<int:id>', methods=['PUT'])
def update_detalle_compra(id):
    try:
        detalle = DetalleCompra.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de compra no encontrado"}), 404
        data = request.get_json()
        if 'compra_id' in data:
            detalle.compra_id = data['compra_id']
        if 'producto_id' in data:
            detalle.producto_id = data['producto_id']
        if 'cantidad' in data:
            detalle.cantidad = data['cantidad']
        if 'precio_unidad' in data:
            detalle.precio_unidad = float(data['precio_unidad'])
        if 'cantidad' in data and 'precio_unidad' in data:
            detalle.subtotal = float(data['cantidad']) * float(data['precio_unidad'])
        db.session.commit()
        return jsonify({"message": "Detalle de compra actualizado", "detalle": detalle.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar detalle de compra"}), 500

@main_bp.route('/detalle-compra/<int:id>', methods=['DELETE'])
def delete_detalle_compra(id):
    try:
        detalle = DetalleCompra.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de compra no encontrado"}), 404
        db.session.delete(detalle)
        db.session.commit()
        return jsonify({"message": "Detalle de compra eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar detalle de compra"}), 500

@main_bp.route('/compras/<int:compra_id>/detalles', methods=['GET'])
def get_detalles_compra_especifica(compra_id):
    try:
        detalles = DetalleCompra.query.filter_by(compra_id=compra_id).all()
        return jsonify([detalle.to_dict() for detalle in detalles])
    except Exception as e:
        return jsonify({"error": "Error al obtener detalles de la compra"}), 500