from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Cliente, Cita # Importamos Cita para validar integridad

cliente_bp = Blueprint('clientes', __name__)

@cliente_bp.route('', methods=['GET'])
def get_clientes():
    try:
        # Retorna todos los clientes para la tabla principal
        return jsonify([c.to_dict() for c in Cliente.query.all()]), 200
    except Exception:
        return jsonify({"error": "Error al obtener la lista de clientes"}), 500

@cliente_bp.route('', methods=['POST'])
def create_cliente():
    try:
        data = request.get_json()
        
        # 1. VALIDACIÓN: Campos obligatorios de identificación
        numero_doc = str(data.get('numero_documento', '')).strip()
        nombre = " ".join(data.get('nombre', '').split()).strip()
        apellido = " ".join(data.get('apellido', '').split()).strip()

        if not numero_doc or not nombre:
            return jsonify({"error": "El documento y el nombre son obligatorios"}), 400

        # 2. VALIDACIÓN: Evitar duplicados (Un paciente = Un documento)
        if Cliente.query.filter_by(numero_documento=numero_doc).first():
            return jsonify({"error": f"Ya existe un cliente registrado con el documento {numero_doc}"}), 400

        nuevo_cliente = Cliente(
            tipo_documento=data.get('tipo_documento'),
            numero_documento=numero_doc,
            nombre=nombre,
            apellido=apellido,
            telefono=data.get('telefono'),
            correo=data.get('correo'),
            direccion=data.get('direccion'),
            fecha_nacimiento=data.get('fecha_nacimiento'), # Formato YYYY-MM-DD
            genero=data.get('genero'),
            estado=data.get('estado', True)
        )
        
        db.session.add(nuevo_cliente)
        db.session.commit()
        
        # Respuesta limpia para el Front (Objeto único)
        return jsonify(nuevo_cliente.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al registrar cliente: {str(e)}"}), 500

@cliente_bp.route('/<int:id>', methods=['PUT'])
def update_cliente(id):
    try:
        cliente = db.session.get(Cliente, id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404
        
        data = request.get_json()

        # Si cambia el documento, verificar que no choque con otro cliente
        if 'numero_documento' in data:
            nuevo_doc = str(data['numero_documento']).strip()
            existente = Cliente.query.filter(Cliente.numero_documento == nuevo_doc, Cliente.id != id).first()
            if existente:
                return jsonify({"error": "Ese número de documento ya está asignado a otro paciente"}), 400
            cliente.numero_documento = nuevo_doc

        # Actualización de datos de contacto
        if 'nombre' in data: cliente.nombre = " ".join(data['nombre'].split()).strip()
        if 'apellido' in data: cliente.apellido = " ".join(data['apellido'].split()).strip()
        if 'telefono' in data: cliente.telefono = data['telefono']
        if 'correo' in data: cliente.correo = data['correo']
        if 'direccion' in data: cliente.direccion = data['direccion']
        
        # Corrección de Estado Null
        if 'estado' in data:
            cliente.estado = bool(data['estado'])

        db.session.commit()
        return jsonify(cliente.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@cliente_bp.route('/<int:id>', methods=['DELETE'])
def delete_cliente(id):
    try:
        cliente = db.session.get(Cliente, id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404

        # REGLA DE ORO: No borrar si tiene historial o citas
        # Esto protege la integridad de los datos de salud
        tiene_citas = Cita.query.filter_by(cliente_id=id).first()
        
        if tiene_citas:
            return jsonify({
                "error": "No se puede eliminar el perfil: El paciente tiene citas registradas. Desactívelo para ocultarlo de la lista actual."
            }), 400

        db.session.delete(cliente)
        db.session.commit()
        return jsonify({"message": "Perfil de cliente eliminado correctamente"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error de integridad al intentar eliminar al cliente"}), 500
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