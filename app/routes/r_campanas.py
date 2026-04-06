from flask import jsonify, request
from app.database import db
from app.models import CampanaSalud, EstadoCita
from datetime import datetime
from app.routes import main_bp

@main_bp.route('/campanas-salud', methods=['GET'])
def get_campanas_salud():
    try:
        campanas = CampanaSalud.query.all()
        return jsonify([campana.to_dict() for campana in campanas])
    except Exception as e:
        return jsonify({"error": "Error al obtener campañas"}), 500

@main_bp.route('/campanas-salud/<int:id>', methods=['GET'])
def get_campana_salud(id):
    try:
        campana = CampanaSalud.query.get(id)
        if not campana:
            return jsonify({"error": "Campaña no encontrada"}), 404
        return jsonify(campana.to_dict())
    except Exception as e:
        return jsonify({"error": f"Error al obtener campaña: {str(e)}"}), 500

@main_bp.route('/campanas-salud', methods=['POST'])
def create_campana_salud():
    try:
        data = request.get_json()
        required_fields = ['empleado_id', 'empresa', 'fecha', 'hora']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        estado_cita_id = data.get('estado_cita_id', 2)
        estado_cita = EstadoCita.query.get(estado_cita_id)
        if not estado_cita:
            return jsonify({"error": "El estado de cita especificado no existe"}), 400
        try:
            fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
            hora = datetime.strptime(data['hora'], '%H:%M').time()
        except ValueError:
            return jsonify({"error": "Formato de fecha (YYYY-MM-DD) u hora (HH:MM) inválido"}), 400
        campana = CampanaSalud(
            empleado_id=data['empleado_id'],
            empresa=data['empresa'],
            contacto=data.get('contacto'),
            fecha=fecha,
            hora=hora,
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

@main_bp.route('/campanas-salud/<int:id>', methods=['PUT'])
def update_campana_salud(id):
    try:
        campana = CampanaSalud.query.get(id)
        if not campana:
            return jsonify({"error": "Campaña no encontrada"}), 404
        data = request.get_json()
        if 'empleado_id' in data:
            campana.empleado_id = data['empleado_id']
        if 'empresa' in data:
            campana.empresa = data['empresa']
        if 'contacto' in data:
            campana.contacto = data['contacto']
        if 'fecha' in data:
            try:
                campana.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido (use YYYY-MM-DD)"}), 400
        if 'hora' in data:
            try:
                campana.hora = datetime.strptime(data['hora'], '%H:%M').time()
            except ValueError:
                return jsonify({"error": "Formato de hora inválido (use HH:MM)"}), 400
        if 'direccion' in data:
            campana.direccion = data['direccion']
        if 'observaciones' in data:
            campana.observaciones = data['observaciones']
        if 'estado_cita_id' in data:
            estado_cita = EstadoCita.query.get(data['estado_cita_id'])
            if not estado_cita:
                return jsonify({"error": "El estado de cita especificado no existe"}), 400
            campana.estado_cita_id = data['estado_cita_id']
        db.session.commit()
        return jsonify({"message": "Campaña actualizada", "campana": campana.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar campaña: {str(e)}"}), 500

@main_bp.route('/campanas-salud/<int:id>', methods=['DELETE'])
def delete_campana_salud(id):
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

@main_bp.route('/empleados/<int:empleado_id>/campanas', methods=['GET'])
def get_campanas_por_empleado(empleado_id):
    try:
        campanas = CampanaSalud.query.filter_by(empleado_id=empleado_id).all()
        return jsonify([campana.to_dict() for campana in campanas])
    except Exception as e:
        return jsonify({"error": "Error al obtener campañas del empleado"}), 500