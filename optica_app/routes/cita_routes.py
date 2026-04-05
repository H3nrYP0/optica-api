from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Cita, EstadoCita
from datetime import datetime

cita_bp = Blueprint('citas', __name__)


@cita_bp.route('', methods=['GET'])
def get_citas():
    try:
        return jsonify([c.to_dict() for c in Cita.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener citas"}), 500


@cita_bp.route('/<int:id>', methods=['GET'])
def get_cita(id):
    try:
        cita = Cita.query.get(id)
        if not cita:
            return jsonify({"error": "Cita no encontrada"}), 404
        return jsonify(cita.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@cita_bp.route('', methods=['POST'])
def create_cita():
    try:
        data = request.get_json()
        required = ['cliente_id', 'servicio_id', 'empleado_id', 'estado_cita_id', 'fecha', 'hora']
        for field in required:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        fecha_date = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        hora_str = data['hora']
        hora_time = (datetime.strptime(hora_str, '%H:%M').time()
                     if hora_str.count(':') == 1
                     else datetime.strptime(hora_str, '%H:%M:%S').time())

        cita = Cita(
            cliente_id=data['cliente_id'],
            servicio_id=data['servicio_id'],
            empleado_id=data['empleado_id'],
            estado_cita_id=data['estado_cita_id'],
            metodo_pago=data.get('metodo_pago'),
            hora=hora_time,
            duracion=data.get('duracion', 30),
            fecha=fecha_date
        )
        db.session.add(cita)
        db.session.commit()
        return jsonify({"message": "Cita creada", "cita": cita.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear cita: {str(e)}"}), 500


@cita_bp.route('/<int:id>', methods=['PUT'])
def update_cita(id):
    try:
        cita = Cita.query.get(id)
        if not cita:
            return jsonify({"error": "Cita no encontrada"}), 404
        data = request.get_json()
        if 'cliente_id' in data:     cita.cliente_id = data['cliente_id']
        if 'servicio_id' in data:    cita.servicio_id = data['servicio_id']
        if 'empleado_id' in data:    cita.empleado_id = data['empleado_id']
        if 'estado_cita_id' in data: cita.estado_cita_id = data['estado_cita_id']
        if 'metodo_pago' in data:    cita.metodo_pago = data['metodo_pago']
        if 'duracion' in data:       cita.duracion = data['duracion']
        if 'hora' in data:
            hora_str = data['hora']
            cita.hora = (datetime.strptime(hora_str, '%H:%M').time()
                         if hora_str.count(':') == 1
                         else datetime.strptime(hora_str, '%H:%M:%S').time())
        if 'fecha' in data:
            cita.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        db.session.commit()
        return jsonify({"message": "Cita actualizada", "cita": cita.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar cita: {str(e)}"}), 500


@cita_bp.route('/<int:id>', methods=['DELETE'])
def delete_cita(id):
    try:
        cita = Cita.query.get(id)
        if not cita:
            return jsonify({"error": "Cita no encontrada"}), 404
        db.session.delete(cita)
        db.session.commit()
        return jsonify({"message": "Cita eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar cita"}), 500
