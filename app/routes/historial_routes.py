from flask import Blueprint, jsonify, request
from app.database import db
from app.models import HistorialFormula

historial_bp = Blueprint('historial', __name__)

@historial_bp.route('', methods=['GET'])
def get_historiales():
    try:
        return jsonify([h.to_dict() for h in HistorialFormula.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener historial de fórmulas"}), 500

@historial_bp.route('', methods=['POST'])
def create_historial():
    try:
        data = request.get_json()
        if not data.get('cliente_id'):
            return jsonify({"error": "El cliente_id es requerido"}), 400
        historial = HistorialFormula(
            cliente_id=data['cliente_id'],
            descripcion=data.get('descripcion', ''),
            od_esfera=data.get('od_esfera'),
            od_cilindro=data.get('od_cilindro'),
            od_eje=data.get('od_eje'),
            oi_esfera=data.get('oi_esfera'),
            oi_cilindro=data.get('oi_cilindro'),
            oi_eje=data.get('oi_eje')
        )
        db.session.add(historial)
        db.session.commit()
        return jsonify({"message": "Historial creado", "historial": historial.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear historial"}), 500

@historial_bp.route('/<int:id>', methods=['PUT'])
def update_historial(id):
    try:
        historial = HistorialFormula.query.get(id)
        if not historial:
            return jsonify({"error": "Historial no encontrado"}), 404
        data = request.get_json()
        if 'cliente_id' in data: historial.cliente_id = data['cliente_id']
        if 'descripcion' in data: historial.descripcion = data['descripcion']
        if 'od_esfera' in data: historial.od_esfera = data['od_esfera']
        if 'od_cilindro' in data: historial.od_cilindro = data['od_cilindro']
        if 'od_eje' in data: historial.od_eje = data['od_eje']
        if 'oi_esfera' in data: historial.oi_esfera = data['oi_esfera']
        if 'oi_cilindro' in data: historial.oi_cilindro = data['oi_cilindro']
        if 'oi_eje' in data: historial.oi_eje = data['oi_eje']
        db.session.commit()
        return jsonify({"message": "Historial actualizado", "historial": historial.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar historial"}), 500

@historial_bp.route('/<int:id>', methods=['DELETE'])
def delete_historial(id):
    try:
        historial = HistorialFormula.query.get(id)
        if not historial:
            return jsonify({"error": "Historial no encontrado"}), 404
        db.session.delete(historial)
        db.session.commit()
        return jsonify({"message": "Historial eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar historial"}), 500