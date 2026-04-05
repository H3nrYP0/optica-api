from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Cita, EstadoCita, Empleado, Cliente, Servicio
from datetime import datetime, timedelta

cita_bp = Blueprint('citas', __name__)

@cita_bp.route('', methods=['GET'])
def get_citas():
    try:
        citas = Cita.query.all()
        return jsonify([c.to_dict() for c in citas]), 200
    except Exception as e:
        return jsonify({"error": "Error al obtener citas"}), 500

@cita_bp.route('', methods=['POST'])
def create_cita():
    try:
        data = request.get_json()
        required = ['cliente_id', 'servicio_id', 'empleado_id', 'estado_cita_id', 'fecha', 'hora']
        
        for field in required:
            if field not in data or data[field] is None:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        # 1. Procesar Fecha y Hora
        fecha_date = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        hora_str = data['hora']
        hora_time = (datetime.strptime(hora_str, '%H:%M').time() 
                     if hora_str.count(':') == 1 
                     else datetime.strptime(hora_str, '%H:%M:%S').time())

        # 2. VALIDACIÓN: No permitir citas en el pasado
        fecha_completa = datetime.combine(fecha_date, hora_time)
        if fecha_completa < datetime.now():
            return jsonify({"error": "No se pueden programar citas en el pasado"}), 400

        # 3. VALIDACIÓN: Disponibilidad del Empleado (Cruce de horarios)
        duracion = int(data.get('duracion', 30))
        hora_fin = (datetime.combine(fecha_date, hora_time) + timedelta(minutes=duracion)).time()

        # Buscamos si el empleado tiene citas que se solapen en ese día
        cruce = Cita.query.filter(
            Cita.empleado_id == data['empleado_id'],
            Cita.fecha == fecha_date,
            Cita.hora >= (datetime.combine(fecha_date, hora_time) - timedelta(minutes=duracion - 1)).time(),
            Cita.hora <= (datetime.combine(fecha_date, hora_time) + timedelta(minutes=duracion - 1)).time()
        ).first()

        if cruce:
            return jsonify({"error": f"El optómetra ya tiene una cita programada a las {cruce.hora.strftime('%H:%M')}"}), 400

        # 4. VALIDACIÓN: ¿Están activos los involucrados?
        emp = db.session.get(Empleado, data['empleado_id'])
        cli = db.session.get(Cliente, data['cliente_id'])
        if not emp or not emp.estado:
            return jsonify({"error": "El optómetra seleccionado no está activo"}), 400
        if not cli or not cli.estado:
            return jsonify({"error": "El cliente seleccionado está inactivo"}), 400

        nueva_cita = Cita(
            cliente_id=data['cliente_id'],
            servicio_id=data['servicio_id'],
            empleado_id=data['empleado_id'],
            estado_cita_id=data['estado_cita_id'],
            metodo_pago=data.get('metodo_pago'),
            hora=hora_time,
            duracion=duracion,
            fecha=fecha_date
        )
        
        db.session.add(nueva_cita)
        db.session.commit()
        
        # Devolvemos el objeto directo (Respuesta Limpia)
        return jsonify(nueva_cita.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error de formato o validación: {str(e)}"}), 400

@cita_bp.route('/<int:id>', methods=['PUT'])
def update_cita(id):
    try:
        cita = db.session.get(Cita, id)
        if not cita:
            return jsonify({"error": "Cita no encontrada"}), 404
            
        data = request.get_json()
        
        # Si cambia la hora o fecha, se debería repetir la validación de cruce (opcional)
        if 'fecha' in data:
            cita.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        if 'hora' in data:
            hora_str = data['hora']
            cita.hora = (datetime.strptime(hora_str, '%H:%M').time() 
                         if hora_str.count(':') == 1 
                         else datetime.strptime(hora_str, '%H:%M:%S').time())
        
        if 'estado_cita_id' in data: cita.estado_cita_id = data['estado_cita_id']
        if 'metodo_pago' in data: cita.metodo_pago = data['metodo_pago']
        if 'duracion' in data: cita.duracion = data['duracion']
        if 'servicio_id' in data: cita.servicio_id = data['servicio_id']

        db.session.commit()
        return jsonify(cita.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@cita_bp.route('/<int:id>', methods=['DELETE'])
def delete_cita(id):
    try:
        cita = db.session.get(Cita, id)
        if not cita:
            return jsonify({"error": "Cita no encontrada"}), 404
            
        # REGLA: ¿Se puede borrar una cita ya completada? 
        # Depende de si quieren o no, aquí se permite borrar pero podría bloquearse
        db.session.delete(cita)
        db.session.commit()
        return jsonify({"message": "Cita eliminada correctamente"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "No se puede eliminar la cita por integridad de datos"}), 500