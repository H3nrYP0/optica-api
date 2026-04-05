from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Horario
from datetime import datetime

horario_bp = Blueprint('horario', __name__)

@horario_bp.route('', methods=['GET'])
def get_horarios():
    try:
        return jsonify([h.to_dict() for h in Horario.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener horarios"}), 500

@horario_bp.route('', methods=['POST'])
def create_horario():
    try:
        data = request.get_json()
        required = ['empleado_id', 'hora_inicio', 'hora_final', 'dia']
        for field in required:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        if not isinstance(data['dia'], int) or data['dia'] not in range(0, 7):
            return jsonify({"error": "El día debe ser un número entre 0 (lunes) y 6 (domingo)"}), 400

        hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
        hora_final = datetime.strptime(data['hora_final'], '%H:%M').time()

        if hora_final <= hora_inicio:
            return jsonify({"error": "La hora final debe ser mayor que la hora inicio"}), 400

        horario = Horario(
            empleado_id=data['empleado_id'],
            dia=data['dia'],
            hora_inicio=hora_inicio,
            hora_final=hora_final,
            activo=True
        )
        db.session.add(horario)
        db.session.commit()
        return jsonify({"message": "Horario creado", "horario": horario.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear horario"}), 500

@horario_bp.route('/<int:id>', methods=['PUT'])
def update_horario(id):
    try:
        horario = Horario.query.get(id)
        if not horario:
            return jsonify({"error": "Horario no encontrado"}), 404
        data = request.get_json()
        if 'empleado_id' in data: horario.empleado_id = data['empleado_id']
        if 'dia' in data:
            if not isinstance(data['dia'], int) or data['dia'] not in range(0, 7):
                return jsonify({"error": "El día debe ser entre 0 y 6"}), 400
            horario.dia = data['dia']
        if 'hora_inicio' in data: horario.hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
        if 'hora_final' in data: horario.hora_final = datetime.strptime(data['hora_final'], '%H:%M').time()
        if 'activo' in data: horario.activo = data['activo']

        if horario.hora_final <= horario.hora_inicio:
            return jsonify({"error": "La hora final debe ser mayor que la hora inicio"}), 400

        db.session.commit()
        return jsonify({"message": "Horario actualizado", "horario": horario.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar horario"}), 500

@horario_bp.route('/<int:id>', methods=['DELETE'])
def delete_horario(id):
    try:
        horario = Horario.query.get(id)
        if not horario:
            return jsonify({"error": "Horario no encontrado"}), 404
        db.session.delete(horario)
        db.session.commit()
        return jsonify({"message": "Horario eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar horario"}), 500

@horario_bp.route('/empleado/<int:empleado_id>', methods=['GET'])
def get_horarios_por_empleado(empleado_id):
    try:
        return jsonify([h.to_dict() for h in Horario.query.filter_by(empleado_id=empleado_id).all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener horarios"}), 500