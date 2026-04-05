from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Empleado, Horario, CampanaSalud, EstadoCita
from datetime import datetime, timedelta
from optica_app.models import Cita

empleado_bp = Blueprint('empleados', __name__)

@empleado_bp.route('', methods=['GET'])
def get_empleados():
    try:
        return jsonify([e.to_dict() for e in Empleado.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener empleados"}), 500

@empleado_bp.route('', methods=['POST'])
def create_empleado():
    try:
        data = request.get_json()
        required = ['nombre', 'numero_documento', 'fecha_ingreso']
        for field in required:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        empleado = Empleado(
            nombre=data['nombre'],
            tipo_documento=data.get('tipo_documento'),
            numero_documento=data['numero_documento'],
            telefono=data.get('telefono'),
            correo=data.get('correo'),
            direccion=data.get('direccion'),
            fecha_ingreso=datetime.strptime(data['fecha_ingreso'], '%Y-%m-%d').date(),
            cargo=data.get('cargo'),
            estado=data.get('estado', True)
        )
        db.session.add(empleado)
        db.session.commit()
        return jsonify({"message": "Empleado creado", "empleado": empleado.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear empleado"}), 500

@empleado_bp.route('/<int:id>', methods=['PUT'])
def update_empleado(id):
    try:
        empleado = Empleado.query.get(id)
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data: empleado.nombre = data['nombre']
        if 'tipo_documento' in data: empleado.tipo_documento = data['tipo_documento']
        if 'numero_documento' in data: empleado.numero_documento = data['numero_documento']
        if 'telefono' in data: empleado.telefono = data['telefono']
        if 'correo' in data: empleado.correo = data['correo']
        if 'direccion' in data: empleado.direccion = data['direccion']
        if 'fecha_ingreso' in data: empleado.fecha_ingreso = datetime.strptime(data['fecha_ingreso'], '%Y-%m-%d').date()
        if 'cargo' in data: empleado.cargo = data['cargo']
        if 'estado' in data: empleado.estado = data['estado']
        db.session.commit()
        return jsonify({"message": "Empleado actualizado", "empleado": empleado.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar empleado"}), 500

@empleado_bp.route('/<int:id>', methods=['DELETE'])
def delete_empleado(id):
    try:
        empleado = Empleado.query.get(id)
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404
        db.session.delete(empleado)
        db.session.commit()
        return jsonify({"message": "Empleado eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar empleado"}), 500

@empleado_bp.route('/<int:empleado_id>/horarios', methods=['GET'])
def get_horarios_empleado(empleado_id):
    try:
        horarios = Horario.query.filter_by(empleado_id=empleado_id).all()
        return jsonify([h.to_dict() for h in horarios])
    except Exception as e:
        return jsonify({"error": "Error al obtener horarios del empleado"}), 500

@empleado_bp.route('/<int:empleado_id>/campanas', methods=['GET'])
def get_campanas_por_empleado(empleado_id):
    try:
        campanas = CampanaSalud.query.filter_by(empleado_id=empleado_id).all()
        return jsonify([c.to_dict() for c in campanas])
    except Exception as e:
        return jsonify({"error": "Error al obtener campañas del empleado"}), 500

@empleado_bp.route('/verificar-disponibilidad', methods=['GET'])
def verificar_disponibilidad():
    try:
        empleado_id = request.args.get('empleado_id', type=int)
        fecha_str = request.args.get('fecha')
        hora_str = request.args.get('hora')
        duracion = request.args.get('duracion', default=30, type=int)
        exclude_cita_id = request.args.get('exclude_cita_id', type=int)

        if not empleado_id or not fecha_str or not hora_str:
            return jsonify({"disponible": False, "mensaje": "Faltan parámetros: empleado_id, fecha, hora"}), 400

        fecha_date = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        hora_time = datetime.strptime(hora_str, '%H:%M').time()
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
                return jsonify({"disponible": False, "mensaje": f"El empleado ya tiene una cita desde las {cita.hora.strftime('%H:%M')} hasta las {fin_cita.strftime('%H:%M')}"})

        return jsonify({"disponible": True, "mensaje": "Horario disponible", "horario": {"inicio": horario.hora_inicio.strftime('%H:%M'), "fin": horario.hora_final.strftime('%H:%M')}})
    except Exception as e:
        return jsonify({"disponible": False, "mensaje": f"Error: {str(e)}"}), 500