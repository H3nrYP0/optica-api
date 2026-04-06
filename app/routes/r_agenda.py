from flask import jsonify, request
from app.database import db
from app.Models.models import Cita, Servicio, Horario, EstadoCita, Empleado
from datetime import datetime, timedelta
from app.routes import main_bp

@main_bp.route('/citas', methods=['GET'])
def get_citas():
    try:
        citas = Cita.query.all()
        return jsonify([cita.to_dict() for cita in citas])
    except Exception as e:
        return jsonify({"error": "Error al obtener citas"}), 500

@main_bp.route('/citas', methods=['POST'])
def create_cita():
    try:
        data = request.get_json()
        required_fields = ['cliente_id', 'servicio_id', 'empleado_id', 'estado_cita_id', 'fecha', 'hora']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        fecha_date = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        hora_str = data['hora']
        if hora_str.count(':') == 1:
            hora_time = datetime.strptime(hora_str, '%H:%M').time()
        else:
            hora_time = datetime.strptime(hora_str, '%H:%M:%S').time()
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

@main_bp.route('/citas/<int:id>', methods=['PUT'])
def update_cita(id):
    try:
        cita = Cita.query.get(id)
        if not cita:
            return jsonify({"error": "Cita no encontrada"}), 404
        data = request.get_json()
        if 'cliente_id' in data:
            cita.cliente_id = data['cliente_id']
        if 'servicio_id' in data:
            cita.servicio_id = data['servicio_id']
        if 'empleado_id' in data:
            cita.empleado_id = data['empleado_id']
        if 'estado_cita_id' in data:
            cita.estado_cita_id = data['estado_cita_id']
        if 'metodo_pago' in data:
            cita.metodo_pago = data['metodo_pago']
        if 'hora' in data:
            hora_str = data['hora']
            if hora_str.count(':') == 1:
                cita.hora = datetime.strptime(hora_str, '%H:%M').time()
            else:
                cita.hora = datetime.strptime(hora_str, '%H:%M:%S').time()
        if 'duracion' in data:
            cita.duracion = data['duracion']
        if 'fecha' in data:
            cita.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        db.session.commit()
        return jsonify({"message": "Cita actualizada", "cita": cita.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar cita: {str(e)}"}), 500

@main_bp.route('/citas/<int:id>', methods=['DELETE'])
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

@main_bp.route('/servicios', methods=['GET'])
def get_servicios():
    try:
        servicios = Servicio.query.all()
        return jsonify([servicio.to_dict() for servicio in servicios])
    except Exception as e:
        return jsonify({"error": "Error al obtener servicios"}), 500

@main_bp.route('/servicios', methods=['POST'])
def create_servicio():
    try:
        data = request.get_json()
        required_fields = ['nombre', 'duracion_min', 'precio']
        for field in required_fields:
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

@main_bp.route('/servicios/<int:id>', methods=['PUT'])
def update_servicio(id):
    try:
        servicio = Servicio.query.get(id)
        if not servicio:
            return jsonify({"error": "Servicio no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data:
            servicio.nombre = data['nombre']
        if 'duracion_min' in data:
            servicio.duracion_min = data['duracion_min']
        if 'precio' in data:
            servicio.precio = float(data['precio'])
        if 'descripcion' in data:
            servicio.descripcion = data['descripcion']
        if 'estado' in data:
            servicio.estado = data['estado']
        db.session.commit()
        return jsonify({"message": "Servicio actualizado", "servicio": servicio.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar servicio"}), 500

@main_bp.route('/servicios/<int:id>', methods=['DELETE'])
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

@main_bp.route('/horario', methods=['GET'])
def get_horarios():
    try:
        horarios = Horario.query.all()
        return jsonify([horario.to_dict() for horario in horarios])
    except Exception as e:
        return jsonify({"error": "Error al obtener horarios"}), 500

@main_bp.route('/horario', methods=['POST'])
def create_horario():
    try:
        data = request.get_json()
        required_fields = ['empleado_id', 'hora_inicio', 'hora_final', 'dia']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        if not isinstance(data['dia'], int) or data['dia'] not in range(0, 7):
            return jsonify({"error": "El día debe ser un número entre 0 (lunes) y 6 (domingo)"}), 400
        hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
        hora_final = datetime.strptime(data['hora_final'], '%H:%M').time()
        if hora_final <= hora_inicio:
            return jsonify({"error": "La hora final debe ser mayor que la hora inicio"}), 400
        horario = Horario(empleado_id=data['empleado_id'], dia=data['dia'], hora_inicio=hora_inicio, hora_final=hora_final, activo=True)
        db.session.add(horario)
        db.session.commit()
        return jsonify({"message": "Horario creado", "horario": horario.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear horario"}), 500

@main_bp.route('/horario/<int:id>', methods=['PUT'])
def update_horario(id):
    try:
        horario = Horario.query.get(id)
        if not horario:
            return jsonify({"error": "Horario no encontrado"}), 404
        data = request.get_json()
        if 'empleado_id' in data:
            horario.empleado_id = data['empleado_id']
        if 'dia' in data:
            if not isinstance(data['dia'], int) or data['dia'] not in range(0, 7):
                return jsonify({"error": "El día debe ser un número entre 0 (lunes) y 6 (domingo)"}), 400
            horario.dia = data['dia']
        if 'hora_inicio' in data:
            horario.hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
        if 'hora_final' in data:
            horario.hora_final = datetime.strptime(data['hora_final'], '%H:%M').time()
        if 'activo' in data:
            horario.activo = data['activo']
        if horario.hora_final <= horario.hora_inicio:
            return jsonify({"error": "La hora final debe ser mayor que la hora inicio"}), 400
        db.session.commit()
        return jsonify({"message": "Horario actualizado", "horario": horario.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar horario"}), 500

@main_bp.route('/horario/<int:id>', methods=['DELETE'])
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

@main_bp.route('/horario/empleado/<int:empleado_id>', methods=['GET'])
def get_horarios_por_empleado(empleado_id):
    try:
        horarios = Horario.query.filter_by(empleado_id=empleado_id).all()
        return jsonify([h.to_dict() for h in horarios])
    except Exception:
        return jsonify({"error": "Error al obtener horarios"}), 500

@main_bp.route('/empleados/<int:empleado_id>/horarios', methods=['GET'])
def get_horarios_empleado(empleado_id):
    try:
        horarios = Horario.query.filter_by(empleado_id=empleado_id).all()
        return jsonify([horario.to_dict() for horario in horarios])
    except Exception as e:
        return jsonify({"error": "Error al obtener horarios del empleado"}), 500

@main_bp.route('/verificar-disponibilidad', methods=['GET'])
def verificar_disponibilidad():
    try:
        empleado_id = request.args.get('empleado_id', type=int)
        fecha_str = request.args.get('fecha')
        hora_str = request.args.get('hora')
        duracion = request.args.get('duracion', default=30, type=int)
        exclude_cita_id = request.args.get('exclude_cita_id', type=int)
        if not empleado_id or not fecha_str or not hora_str:
            return jsonify({"disponible": False, "mensaje": "Faltan parámetros: empleado_id, fecha, hora"}), 400
        try:
            fecha_date = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora_time = datetime.strptime(hora_str, '%H:%M').time()
        except ValueError:
            return jsonify({"disponible": False, "mensaje": "Formato de fecha u hora inválido"}), 400
        dia_semana = fecha_date.weekday()
        horario = Horario.query.filter_by(empleado_id=empleado_id, dia=dia_semana, activo=True).first()
        if not horario:
            return jsonify({"disponible": False, "mensaje": "El empleado no tiene horario asignado para este día"})
        if hora_time < horario.hora_inicio or hora_time > horario.hora_final:
            return jsonify({"disponible": False, "mensaje": f"El empleado solo trabaja de {horario.hora_inicio.strftime('%H:%M')} a {horario.hora_final.strftime('%H:%M')}"})
        inicio_solicitado = datetime.combine(fecha_date, hora_time)
        fin_solicitado = inicio_solicitado + timedelta(minutes=duracion)
        citas = Cita.query.filter(Cita.empleado_id == empleado_id, Cita.fecha == fecha_date).all()
        for cita in citas:
            if exclude_cita_id and cita.id == exclude_cita_id:
                continue
            inicio_cita = datetime.combine(cita.fecha, cita.hora)
            fin_cita = inicio_cita + timedelta(minutes=cita.duracion or 30)
            if inicio_solicitado < fin_cita and fin_solicitado > inicio_cita:
                return jsonify({"disponible": False, "mensaje": f"El empleado ya tiene una cita programada desde las {cita.hora.strftime('%H:%M')}"})
        return jsonify({"disponible": True, "mensaje": "Horario disponible", "horario": {"inicio": horario.hora_inicio.strftime('%H:%M'), "fin": horario.hora_final.strftime('%H:%M')}})
    except Exception as e:
        return jsonify({"disponible": False, "mensaje": f"Error al verificar disponibilidad: {str(e)}"}), 500

@main_bp.route('/estado-cita', methods=['GET'])
def get_estados_cita():
    try:
        estados = EstadoCita.query.all()
        return jsonify([estado.to_dict() for estado in estados])
    except Exception as e:
        return jsonify({"error": "Error al obtener estados de cita"}), 500

@main_bp.route('/estado-cita', methods=['POST'])
def create_estado_cita():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400
        estado = EstadoCita(nombre=data['nombre'])
        db.session.add(estado)
        db.session.commit()
        return jsonify({"message": "Estado de cita creado", "estado": estado.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear estado de cita"}), 500

@main_bp.route('/estado-cita/<int:id>', methods=['PUT'])
def update_estado_cita(id):
    try:
        estado = EstadoCita.query.get(id)
        if not estado:
            return jsonify({"error": "Estado de cita no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data:
            estado.nombre = data['nombre']
        db.session.commit()
        return jsonify({"message": "Estado de cita actualizado", "estado": estado.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar estado de cita"}), 500

@main_bp.route('/estado-cita/<int:id>', methods=['DELETE'])
def delete_estado_cita(id):
    try:
        estado = EstadoCita.query.get(id)
        if not estado:
            return jsonify({"error": "Estado de cita no encontrado"}), 404
        db.session.delete(estado)
        db.session.commit()
        return jsonify({"message": "Estado de cita eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar estado de cita"}), 500