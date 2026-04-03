from flask import Blueprint, jsonify, request
from app.database import db
from app.models import Venta, DetalleVenta, Abono
from datetime import datetime

venta_bp = Blueprint('ventas', __name__)

@venta_bp.route('', methods=['GET'])
def get_ventas():
    try:
        return jsonify([v.to_dict() for v in Venta.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener ventas"}), 500

@venta_bp.route('/<int:id>', methods=['GET'])
def get_venta(id):
    try:
        venta = Venta.query.get(id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
        return jsonify(venta.to_dict())
    except Exception as e:
        return jsonify({"error": "Error al obtener venta"}), 500

@venta_bp.route('/<int:id>', methods=['PUT'])
def update_venta(id):
    try:
        venta = Venta.query.get(id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
        data = request.get_json()
        if 'estado' in data: venta.estado = data['estado']
        if 'metodo_pago' in data: venta.metodo_pago = data['metodo_pago']
        if 'metodo_entrega' in data: venta.metodo_entrega = data['metodo_entrega']
        if 'direccion_entrega' in data: venta.direccion_entrega = data['direccion_entrega']
        if 'transferencia_comprobante' in data: venta.transferencia_comprobante = data['transferencia_comprobante']
        if 'total' in data: venta.total = float(data['total'])
        db.session.commit()
        return jsonify({"message": "Venta actualizada", "venta": venta.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar venta: {str(e)}"}), 500

@venta_bp.route('/<int:id>', methods=['DELETE'])
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

@venta_bp.route('/<int:venta_id>/detalles', methods=['GET'])
def get_detalles_venta(venta_id):
    try:
        detalles = DetalleVenta.query.filter_by(venta_id=venta_id).all()
        return jsonify([d.to_dict() for d in detalles])
    except Exception as e:
        return jsonify({"error": "Error al obtener detalles de la venta"}), 500

@venta_bp.route('/<int:venta_id>/abonos', methods=['GET'])
def get_abonos(venta_id):
    try:
        venta = Venta.query.get(venta_id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
        return jsonify([a.to_dict() for a in Abono.query.filter_by(venta_id=venta_id).all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener abonos"}), 500

@venta_bp.route('/<int:venta_id>/abonos', methods=['POST'])
def add_abono(venta_id):
    try:
        venta = Venta.query.get(venta_id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
        data = request.get_json()
        if 'monto_abonado' not in data:
            return jsonify({"error": "El campo 'monto_abonado' es requerido"}), 400
        abono = Abono(venta_id=venta_id, monto_abonado=float(data['monto_abonado']), fecha=datetime.utcnow())
        db.session.add(abono)
        db.session.commit()
        return jsonify({"message": "Abono registrado", "abono": abono.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al registrar abono: {str(e)}"}), 500