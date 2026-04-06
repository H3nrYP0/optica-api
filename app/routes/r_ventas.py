from flask import jsonify, request
from app.database import db
from app.models import Venta, DetalleVenta, Abono
from datetime import datetime
from app.routes import main_bp

@main_bp.route('/ventas', methods=['GET'])
def get_ventas():
    try:
        ventas = Venta.query.all()
        return jsonify([venta.to_dict() for venta in ventas])
    except Exception as e:
        return jsonify({"error": "Error al obtener ventas"}), 500

@main_bp.route('/ventas/<int:id>', methods=['GET'])
def get_venta(id):
    try:
        venta = Venta.query.get(id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
        return jsonify(venta.to_dict())
    except Exception as e:
        return jsonify({"error": "Error al obtener venta"}), 500

@main_bp.route('/ventas/<int:id>', methods=['PUT'])
def update_venta(id):
    try:
        venta = Venta.query.get(id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
        data = request.get_json()
        if 'estado' in data:
            venta.estado = data['estado']
        if 'metodo_pago' in data:
            venta.metodo_pago = data['metodo_pago']
        if 'metodo_entrega' in data:
            venta.metodo_entrega = data['metodo_entrega']
        if 'direccion_entrega' in data:
            venta.direccion_entrega = data['direccion_entrega']
        if 'transferencia_comprobante' in data:
            venta.transferencia_comprobante = data['transferencia_comprobante']
        if 'total' in data:
            venta.total = float(data['total'])
        db.session.commit()
        return jsonify({"message": "Venta actualizada", "venta": venta.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar venta: {str(e)}"}), 500

@main_bp.route('/ventas/<int:id>', methods=['DELETE'])
def delete_venta(id):
    try:
        venta = Venta.query.get(id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
        if venta.abonos and len(venta.abonos) > 0:
            return jsonify({"error": "No se puede eliminar una venta con abonos registrados"}), 400
        db.session.delete(venta)
        db.session.commit()
        return jsonify({"message": "Venta eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar venta: {str(e)}"}), 500

@main_bp.route('/ventas/<int:venta_id>/abonos', methods=['POST'])
def add_abono(venta_id):
    try:
        venta = Venta.query.get(venta_id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
        data = request.get_json()
        if 'monto_abonado' not in data:
            return jsonify({"error": "El campo 'monto_abonado' es requerido"}), 400
        abono = Abono(venta_id=venta.id, monto_abonado=float(data['monto_abonado']), fecha=datetime.utcnow())
        db.session.add(abono)
        db.session.commit()
        return jsonify({"message": "Abono registrado", "abono": abono.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al registrar abono: {str(e)}"}), 500

@main_bp.route('/ventas/<int:venta_id>/abonos', methods=['GET'])
def get_abonos(venta_id):
    try:
        venta = Venta.query.get(venta_id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
        abonos = Abono.query.filter_by(venta_id=venta_id).all()
        return jsonify([abono.to_dict() for abono in abonos])
    except Exception as e:
        return jsonify({"error": "Error al obtener abonos"}), 500

@main_bp.route('/abonos/<int:id>', methods=['DELETE'])
def delete_abono(id):
    try:
        abono = Abono.query.get(id)
        if not abono:
            return jsonify({"error": "Abono no encontrado"}), 404
        db.session.delete(abono)
        db.session.commit()
        return jsonify({"message": "Abono eliminado"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar abono: {str(e)}"}), 500

@main_bp.route('/detalle-venta', methods=['GET'])
def get_detalles_venta():
    try:
        detalles = DetalleVenta.query.all()
        return jsonify([detalle.to_dict() for detalle in detalles])
    except Exception as e:
        return jsonify({"error": "Error al obtener detalles de venta"}), 500

@main_bp.route('/detalle-venta', methods=['POST'])
def create_detalle_venta():
    try:
        data = request.get_json()
        required_fields = ['venta_id', 'producto_id', 'cantidad', 'precio_unitario']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        detalle = DetalleVenta(
            venta_id=data['venta_id'],
            producto_id=data['producto_id'],
            cantidad=data['cantidad'],
            precio_unitario=float(data['precio_unitario']),
            descuento=data.get('descuento', 0.0),
            subtotal=float(data['cantidad']) * float(data['precio_unitario']) - float(data.get('descuento', 0.0))
        )
        db.session.add(detalle)
        db.session.commit()
        return jsonify({"message": "Detalle de venta creado", "detalle": detalle.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear detalle de venta"}), 500

@main_bp.route('/detalle-venta/<int:id>', methods=['PUT'])
def update_detalle_venta(id):
    try:
        detalle = DetalleVenta.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de venta no encontrado"}), 404
        data = request.get_json()
        if 'venta_id' in data:
            detalle.venta_id = data['venta_id']
        if 'producto_id' in data:
            detalle.producto_id = data['producto_id']
        if 'cantidad' in data:
            detalle.cantidad = data['cantidad']
        if 'precio_unitario' in data:
            detalle.precio_unitario = float(data['precio_unitario'])
        if 'descuento' in data:
            detalle.descuento = float(data['descuento'])
        if 'cantidad' in data and 'precio_unitario' in data:
            detalle.subtotal = float(data['cantidad']) * float(data['precio_unitario']) - float(data.get('descuento', detalle.descuento))
        db.session.commit()
        return jsonify({"message": "Detalle de venta actualizado", "detalle": detalle.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar detalle de venta"}), 500

@main_bp.route('/detalle-venta/<int:id>', methods=['DELETE'])
def delete_detalle_venta(id):
    try:
        detalle = DetalleVenta.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de venta no encontrado"}), 404
        db.session.delete(detalle)
        db.session.commit()
        return jsonify({"message": "Detalle de venta eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar detalle de venta"}), 500

@main_bp.route('/ventas/<int:venta_id>/detalles', methods=['GET'])
def get_detalles_venta_especifica(venta_id):
    try:
        detalles = DetalleVenta.query.filter_by(venta_id=venta_id).all()
        return jsonify([detalle.to_dict() for detalle in detalles])
    except Exception as e:
        return jsonify({"error": "Error al obtener detalles de la venta"}), 500