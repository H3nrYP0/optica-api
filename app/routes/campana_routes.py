from flask import Blueprint, jsonify, request
from app.database import db
from app.models import CampanaSalud, EstadoCita
from datetime import datetime

campana_bp = Blueprint('campanas', __name__)

@campana_bp.route('', methods=['GET'])
def get_campanas():
    try:
        return jsonify([c.to_dict() for c in CampanaSalud.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener campañas"}), 500

@campana_bp.route('/<int:id>', methods=['GET'])
def get_campana(id):
    try:
        campana = CampanaSalud.query.get(id)
        if not campana:
            return jsonify({"error": "Campaña no encontrada"}), 404
        return jsonify(campana.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@campana_bp.route('', methods=['POST'])
def create_campana():
    try:
        data = request.get_json()
        required = ['empleado_id', 'empresa', 'fecha', 'hora']
        for field in required:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        estado_cita_id = data.get('estado_cita_id', 2)
        if not EstadoCita.query.get(estado_cita_id):
            return jsonify({"error": "El estado de cita especificado no existe"}), 400

        campana = CampanaSalud(
            empleado_id=data['empleado_id'],
            empresa=data['empresa'],
            contacto=data.get('contacto'),
            fecha=datetime.strptime(data['fecha'], '%Y-%m-%d').date(),
            hora=datetime.strptime(data['hora'], '%H:%M').time(),
            direccion=data.get('direccion'),
            observaciones=data.get('observaciones'),
            estado_cita_id=estado_cita_id
        )
        db.session.add(campana)
        db.session.commit()
        return jsonify({"message": "Campaña creada", "campana": campana.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear campaña: {str(e)}"}), 500

@campana_bp.route('/<int:id>', methods=['PUT'])
def update_campana(id):
    try:
        campana = CampanaSalud.query.get(id)
        if not campana:
            return jsonify({"error": "Campaña no encontrada"}), 404
        data = request.get_json()
        if 'empleado_id' in data: campana.empleado_id = data['empleado_id']
        if 'empresa' in data: campana.empresa = data['empresa']
        if 'contacto' in data: campana.contacto = data['contacto']
        if 'fecha' in data: campana.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        if 'hora' in data: campana.hora = datetime.strptime(data['hora'], '%H:%M').time()
        if 'direccion' in data: campana.direccion = data['direccion']
        if 'observaciones' in data: campana.observaciones = data['observaciones']
        if 'estado_cita_id' in data:
            if not EstadoCita.query.get(data['estado_cita_id']):
                return jsonify({"error": "El estado de cita no existe"}), 400
            campana.estado_cita_id = data['estado_cita_id']
        db.session.commit()
        return jsonify({"message": "Campaña actualizada", "campana": campana.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar campaña: {str(e)}"}), 500

@campana_bp.route('/<int:id>', methods=['DELETE'])
def delete_campana(id):
    try:
        campana = CampanaSalud.query.get(id)
        if not campana:
            return jsonify({"error": "Campaña no encontrada"}), 404
        db.session.delete(campana)
        db.session.commit()
        return jsonify({"message": "Campaña eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar campaña: {str(e)}"}), 500