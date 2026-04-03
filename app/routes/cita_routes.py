from flask import Blueprint, jsonify, request
from app.database import db
from app.models import Cita, EstadoCita, Servicio
from datetime import datetime

cita_bp = Blueprint('citas', __name__)

@cita_bp.route('', methods=['GET'])
def get_citas():
    try:
        return jsonify([c.to_dict() for c in Cita.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener citas"}), 500

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
        hora_time = datetime.strptime(hora_str, '%H:%M').time() if hora_str.count(':') == 1 else datetime.strptime(hora_str, '%H:%M:%S').time()

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
        if 'cliente_id' in data: cita.cliente_id = data['cliente_id']
        if 'servicio_id' in data: cita.servicio_id = data['servicio_id']
        if 'empleado_id' in data: cita.empleado_id = data['empleado_id']
        if 'estado_cita_id' in data: cita.estado_cita_id = data['estado_cita_id']
        if 'metodo_pago' in data: cita.metodo_pago = data['metodo_pago']
        if 'duracion' in data: cita.duracion = data['duracion']
        if 'hora' in data:
            hora_str = data['hora']
            cita.hora = datetime.strptime(hora_str, '%H:%M').time() if hora_str.count(':') == 1 else datetime.strptime(hora_str, '%H:%M:%S').time()
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

@cita_bp.route('/servicios', methods=['GET'])
def get_servicios():
    try:
        return jsonify([s.to_dict() for s in Servicio.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener servicios"}), 500

@cita_bp.route('/servicios', methods=['POST'])
def create_servicio():
    try:
        data = request.get_json()
        required = ['nombre', 'duracion_min', 'precio']
        for field in required:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        servicio = Servicio(
            nombre=data['nombre'],
            duracion_min=data['duracion_min'],
            precio=float(data['precio']),
            descripcion=data.get('descripcion', ''),
            estado=data.get('estado', True)
        )
        db.session.add(servicio)
        db.session.commit()
        return jsonify({"message": "Servicio creado", "servicio": servicio.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear servicio"}), 500

@cita_bp.route('/servicios/<int:id>', methods=['PUT'])
def update_servicio(id):
    try:
        servicio = Servicio.query.get(id)
        if not servicio:
            return jsonify({"error": "Servicio no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data: servicio.nombre = data['nombre']
        if 'duracion_min' in data: servicio.duracion_min = data['duracion_min']
        if 'precio' in data: servicio.precio = float(data['precio'])
        if 'descripcion' in data: servicio.descripcion = data['descripcion']
        if 'estado' in data: servicio.estado = data['estado']
        db.session.commit()
        return jsonify({"message": "Servicio actualizado", "servicio": servicio.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar servicio"}), 500

@cita_bp.route('/servicios/<int:id>', methods=['DELETE'])
def delete_servicio(id):
    try:
        servicio = Servicio.query.get(id)
        if not servicio:
            return jsonify({"error": "Servicio no encontrado"}), 404
        db.session.delete(servicio)
        db.session.commit()
        return jsonify({"message": "Servicio eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar servicio"}), 500