from flask import jsonify, request
from app.database import db
from app.Models.models import Cita, Servicio, Horario, EstadoCita, Empleado, Cliente
from datetime import datetime, timedelta
from app.routes import main_bp


# ============================================================
# MÓDULO: CITAS
# ============================================================

@main_bp.route('/citas', methods=['GET'])
def get_citas():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Ordenar por id descendente (más recientes primero)
        pagination = Cita.query.order_by(Cita.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'data': [cita.to_dict() for cita in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages
        })
    except Exception as e:
        return jsonify({"error": "Error al obtener citas"}), 500

@main_bp.route('/citas/<int:id>', methods=['GET'])
def get_cita(id):
    try:
        cita = Cita.query.get(id)
        if not cita:
            return jsonify({"error": "Cita no encontrada"}), 404
        return jsonify(cita.to_dict())
    except Exception as e:
        return jsonify({"error": "Error al obtener la cita"}), 500


@main_bp.route('/citas', methods=['POST'])
def create_cita():
    try:
        data = request.get_json()
        required_fields = ['cliente_id', 'servicio_id', 'empleado_id', 'estado_cita_id', 'fecha', 'hora']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        # 1. Procesar fecha y hora
        fecha_date = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        hora_str = data['hora']
        if hora_str.count(':') == 1:
            hora_time = datetime.strptime(hora_str, '%H:%M').time()
        else:
            hora_time = datetime.strptime(hora_str, '%H:%M:%S').time()

        # 2. Validar no pasado (usar UTC o zona horaria configurada)
        ahora = datetime.utcnow()
        fecha_hora_cita = datetime.combine(fecha_date, hora_time)
        if fecha_hora_cita < ahora:
            return jsonify({"error": "No se pueden programar citas en el pasado"}), 400

        # 3. Obtener servicio y su duración (obligatorio, no permitir duración externa)
        servicio = Servicio.query.get(data['servicio_id'])
        if not servicio:
            return jsonify({"error": "El servicio especificado no existe"}), 400
        duracion = servicio.duracion_min  # forzado

        # 4. Validar disponibilidad (horario laboral y solapamiento)
        validacion = validar_disponibilidad_cita(
            empleado_id=data['empleado_id'],
            fecha=fecha_date,
            hora=hora_time,
            duracion=duracion,
            exclude_cita_id=None
        )
        if not validacion["disponible"]:
            return jsonify({"error": validacion["mensaje"]}), 400

        # 5. Validar que cliente y empleado estén activos
        empleado = Empleado.query.get(data['empleado_id'])
        cliente = Cliente.query.get(data['cliente_id'])
        if not empleado or not empleado.estado:
            return jsonify({"error": "El optómetra seleccionado no está activo"}), 400
        if not cliente or not cliente.estado:
            return jsonify({"error": "El cliente seleccionado está inactivo"}), 400

        # Crear la cita (sin campo duración del request)
        cita = Cita(
            cliente_id=data['cliente_id'],
            servicio_id=data['servicio_id'],
            empleado_id=data['empleado_id'],
            estado_cita_id=data['estado_cita_id'],
            metodo_pago=data.get('metodo_pago'),
            hora=hora_time,
            duracion=duracion,
            fecha=fecha_date
        )
        db.session.add(cita)
        db.session.commit()
        return jsonify({"message": "Cita creada", "cita": cita.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear cita: {str(e)}"}), 500

def validar_disponibilidad_cita(empleado_id, fecha, hora, duracion, exclude_cita_id=None):
    """
    Retorna dict con 'disponible' (bool) y 'mensaje' (str).
    """
    # Horario laboral
    dia_semana = fecha.weekday()
    horario = Horario.query.filter_by(empleado_id=empleado_id, dia=dia_semana, activo=True).first()
    if not horario:
        return {"disponible": False, "mensaje": "El empleado no tiene horario asignado para este día"}
    if not (horario.hora_inicio <= hora <= horario.hora_final):
        return {
            "disponible": False,
            "mensaje": f"El empleado solo trabaja de {horario.hora_inicio.strftime('%H:%M')} a {horario.hora_final.strftime('%H:%M')}"
        }

    # Solapamiento con otras citas
    inicio_solicitado = datetime.combine(fecha, hora)
    fin_solicitado = inicio_solicitado + timedelta(minutes=duracion)
    citas = Cita.query.filter(
        Cita.empleado_id == empleado_id,
        Cita.fecha == fecha
    )
    if exclude_cita_id:
        citas = citas.filter(Cita.id != exclude_cita_id)

    for cita in citas:
        inicio_cita = datetime.combine(cita.fecha, cita.hora)
        fin_cita = inicio_cita + timedelta(minutes=cita.duracion or 30)
        if inicio_solicitado < fin_cita and fin_solicitado > inicio_cita:
            return {
                "disponible": False,
                "mensaje": f"El empleado ya tiene una cita programada desde las {cita.hora.strftime('%H:%M')}"
            }
    return {"disponible": True, "mensaje": "Horario disponible"}

@main_bp.route('/citas/<int:id>', methods=['PUT'])
def update_cita(id):
    try:
        cita = Cita.query.get(id)
        if not cita:
            return jsonify({"error": "Cita no encontrada"}), 404

        data = request.get_json()

        # No permitir modificar cita pasada
        ahora = datetime.utcnow()
        fecha_cita_actual = datetime.combine(cita.fecha, cita.hora)
        if fecha_cita_actual < ahora:
            return jsonify({"error": "No se puede modificar una cita que ya pasó"}), 400

        # Guardar valores originales para validar solo si cambian
        nuevo_empleado_id = data.get('empleado_id', cita.empleado_id)
        nueva_fecha = data.get('fecha')
        nueva_hora = data.get('hora')
        nuevo_servicio_id = data.get('servicio_id', cita.servicio_id)

        # Si se cambia servicio, forzar nueva duración
        duracion = cita.duracion
        if nuevo_servicio_id != cita.servicio_id:
            servicio = Servicio.query.get(nuevo_servicio_id)
            if not servicio:
                return jsonify({"error": "Servicio no existe"}), 400
            duracion = servicio.duracion_min
            cita.servicio_id = nuevo_servicio_id
            cita.duracion = duracion  # actualizar duración automáticamente

        # Procesar nueva fecha/hora si vienen
        fecha_final = cita.fecha
        hora_final = cita.hora
        if nueva_fecha:
            fecha_final = datetime.strptime(nueva_fecha, '%Y-%m-%d').date()
        if nueva_hora:
            hora_str = nueva_hora
            if hora_str.count(':') == 1:
                hora_final = datetime.strptime(hora_str, '%H:%M').time()
            else:
                hora_final = datetime.strptime(hora_str, '%H:%M:%S').time()

        # Validar que la nueva fecha/hora no sea pasada
        nueva_fecha_hora = datetime.combine(fecha_final, hora_final)
        if nueva_fecha_hora < ahora:
            return jsonify({"error": "No se puede reprogramar la cita a una fecha/hora pasada"}), 400

        # Validar disponibilidad si cambió empleado, fecha, hora o duración
        if (nuevo_empleado_id != cita.empleado_id or
            nueva_fecha is not None or
            nueva_hora is not None or
            nuevo_servicio_id != cita.servicio_id):

            validacion = validar_disponibilidad_cita(
                empleado_id=nuevo_empleado_id,
                fecha=fecha_final,
                hora=hora_final,
                duracion=duracion,
                exclude_cita_id=cita.id
            )
            if not validacion["disponible"]:
                return jsonify({"error": validacion["mensaje"]}), 400

        # Actualizar campos restantes
        if 'cliente_id' in data:
            cliente = Cliente.query.get(data['cliente_id'])
            if not cliente or not cliente.estado:
                return jsonify({"error": "Cliente no válido o inactivo"}), 400
            cita.cliente_id = data['cliente_id']
        if 'estado_cita_id' in data:
            cita.estado_cita_id = data['estado_cita_id']
        if 'metodo_pago' in data:
            cita.metodo_pago = data['metodo_pago']
        if 'empleado_id' in data:
            cita.empleado_id = data['empleado_id']
        if 'fecha' in data:
            cita.fecha = fecha_final
        if 'hora' in data:
            cita.hora = hora_final

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
        
        # No permitir eliminar citas completadas
        estado_actual = EstadoCita.query.get(cita.estado_cita_id)
        if estado_actual and estado_actual.nombre.lower() in ['completada']:
            return jsonify({"error": "No se puede eliminar una cita que ya está completada"}), 400
            
        db.session.delete(cita)
        db.session.commit()
        return jsonify({"message": "Cita eliminada correctamente"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar cita"}), 500


# ============================================================
# MÓDULO: SERVICIOS
# ============================================================

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
        
        # Limpiar y validar nombre
        nombre = " ".join(data.get('nombre', '').split()).strip()
        precio = float(data.get('precio', 0))
        duracion = int(data.get('duracion_min', 30))

        # 1. VALIDACIÓN: Datos básicos
        if not nombre:
            return jsonify({"error": "El nombre del servicio es obligatorio"}), 400
        if precio <= 0:
            return jsonify({"error": "El precio debe ser mayor a 0"}), 400
        if duracion <= 0:
            return jsonify({"error": "La duración debe ser mayor a 0 minutos"}), 400

        # 2. VALIDACIÓN: Unicidad (case insensitive)
        if Servicio.query.filter(Servicio.nombre.ilike(nombre)).first():
            return jsonify({"error": f"El servicio '{nombre}' ya existe"}), 400

        servicio = Servicio(
            nombre=nombre,
            duracion_min=duracion,
            precio=precio,
            descripcion=data.get('descripcion', '').strip(),
            estado=data.get('estado', True)
        )
        
        db.session.add(servicio)
        db.session.commit()
        
        return jsonify({"message": "Servicio creado", "servicio": servicio.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear servicio: {str(e)}"}), 500


@main_bp.route('/servicios/<int:id>', methods=['PUT'])
def update_servicio(id):
    try:
        servicio = Servicio.query.get(id)
        if not servicio:
            return jsonify({"error": "Servicio no encontrado"}), 404
            
        data = request.get_json()
        
        # Si se intenta cambiar el nombre, validar que no choque con otro
        if 'nombre' in data:
            nombre = " ".join(data['nombre'].split()).strip()
            existente = Servicio.query.filter(
                Servicio.nombre.ilike(nombre), 
                Servicio.id != id
            ).first()
            if existente:
                return jsonify({"error": "Ya existe otro servicio con ese nombre"}), 400
            servicio.nombre = nombre

        # Actualización de otros campos con validaciones
        if 'precio' in data:
            precio = float(data['precio'])
            if precio <= 0:
                return jsonify({"error": "El precio debe ser mayor a 0"}), 400
            servicio.precio = precio
            
        if 'duracion_min' in data:
            duracion = int(data['duracion_min'])
            if duracion <= 0:
                return jsonify({"error": "La duración debe ser mayor a 0 minutos"}), 400
            servicio.duracion_min = duracion
            
        if 'descripcion' in data:
            servicio.descripcion = data['descripcion'].strip()
            
        if 'estado' in data:
            # VALIDACIÓN: No desactivar si tiene citas pendientes
            if not data['estado'] and servicio.citas:
                citas_pendientes = [c for c in servicio.citas if c.estado_cita_id == 1]  # 1 = pendiente
                if citas_pendientes:
                    return jsonify({"error": "No puedes desactivar un servicio que tiene citas pendientes"}), 400
            servicio.estado = bool(data['estado'])

        db.session.commit()
        return jsonify({"message": "Servicio actualizado", "servicio": servicio.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar servicio: {str(e)}"}), 500


@main_bp.route('/servicios/<int:id>', methods=['DELETE'])
def delete_servicio(id):
    try:
        servicio = Servicio.query.get(id)
        if not servicio:
            return jsonify({"error": "Servicio no encontrado"}), 404

        # REGLA DE NEGOCIO: No borrar si hay citas asociadas
        if servicio.citas and len(servicio.citas) > 0:
            return jsonify({
                "error": "No se puede eliminar. Este servicio tiene citas registradas. Desactívelo en su lugar."
            }), 400

        db.session.delete(servicio)
        db.session.commit()
        return jsonify({"message": "Servicio eliminado correctamente"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar servicio"}), 500


# ============================================================
# MÓDULO: HORARIOS
# ============================================================

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

        # Validar día
        if not isinstance(data['dia'], int) or data['dia'] not in range(0, 7):
            return jsonify({"error": "El día debe ser un número entre 0 (lunes) y 6 (domingo)"}), 400

        # Validar horas
        try:
            hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
            hora_final = datetime.strptime(data['hora_final'], '%H:%M').time()
        except ValueError:
            return jsonify({"error": "Formato de hora inválido. Use HH:MM"}), 400

        if hora_final <= hora_inicio:
            return jsonify({"error": "La hora final debe ser mayor que la hora inicio"}), 400

        # VALIDACIÓN: Empleado existe y está activo
        empleado = Empleado.query.get(data['empleado_id'])
        if not empleado or not empleado.estado:
            return jsonify({"error": "El empleado especificado no existe o está inactivo"}), 400

        # VALIDACIÓN: No duplicar horario para mismo empleado, día y activo
        horario_existente = Horario.query.filter_by(
            empleado_id=data['empleado_id'],
            dia=data['dia'],
            activo=True
        ).first()
        
        if horario_existente:
            return jsonify({"error": "El empleado ya tiene un horario activo para este día"}), 400

        horario = Horario(
            empleado_id=data['empleado_id'],
            dia=data['dia'],
            hora_inicio=hora_inicio,
            hora_final=hora_final,
            activo=data.get('activo', True)
        )
        
        db.session.add(horario)
        db.session.commit()
        
        return jsonify({"message": "Horario creado", "horario": horario.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear horario: {str(e)}"}), 500


@main_bp.route('/horario/<int:id>', methods=['PUT'])
def update_horario(id):
    try:
        horario = Horario.query.get(id)
        if not horario:
            return jsonify({"error": "Horario no encontrado"}), 404
            
        data = request.get_json()
        
        if 'empleado_id' in data:
            empleado = Empleado.query.get(data['empleado_id'])
            if not empleado or not empleado.estado:
                return jsonify({"error": "Empleado no válido o inactivo"}), 400
            horario.empleado_id = data['empleado_id']
            
        if 'dia' in data:
            if not isinstance(data['dia'], int) or data['dia'] not in range(0, 7):
                return jsonify({"error": "El día debe ser entre 0 y 6"}), 400
            horario.dia = data['dia']
            
        if 'hora_inicio' in data:
            try:
                horario.hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
            except ValueError:
                return jsonify({"error": "Formato de hora inválido. Use HH:MM"}), 400
            
        if 'hora_final' in data:
            try:
                horario.hora_final = datetime.strptime(data['hora_final'], '%H:%M').time()
            except ValueError:
                return jsonify({"error": "Formato de hora inválido. Use HH:MM"}), 400
            
        if 'activo' in data:
            horario.activo = data['activo']

        # Validar que hora_final > hora_inicio
        if horario.hora_final <= horario.hora_inicio:
            return jsonify({"error": "La hora final debe ser mayor que la hora inicio"}), 400

        db.session.commit()
        return jsonify({"message": "Horario actualizado", "horario": horario.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar horario: {str(e)}"}), 500


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
        return jsonify({"error": f"Error al eliminar horario: {str(e)}"}), 500


@main_bp.route('/horario/empleado/<int:empleado_id>', methods=['GET'])
def get_horarios_por_empleado(empleado_id):
    try:
        horarios = Horario.query.filter_by(empleado_id=empleado_id).all()
        return jsonify([h.to_dict() for h in horarios])
    except Exception as e:
        return jsonify({"error": "Error al obtener horarios"}), 500


@main_bp.route('/empleados/<int:empleado_id>/horarios', methods=['GET'])
def get_horarios_empleado(empleado_id):
    try:
        horarios = Horario.query.filter_by(empleado_id=empleado_id).all()
        return jsonify([horario.to_dict() for horario in horarios])
    except Exception as e:
        return jsonify({"error": "Error al obtener horarios del empleado"}), 500

# ============================================================
# MÓDULO: VERIFICAR DISPONIBILIDAD
# ============================================================

@main_bp.route('/verificar-disponibilidad', methods=['GET'])
def verificar_disponibilidad():
    """
    Verifica si un empleado está disponible en una fecha y hora específicas.
    Query params:
        empleado_id (int): ID del empleado
        fecha (str): YYYY-MM-DD
        hora (str): HH:MM
        servicio_id (int): ID del servicio (para obtener duración automática)
        duracion (int): duración en minutos (opcional, se usa si no hay servicio_id)
        exclude_cita_id (int): ID de una cita a excluir (para edición)
    """
    try:
        empleado_id = request.args.get('empleado_id', type=int)
        fecha_str = request.args.get('fecha')
        hora_str = request.args.get('hora')
        servicio_id = request.args.get('servicio_id', type=int)
        duracion = request.args.get('duracion', type=int)
        exclude_cita_id = request.args.get('exclude_cita_id', type=int)

        # Validar parámetros obligatorios
        if not empleado_id or not fecha_str or not hora_str:
            return jsonify({
                "disponible": False,
                "mensaje": "Faltan parámetros: empleado_id, fecha, hora"
            }), 400

        # Validar que el empleado exista y esté activo
        empleado = Empleado.query.get(empleado_id)
        if not empleado or not empleado.estado:
            return jsonify({
                "disponible": False,
                "mensaje": "El empleado no está activo o no existe"
            }), 400

        # Obtener duración desde servicio si se proporciona
        if servicio_id:
            servicio = Servicio.query.get(servicio_id)
            if servicio:
                duracion = servicio.duracion_min
        # Si no hay servicio ni duración, usar valor por defecto seguro
        if not duracion:
            duracion = 30

        # Procesar fecha y hora
        try:
            fecha_date = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora_time = datetime.strptime(hora_str, '%H:%M').time()
        except ValueError:
            return jsonify({
                "disponible": False,
                "mensaje": "Formato de fecha u hora inválido (use YYYY-MM-DD y HH:MM)"
            }), 400

        # Validar que no sea en el pasado (usando UTC)
        ahora = datetime.utcnow()
        fecha_hora_solicitada = datetime.combine(fecha_date, hora_time)
        if fecha_hora_solicitada < ahora:
            return jsonify({
                "disponible": False,
                "mensaje": "No se pueden verificar disponibilidad en el pasado"
            }), 400

        # Verificar horario laboral
        dia_semana = fecha_date.weekday()
        horario = Horario.query.filter_by(
            empleado_id=empleado_id, dia=dia_semana, activo=True
        ).first()

        if not horario:
            return jsonify({
                "disponible": False,
                "mensaje": "El empleado no tiene horario asignado para este día"
            })

        # Validar que la hora esté dentro del rango laboral
        if hora_time < horario.hora_inicio or hora_time > horario.hora_final:
            return jsonify({
                "disponible": False,
                "mensaje": f"El empleado solo trabaja de {horario.hora_inicio.strftime('%H:%M')} a {horario.hora_final.strftime('%H:%M')}",
                "horario": {
                    "inicio": horario.hora_inicio.strftime('%H:%M'),
                    "fin": horario.hora_final.strftime('%H:%M')
                }
            })

        # Verificar solapamiento con citas existentes
        inicio_solicitado = datetime.combine(fecha_date, hora_time)
        fin_solicitado = inicio_solicitado + timedelta(minutes=duracion)

        query = Cita.query.filter(
            Cita.empleado_id == empleado_id,
            Cita.fecha == fecha_date
        )
        if exclude_cita_id:
            query = query.filter(Cita.id != exclude_cita_id)

        for cita in query.all():
            inicio_cita = datetime.combine(cita.fecha, cita.hora)
            fin_cita = inicio_cita + timedelta(minutes=cita.duracion or 30)
            if inicio_solicitado < fin_cita and fin_solicitado > inicio_cita:
                return jsonify({
                    "disponible": False,
                    "mensaje": f"El empleado ya tiene una cita programada desde las {cita.hora.strftime('%H:%M')}",
                    "horario": {
                        "inicio": horario.hora_inicio.strftime('%H:%M'),
                        "fin": horario.hora_final.strftime('%H:%M')
                    }
                })

        # Si todo está bien, retornar disponible
        return jsonify({
            "disponible": True,
            "mensaje": "Horario disponible",
            "horario": {
                "inicio": horario.hora_inicio.strftime('%H:%M'),
                "fin": horario.hora_final.strftime('%H:%M')
            }
        })

    except Exception as e:
        return jsonify({
            "disponible": False,
            "mensaje": f"Error interno al verificar disponibilidad: {str(e)}"
        }), 500

# ============================================================
# MÓDULO: ESTADOS DE CITA
# ============================================================

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
            
        nombre = " ".join(data['nombre'].split()).strip()
        
        # Validar unicidad
        if EstadoCita.query.filter(EstadoCita.nombre.ilike(nombre)).first():
            return jsonify({"error": f"El estado '{nombre}' ya existe"}), 400
            
        estado = EstadoCita(nombre=nombre)
        db.session.add(estado)
        db.session.commit()
        
        return jsonify({"message": "Estado de cita creado", "estado": estado.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear estado de cita: {str(e)}"}), 500


@main_bp.route('/estado-cita/<int:id>', methods=['PUT'])
def update_estado_cita(id):
    try:
        estado = EstadoCita.query.get(id)
        if not estado:
            return jsonify({"error": "Estado de cita no encontrado"}), 404
            
        data = request.get_json()
        
        if 'nombre' in data:
            nombre = " ".join(data['nombre'].split()).strip()
            existente = EstadoCita.query.filter(
                EstadoCita.nombre.ilike(nombre), 
                EstadoCita.id != id
            ).first()
            if existente:
                return jsonify({"error": "Ya existe otro estado con ese nombre"}), 400
            estado.nombre = nombre
            
        db.session.commit()
        return jsonify({"message": "Estado de cita actualizado", "estado": estado.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar estado de cita: {str(e)}"}), 500


@main_bp.route('/estado-cita/<int:id>', methods=['DELETE'])
def delete_estado_cita(id):
    try:
        estado = EstadoCita.query.get(id)
        if not estado:
            return jsonify({"error": "Estado de cita no encontrado"}), 404
            
        # Validar que no tenga citas asociadas
        if estado.citas and len(estado.citas) > 0:
            return jsonify({"error": "No se puede eliminar un estado que tiene citas asociadas"}), 400
            
        db.session.delete(estado)
        db.session.commit()
        return jsonify({"message": "Estado de cita eliminado correctamente"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar estado de cita: {str(e)}"}), 500