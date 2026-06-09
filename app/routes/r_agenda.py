"""
Módulo de agenda: citas, servicios, horarios, novedades y disponibilidad.
Permisos granulares:
- Citas: ver_citas, crear_citas, editar_citas, eliminar_citas
- Servicios: ver_servicios, crear_servicios, editar_servicios, eliminar_servicios
- Horarios y novedades: ver_empleados, crear_empleados, editar_empleados, eliminar_empleados
- Estados de cita: ver_citas, crear_citas, editar_citas, eliminar_citas
"""

from flask import jsonify, request
from app.database import db
from app.Models.models import (
    Cita, Servicio, Horario, EstadoCita, Empleado, Cliente,
    Venta, EstadoVenta, DetalleVenta, Novedad
)
from datetime import datetime, timedelta
import pytz
from app.routes import main_bp
from app.auth.decorators import permiso_requerido

tz_colombia = pytz.timezone('America/Bogota')
MAX_PER_PAGE = 10


# ============================================================
# FUNCIÓN AUXILIAR DE DISPONIBILIDAD (CORREGIDA)
# ============================================================
def validar_disponibilidad_cita(empleado_id, fecha, hora, duracion, exclude_cita_id=None):
    """
    Retorna dict con 'disponible' (bool) y 'mensaje' (str).
    Versión robusta que verifica novedades (con o sin horario), horario laboral y solapamiento.
    """
    # 1. Verificar novedades activas (activo es booleano)
    novedad = Novedad.query.filter(
        Novedad.empleado_id == empleado_id,
        Novedad.fecha_inicio <= fecha,
        Novedad.fecha_fin >= fecha,
        Novedad.activo == True
    ).first()
    if novedad:
        empleado_nombre = Empleado.query.get(empleado_id).nombre
        fecha_inicio_str = novedad.fecha_inicio.strftime('%d/%m/%Y')
        fecha_fin_str = novedad.fecha_fin.strftime('%d/%m/%Y')
        motivo_str = f": {novedad.motivo}" if novedad.motivo else ""
        # Novedad de día completo (sin horas)
        if novedad.hora_inicio is None and novedad.hora_fin is None:
            return {
                "disponible": False,
                "mensaje": f"El empleado {empleado_nombre} no está disponible por {novedad.tipo} del {fecha_inicio_str} al {fecha_fin_str}{motivo_str}."
            }
        # Novedad con rango horario
        if novedad.hora_inicio and novedad.hora_fin:
            if novedad.hora_inicio <= hora <= novedad.hora_fin:
                hora_inicio_str = novedad.hora_inicio.strftime('%H:%M')
                hora_fin_str = novedad.hora_fin.strftime('%H:%M')
                return {
                    "disponible": False,
                    "mensaje": f"El empleado {empleado_nombre} no está disponible el {fecha_inicio_str} de {hora_inicio_str} a {hora_fin_str} por {novedad.tipo}{motivo_str}."
                }

    # 2. Verificar horario laboral
    dia_semana = fecha.weekday()  # 0=lunes ... 6=domingo
    horario = Horario.query.filter_by(
        empleado_id=empleado_id, dia=dia_semana, activo=True
    ).first()
    if not horario:
        return {"disponible": False, "mensaje": "El empleado no tiene horario asignado para este día"}
    if not (horario.hora_inicio <= hora <= horario.hora_final):
        return {
            "disponible": False,
            "mensaje": f"El empleado solo trabaja de {horario.hora_inicio.strftime('%H:%M')} a {horario.hora_final.strftime('%H:%M')}"
        }

    # 3. Verificar solapamiento con otras citas (excluyendo la propia si se edita)
    inicio_solicitado = datetime.combine(fecha, hora)
    fin_solicitado = inicio_solicitado + timedelta(minutes=duracion)
    citas = Cita.query.filter(Cita.empleado_id == empleado_id, Cita.fecha == fecha)
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


# ============================================================
# MÓDULO: CITAS (con paginación, búsqueda y filtros)
# ============================================================

@main_bp.route('/citas', methods=['GET'])
@permiso_requerido("ver_citas")
def get_citas():
    """
    Listar citas con paginación, búsqueda y filtros.
    Query params:
        page          (int) – página actual
        per_page      (int) – máx 10
        search        (str) – busca en cliente (nombre/apellido) o empleado (nombre)
        cliente_id    (int)
        empleado_id   (int)
        servicio_id   (int)
        estado_cita_id(int)
        fecha_desde   (str) YYYY-MM-DD
        fecha_hasta   (str) YYYY-MM-DD
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        search = request.args.get('search', '', type=str).strip()
        cliente_id = request.args.get('cliente_id', type=int)
        empleado_id = request.args.get('empleado_id', type=int)
        servicio_id = request.args.get('servicio_id', type=int)
        estado_cita_id = request.args.get('estado_cita_id', type=int)
        fecha_desde = request.args.get('fecha_desde', '', type=str).strip()
        fecha_hasta = request.args.get('fecha_hasta', '', type=str).strip()

        query = Cita.query
        if cliente_id:
            query = query.filter(Cita.cliente_id == cliente_id)
        if empleado_id:
            query = query.filter(Cita.empleado_id == empleado_id)
        if servicio_id:
            query = query.filter(Cita.servicio_id == servicio_id)
        if estado_cita_id:
            query = query.filter(Cita.estado_cita_id == estado_cita_id)
        if fecha_desde:
            try:
                fd = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                query = query.filter(Cita.fecha >= fd)
            except ValueError:
                return jsonify({"error": "Formato fecha_desde inválido"}), 400
        if fecha_hasta:
            try:
                fh = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                query = query.filter(Cita.fecha <= fh)
            except ValueError:
                return jsonify({"error": "Formato fecha_hasta inválido"}), 400
        if search:
            like = f"%{search}%"
            query = query.join(Cliente, Cita.cliente_id == Cliente.id) \
                         .join(Empleado, Cita.empleado_id == Empleado.id) \
                         .filter(
                db.or_(
                    Cliente.nombre.ilike(like),
                    Cliente.apellido.ilike(like),
                    Empleado.nombre.ilike(like),
                    Empleado.apellido.ilike(like)
                )
            )

        query = query.order_by(Cita.fecha.desc(), Cita.hora.desc())

        # Si no hay paginación ni filtros, devolver todos (para uso interno)
        has_pagination = 'page' in request.args or 'per_page' in request.args
        has_filters = cliente_id or empleado_id or servicio_id or estado_cita_id or fecha_desde or fecha_hasta or search
        if not has_pagination and not has_filters:
            citas = query.all()
            return jsonify([cita.to_dict() for cita in citas])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [cita.to_dict() for cita in pagination.items],
            'pagination': {
                'current_page': pagination.page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
        })
    except Exception as e:
        return jsonify({"error": f"Error al obtener citas: {str(e)}"}), 500


@main_bp.route('/citas/<int:id>', methods=['GET'])
@permiso_requerido("ver_citas")
def get_cita(id):
    try:
        cita = Cita.query.get(id)
        if not cita:
            return jsonify({"error": "Cita no encontrada"}), 404
        return jsonify(cita.to_dict())
    except Exception as e:
        return jsonify({"error": f"Error al obtener la cita: {str(e)}"}), 500


@main_bp.route('/citas', methods=['POST'])
@permiso_requerido("crear_citas")
def create_cita():
    try:
        data = request.get_json()
        required = ['cliente_id', 'servicio_id', 'empleado_id', 'estado_cita_id', 'fecha', 'hora']
        for field in required:
            if field not in data or data[field] is None:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        # Validar fecha y hora
        try:
            fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
        try:
            hora = datetime.strptime(data['hora'], '%H:%M').time()
        except ValueError:
            return jsonify({"error": "Formato de hora inválido. Use HH:MM"}), 400

        # Validar que no sea pasado
        ahora_utc = datetime.utcnow()
        if datetime.combine(fecha, hora) < ahora_utc:
            return jsonify({"error": "No se pueden programar citas en el pasado"}), 400

        # Obtener servicio (para duración)
        servicio = Servicio.query.get(data['servicio_id'])
        if not servicio or not servicio.estado:
            return jsonify({"error": "Servicio no válido o inactivo"}), 400
        duracion = servicio.duracion_min

        # Verificar disponibilidad
        disponibilidad = validar_disponibilidad_cita(
            empleado_id=data['empleado_id'],
            fecha=fecha,
            hora=hora,
            duracion=duracion,
            exclude_cita_id=None
        )
        if not disponibilidad["disponible"]:
            return jsonify({"error": disponibilidad["mensaje"]}), 400

        # Verificar existencia y estado de empleado y cliente
        empleado = Empleado.query.get(data['empleado_id'])
        if not empleado or not empleado.estado:
            return jsonify({"error": "El optómetra seleccionado no está activo"}), 400
        cliente = Cliente.query.get(data['cliente_id'])
        if not cliente or not cliente.estado:
            return jsonify({"error": "El cliente seleccionado está inactivo"}), 400

        # Crear cita
        nueva_cita = Cita(
            cliente_id=data['cliente_id'],
            servicio_id=servicio.id,
            empleado_id=data['empleado_id'],
            estado_cita_id=data['estado_cita_id'],
            metodo_pago=data.get('metodo_pago'),
            hora=hora,
            duracion=duracion,
            fecha=fecha
        )
        db.session.add(nueva_cita)
        db.session.commit()
        return jsonify({"message": "Cita creada", "cita": nueva_cita.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear cita: {str(e)}"}), 500


@main_bp.route('/citas/<int:id>', methods=['PUT'])
@permiso_requerido("editar_citas")
def update_cita(id):
    try:
        cita = Cita.query.get(id)
        if not cita:
            return jsonify({"error": "Cita no encontrada"}), 404

        # No permitir editar si ya está cancelada
        estado_actual = EstadoCita.query.get(cita.estado_cita_id)
        if estado_actual and estado_actual.nombre.lower() == "cancelada":
            return jsonify({"error": "No se puede modificar una cita cancelada"}), 400

        ahora_utc = datetime.utcnow()
        if datetime.combine(cita.fecha, cita.hora) < ahora_utc:
            return jsonify({"error": "No se puede modificar una cita que ya pasó"}), 400

        data = request.get_json()

        # Obtener nuevos valores (o mantener los actuales)
        nuevo_empleado_id = data.get('empleado_id', cita.empleado_id)
        nueva_fecha_str = data.get('fecha')
        nueva_hora_str = data.get('hora')
        nuevo_servicio_id = data.get('servicio_id', cita.servicio_id)

        fecha_final = cita.fecha
        hora_final = cita.hora
        if nueva_fecha_str:
            try:
                fecha_final = datetime.strptime(nueva_fecha_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
        if nueva_hora_str:
            try:
                hora_final = datetime.strptime(nueva_hora_str, '%H:%M').time()
            except ValueError:
                return jsonify({"error": "Formato de hora inválido. Use HH:MM"}), 400

        # Validar que la nueva fecha/hora no sea pasada
        if datetime.combine(fecha_final, hora_final) < ahora_utc:
            return jsonify({"error": "No se puede reprogramar a una fecha/hora pasada"}), 400

        # Duración: puede cambiar si se cambia el servicio
        duracion = cita.duracion
        if nuevo_servicio_id != cita.servicio_id:
            servicio = Servicio.query.get(nuevo_servicio_id)
            if not servicio or not servicio.estado:
                return jsonify({"error": "Servicio no válido o inactivo"}), 400
            duracion = servicio.duracion_min

        # Verificar disponibilidad si cambian datos relevantes
        if (nuevo_empleado_id != cita.empleado_id or
            nueva_fecha_str is not None or
            nueva_hora_str is not None or
            nuevo_servicio_id != cita.servicio_id):
            disponibilidad = validar_disponibilidad_cita(
                empleado_id=nuevo_empleado_id,
                fecha=fecha_final,
                hora=hora_final,
                duracion=duracion,
                exclude_cita_id=cita.id
            )
            if not disponibilidad["disponible"]:
                return jsonify({"error": disponibilidad["mensaje"]}), 400

        # Actualizar campos
        if 'cliente_id' in data:
            cliente = Cliente.query.get(data['cliente_id'])
            if not cliente or not cliente.estado:
                return jsonify({"error": "Cliente no válido o inactivo"}), 400
            cita.cliente_id = data['cliente_id']
        if 'empleado_id' in data:
            empleado = Empleado.query.get(data['empleado_id'])
            if not empleado or not empleado.estado:
                return jsonify({"error": "Empleado no válido o inactivo"}), 400
            cita.empleado_id = data['empleado_id']
        if 'servicio_id' in data:
            cita.servicio_id = nuevo_servicio_id
            cita.duracion = duracion
        if 'fecha' in data:
            cita.fecha = fecha_final
        if 'hora' in data:
            cita.hora = hora_final
        if 'metodo_pago' in data:
            cita.metodo_pago = data['metodo_pago']
        if 'estado_cita_id' in data:
            nuevo_estado = EstadoCita.query.get(data['estado_cita_id'])
            if not nuevo_estado:
                return jsonify({"error": "Estado de cita inválido"}), 400
            # Si se marca como completada, crear venta automática si no existe
            if data['estado_cita_id'] == 3 and cita.estado_cita_id != 3:
                if hasattr(cita, 'venta') and cita.venta:
                    return jsonify({"error": "Esta cita ya tiene una venta asociada"}), 400
                servicio_actual = Servicio.query.get(cita.servicio_id)
                if not servicio_actual:
                    return jsonify({"error": "Servicio no encontrado"}), 404
                estado_venta = EstadoVenta.query.filter_by(nombre='completada').first()
                if not estado_venta:
                    return jsonify({"error": "Estado 'completada' no encontrado en EstadoVenta"}), 500
                venta = Venta(
                    cita_id=cita.id,
                    cliente_id=cita.cliente_id,
                    fecha_venta=datetime.utcnow(),
                    total=servicio_actual.precio,
                    metodo_pago=cita.metodo_pago,
                    estado_id=estado_venta.id
                )
                db.session.add(venta)
                db.session.flush()
                detalle = DetalleVenta(
                    venta_id=venta.id,
                    servicio_id=servicio_actual.id,
                    cantidad=1,
                    precio_unitario=servicio_actual.precio,
                    subtotal=servicio_actual.precio
                )
                db.session.add(detalle)
            cita.estado_cita_id = data['estado_cita_id']

        db.session.commit()
        return jsonify({"message": "Cita actualizada", "cita": cita.to_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar cita: {str(e)}"}), 500


@main_bp.route('/citas/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_citas")
def delete_cita(id):
    try:
        cita = Cita.query.get(id)
        if not cita:
            return jsonify({"error": "Cita no encontrada"}), 404

        estado = EstadoCita.query.get(cita.estado_cita_id)
        if estado and estado.nombre.lower() == 'completada':
            return jsonify({"error": "No se puede eliminar una cita completada"}), 400

        ahora_utc = datetime.utcnow()
        if datetime.combine(cita.fecha, cita.hora) < ahora_utc:
            return jsonify({"error": "No se puede eliminar una cita que ya pasó"}), 400

        db.session.delete(cita)
        db.session.commit()
        return jsonify({"message": "Cita eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar cita: {str(e)}"}), 500


# ============================================================
# MÓDULO: SERVICIOS (público GET, resto con permisos)
# ============================================================

@main_bp.route('/servicios', methods=['GET'])
def get_servicios():
    """
    Listar servicios con paginación, búsqueda y filtro de estado.
    Query params: page, per_page, search, estado
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        search = request.args.get('search', '', type=str).strip()
        estado = request.args.get('estado', '', type=str).strip().lower()

        query = Servicio.query
        if search:
            query = query.filter(Servicio.nombre.ilike(f"%{search}%"))
        if estado != '':
            estado_bool = estado == 'true'
            query = query.filter(Servicio.estado == estado_bool)

        query = query.order_by(Servicio.nombre.asc())

        # Si no hay paginación ni filtros, devolver todos
        if 'page' not in request.args and 'per_page' not in request.args and not search and estado == '':
            servicios = query.all()
            return jsonify([s.to_dict() for s in servicios])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [s.to_dict() for s in pagination.items],
            'pagination': {
                'current_page': pagination.page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
        })
    except Exception as e:
        return jsonify({"error": "Error al obtener servicios"}), 500


@main_bp.route('/servicios', methods=['POST'])
@permiso_requerido("crear_servicios")
def create_servicio():
    try:
        data = request.get_json()
        nombre = " ".join(data.get('nombre', '').split()).strip()
        if not nombre:
            return jsonify({"error": "El nombre del servicio es obligatorio"}), 400
        precio = float(data.get('precio', 0))
        duracion = int(data.get('duracion_min', 30))
        if precio <= 0:
            return jsonify({"error": "El precio debe ser mayor a 0"}), 400
        if duracion <= 0:
            return jsonify({"error": "La duración debe ser mayor a 0 minutos"}), 400
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
@permiso_requerido("editar_servicios")
def update_servicio(id):
    try:
        servicio = Servicio.query.get(id)
        if not servicio:
            return jsonify({"error": "Servicio no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data:
            nombre = " ".join(data['nombre'].split()).strip()
            existente = Servicio.query.filter(Servicio.nombre.ilike(nombre), Servicio.id != id).first()
            if existente:
                return jsonify({"error": "Ya existe otro servicio con ese nombre"}), 400
            servicio.nombre = nombre
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
            # Validar que no se desactive si tiene citas pendientes
            if not data['estado'] and servicio.citas:
                pendientes = [c for c in servicio.citas if c.estado_cita_id == 1]  # 1 = pendiente
                if pendientes:
                    return jsonify({"error": "No se puede desactivar un servicio con citas pendientes"}), 400
            servicio.estado = bool(data['estado'])
        db.session.commit()
        return jsonify({"message": "Servicio actualizado", "servicio": servicio.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar servicio: {str(e)}"}), 500


@main_bp.route('/servicios/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_servicios")
def delete_servicio(id):
    try:
        servicio = Servicio.query.get(id)
        if not servicio:
            return jsonify({"error": "Servicio no encontrado"}), 404
        if servicio.citas and len(servicio.citas) > 0:
            return jsonify({"error": "No se puede eliminar. Este servicio tiene citas registradas. Desactívelo en su lugar."}), 400
        db.session.delete(servicio)
        db.session.commit()
        return jsonify({"message": "Servicio eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar servicio"}), 500


# ============================================================
# MÓDULO: HORARIOS (permisos de empleados)
# ============================================================

@main_bp.route('/horario', methods=['GET'])
@permiso_requerido("ver_empleados")
def get_horarios():
    """
    Listar horarios con paginación, búsqueda por empleado, filtro por activo.
    Query params: page, per_page, empleado_id, activo
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        empleado_id = request.args.get('empleado_id', type=int)
        activo = request.args.get('activo', '', type=str).strip().lower()

        query = Horario.query
        if empleado_id:
            query = query.filter(Horario.empleado_id == empleado_id)
        if activo != '':
            activo_bool = activo == 'true'
            query = query.filter(Horario.activo == activo_bool)

        query = query.order_by(Horario.empleado_id, Horario.dia)

        if 'page' not in request.args and 'per_page' not in request.args and not empleado_id and activo == '':
            horarios = query.all()
            return jsonify([h.to_dict() for h in horarios])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [h.to_dict() for h in pagination.items],
            'pagination': {
                'current_page': pagination.page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
        })
    except Exception as e:
        return jsonify({"error": "Error al obtener horarios"}), 500


@main_bp.route('/horario', methods=['POST'])
@permiso_requerido("crear_empleados")
def create_horario():
    try:
        data = request.get_json()
        required = ['empleado_id', 'hora_inicio', 'hora_final', 'dia']
        for field in required:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        if not isinstance(data['dia'], int) or data['dia'] not in range(0, 7):
            return jsonify({"error": "El día debe ser un número entre 0 (lunes) y 6 (domingo)"}), 400
        try:
            hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
            hora_final = datetime.strptime(data['hora_final'], '%H:%M').time()
        except ValueError:
            return jsonify({"error": "Formato de hora inválido. Use HH:MM"}), 400
        if hora_final <= hora_inicio:
            return jsonify({"error": "La hora final debe ser posterior a la hora de inicio."}), 400

        empleado = Empleado.query.get(data['empleado_id'])
        if not empleado or not empleado.estado:
            return jsonify({"error": "Empleado no válido o inactivo"}), 400

        # Evitar duplicado activo para el mismo día
        existente = Horario.query.filter_by(empleado_id=data['empleado_id'], dia=data['dia'], activo=True).first()
        if existente:
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
@permiso_requerido("editar_empleados")
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
        if horario.hora_final <= horario.hora_inicio:
            return jsonify({"error": "La hora final debe ser mayor que la hora inicio"}), 400
        db.session.commit()
        return jsonify({"message": "Horario actualizado", "horario": horario.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar horario: {str(e)}"}), 500


@main_bp.route('/horario/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_empleados")
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
@permiso_requerido("ver_empleados")
def get_horarios_por_empleado(empleado_id):
    try:
        horarios = Horario.query.filter_by(empleado_id=empleado_id).all()
        return jsonify([h.to_dict() for h in horarios])
    except Exception as e:
        return jsonify({"error": "Error al obtener horarios"}), 500


@main_bp.route('/empleados/<int:empleado_id>/horarios', methods=['GET'])
@permiso_requerido("ver_empleados")
def get_horarios_empleado(empleado_id):
    try:
        horarios = Horario.query.filter_by(empleado_id=empleado_id).all()
        return jsonify([horario.to_dict() for horario in horarios])
    except Exception as e:
        return jsonify({"error": "Error al obtener horarios del empleado"}), 500


# ============================================================
# MÓDULO: VERIFICAR DISPONIBILIDAD (público)
# ============================================================

@main_bp.route('/verificar-disponibilidad', methods=['GET'])
def verificar_disponibilidad():
    """
    Endpoint público para verificar disponibilidad de una cita.
    Parámetros:
        empleado_id (int) obligatorio
        fecha (str) YYYY-MM-DD
        hora (str) HH:MM
        servicio_id (int) opcional (para obtener duración)
        duracion (int) opcional (si no se envía servicio_id)
        exclude_cita_id (int) opcional (para edición)
    """
    try:
        empleado_id = request.args.get('empleado_id', type=int)
        fecha_str = request.args.get('fecha')
        hora_str = request.args.get('hora')
        servicio_id = request.args.get('servicio_id', type=int)
        duracion = request.args.get('duracion', type=int)
        exclude_cita_id = request.args.get('exclude_cita_id', type=int)

        if not empleado_id or not fecha_str or not hora_str:
            return jsonify({"disponible": False, "mensaje": "Faltan parámetros: empleado_id, fecha, hora"}), 400

        empleado = Empleado.query.get(empleado_id)
        if not empleado or not empleado.estado:
            return jsonify({"disponible": False, "mensaje": "El empleado no está activo o no existe"}), 400

        # Obtener duración: si viene servicio_id, lo usamos; si no, usamos el parámetro duracion; defecto 30
        if servicio_id:
            servicio = Servicio.query.get(servicio_id)
            if servicio:
                duracion = servicio.duracion_min
        if not duracion:
            duracion = 30

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora = datetime.strptime(hora_str, '%H:%M').time()
        except ValueError:
            return jsonify({"disponible": False, "mensaje": "Formato de fecha u hora inválido"}), 400

        # No permitir verificar disponibilidad en el pasado
        ahora_utc = datetime.utcnow()
        if datetime.combine(fecha, hora) < ahora_utc:
            return jsonify({"disponible": False, "mensaje": "No se pueden verificar horarios en el pasado"}), 400

        resultado = validar_disponibilidad_cita(empleado_id, fecha, hora, duracion, exclude_cita_id)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"disponible": False, "mensaje": f"Error interno: {str(e)}"}), 500


@main_bp.route('/verificar-disponibilidad-multiple', methods=['GET'])
def verificar_disponibilidad_multiple():
    """
    Endpoint público para obtener todas las horas disponibles de un día para un servicio.
    Parámetros:
        servicio_id (int) obligatorio
        fecha (str) YYYY-MM-DD
        intervalo_minutos (int) opcional, defecto 30
        empleados_ids (str) opcional, lista separada por comas
    """
    try:
        servicio_id = request.args.get('servicio_id', type=int)
        fecha_str = request.args.get('fecha')
        intervalo = request.args.get('intervalo_minutos', 30, type=int)
        empleados_ids_str = request.args.get('empleados_ids', '')

        if not servicio_id or not fecha_str:
            return jsonify({"error": "Faltan parámetros: servicio_id, fecha"}), 400
        if intervalo < 1:
            intervalo = 30

        servicio = Servicio.query.get(servicio_id)
        if not servicio or not servicio.estado:
            return jsonify({"error": "Servicio no encontrado o inactivo"}), 404

        duracion = servicio.duracion_min
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400

        hoy_utc = datetime.utcnow().date()
        if fecha < hoy_utc:
            return jsonify({"error": "No se puede consultar disponibilidad en fechas pasadas"}), 400

        # Seleccionar empleados
        if empleados_ids_str:
            ids = [int(x) for x in empleados_ids_str.split(',') if x.strip().isdigit()]
            empleados = Empleado.query.filter(Empleado.id.in_(ids), Empleado.estado == True).all()
        else:
            empleados = Empleado.query.filter_by(estado=True).all()

        if not empleados:
            return jsonify({"horas_disponibles": []})

        # Obtener horarios y novedades para cada empleado en la fecha dada
        dia_semana = fecha.weekday()
        horarios_por_emp = {}
        novedades_por_emp = {}
        for emp in empleados:
            horarios_por_emp[emp.id] = Horario.query.filter_by(empleado_id=emp.id, activo=True).all()
            novedades_por_emp[emp.id] = Novedad.query.filter(
                Novedad.empleado_id == emp.id,
                Novedad.fecha_inicio <= fecha,
                Novedad.fecha_fin >= fecha,
                Novedad.activo == True
            ).all()

        # Obtener citas existentes ese día
        citas_por_empleado = {}
        todas_citas = Cita.query.filter(Cita.fecha == fecha).all()
        for cita in todas_citas:
            if cita.empleado_id not in citas_por_empleado:
                citas_por_empleado[cita.empleado_id] = []
            inicio_cita = datetime.combine(cita.fecha, cita.hora)
            fin_cita = inicio_cita + timedelta(minutes=cita.duracion or 30)
            citas_por_empleado[cita.empleado_id].append((inicio_cita, fin_cita))

        # Calcular rango horario global (el más temprano inicio y más tarde fin entre todos los horarios)
        hora_global_inicio = 24 * 60
        hora_global_fin = 0
        horario_empleado_dia = {}
        for emp in empleados:
            horario_dia = None
            for h in horarios_por_emp.get(emp.id, []):
                if h.dia == dia_semana and h.activo:
                    horario_dia = h
                    break
            if not horario_dia:
                continue
            inicio_min = horario_dia.hora_inicio.hour * 60 + horario_dia.hora_inicio.minute
            fin_min = horario_dia.hora_final.hour * 60 + horario_dia.hora_final.minute
            horario_empleado_dia[emp.id] = horario_dia
            if inicio_min < hora_global_inicio:
                hora_global_inicio = inicio_min
            if fin_min > hora_global_fin:
                hora_global_fin = fin_min

        if hora_global_inicio == 24 * 60 or hora_global_fin == 0:
            return jsonify({"horas_disponibles": []})

        # Generar horas candidatas según el intervalo
        horas_posibles = []
        current_min = hora_global_inicio
        while current_min + duracion <= hora_global_fin:
            h = current_min // 60
            m = current_min % 60
            horas_posibles.append(f"{h:02d}:{m:02d}")
            current_min += intervalo

        resultado = []
        for hora_str in horas_posibles:
            hora_time = datetime.strptime(hora_str, '%H:%M').time()
            inicio_solicitado = datetime.combine(fecha, hora_time)
            fin_solicitado = inicio_solicitado + timedelta(minutes=duracion)

            empleado_asignado = None
            for emp in empleados:
                horario_emp = horario_empleado_dia.get(emp.id)
                if not horario_emp:
                    continue

                # Verificar bloqueo por novedades
                bloqueado = False
                for nov in novedades_por_emp.get(emp.id, []):
                    if nov.hora_inicio is None and nov.hora_fin is None:
                        bloqueado = True
                        break
                    if nov.hora_inicio and nov.hora_fin:
                        if nov.hora_inicio <= hora_time <= nov.hora_fin:
                            bloqueado = True
                            break
                if bloqueado:
                    continue

                # Verificar dentro del horario laboral
                if hora_time < horario_emp.hora_inicio or hora_time > horario_emp.hora_final:
                    continue
                # Verificar que alcance a terminar antes de fin de jornada
                fin_jornada = datetime.combine(fecha, horario_emp.hora_final)
                if fin_solicitado > fin_jornada:
                    continue

                # Verificar solapamiento con otras citas
                conflicto = False
                for inicio_cita, fin_cita in citas_por_empleado.get(emp.id, []):
                    if inicio_solicitado < fin_cita and fin_solicitado > inicio_cita:
                        conflicto = True
                        break
                if conflicto:
                    continue

                empleado_asignado = emp.id
                break  # tomar el primer empleado disponible

            if empleado_asignado:
                resultado.append({"hora": hora_str, "empleado_id": empleado_asignado})

        return jsonify({
            "fecha": fecha_str,
            "servicio_id": servicio_id,
            "duracion": duracion,
            "intervalo_minutos": intervalo,
            "horas_disponibles": resultado
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================
# MÓDULO: ESTADOS DE CITA (permisos de citas)
# ============================================================

@main_bp.route('/estado-cita', methods=['GET'])
def get_estados_cita():
    """Listar estados de cita (público) con paginación y búsqueda."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        search = request.args.get('search', '', type=str).strip()

        query = EstadoCita.query
        if search:
            query = query.filter(EstadoCita.nombre.ilike(f"%{search}%"))
        query = query.order_by(EstadoCita.nombre.asc())

        if 'page' not in request.args and 'per_page' not in request.args and not search:
            estados = query.all()
            return jsonify([e.to_dict() for e in estados])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [e.to_dict() for e in pagination.items],
            'pagination': {
                'current_page': pagination.page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
        })
    except Exception as e:
        return jsonify({"error": "Error al obtener estados de cita"}), 500


@main_bp.route('/estado-cita', methods=['POST'])
@permiso_requerido("crear_citas")
def create_estado_cita():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400
        nombre = " ".join(data['nombre'].split()).strip()
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
@permiso_requerido("editar_citas")
def update_estado_cita(id):
    try:
        estado = EstadoCita.query.get(id)
        if not estado:
            return jsonify({"error": "Estado de cita no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data:
            nombre = " ".join(data['nombre'].split()).strip()
            existente = EstadoCita.query.filter(EstadoCita.nombre.ilike(nombre), EstadoCita.id != id).first()
            if existente:
                return jsonify({"error": "Ya existe otro estado con ese nombre"}), 400
            estado.nombre = nombre
        db.session.commit()
        return jsonify({"message": "Estado de cita actualizado", "estado": estado.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar estado de cita: {str(e)}"}), 500


@main_bp.route('/estado-cita/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_citas")
def delete_estado_cita(id):
    try:
        estado = EstadoCita.query.get(id)
        if not estado:
            return jsonify({"error": "Estado de cita no encontrado"}), 404
        if estado.citas and len(estado.citas) > 0:
            return jsonify({"error": "No se puede eliminar un estado que tiene citas asociadas"}), 400
        db.session.delete(estado)
        db.session.commit()
        return jsonify({"message": "Estado de cita eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar estado de cita: {str(e)}"}), 500


# ============================================================
# MÓDULO: NOVEDADES (permisos de empleados)
# ============================================================

@main_bp.route('/novedades', methods=['GET'])
@permiso_requerido("ver_empleados")
def get_novedades():
    """
    Listar novedades con paginación, búsqueda y filtros.
    Query params: page, per_page, search, empleado_id, tipo, activo
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        search = request.args.get('search', '', type=str).strip()
        empleado_id = request.args.get('empleado_id', type=int)
        tipo = request.args.get('tipo', '', type=str).strip()
        activo = request.args.get('activo', '', type=str).strip().lower()

        query = Novedad.query
        if empleado_id:
            query = query.filter(Novedad.empleado_id == empleado_id)
        if tipo:
            query = query.filter(Novedad.tipo == tipo)
        if activo != '':
            activo_bool = activo == 'true'
            query = query.filter(Novedad.activo == activo_bool)
        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(
                    Novedad.motivo.ilike(like),
                    Novedad.tipo.ilike(like)
                )
            )
        query = query.order_by(Novedad.fecha_inicio.desc())

        if 'page' not in request.args and 'per_page' not in request.args and not search and not empleado_id and not tipo and activo == '':
            novedades = query.all()
            return jsonify([n.to_dict() for n in novedades])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [n.to_dict() for n in pagination.items],
            'pagination': {
                'current_page': pagination.page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
        })
    except Exception as e:
        return jsonify({"error": "Error al obtener novedades"}), 500


@main_bp.route('/novedades/empleado/<int:empleado_id>', methods=['GET'])
@permiso_requerido("ver_empleados")
def get_novedades_por_empleado(empleado_id):
    try:
        novedades = Novedad.query.filter_by(empleado_id=empleado_id).all()
        return jsonify([n.to_dict() for n in novedades])
    except Exception as e:
        return jsonify({"error": "Error al obtener novedades"}), 500


@main_bp.route('/novedades', methods=['POST'])
@permiso_requerido("crear_empleados")
def create_novedad():
    try:
        data = request.get_json()
        required = ['empleado_id', 'fecha_inicio', 'fecha_fin', 'tipo']
        for field in required:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        empleado = Empleado.query.get(data['empleado_id'])
        if not empleado or not empleado.estado:
            return jsonify({"error": "Empleado no existe o está inactivo"}), 400

        try:
            fecha_inicio = datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400

        if fecha_inicio > fecha_fin:
            return jsonify({"error": "La fecha de inicio no puede ser posterior a la fecha de fin."}), 400

        hora_inicio = None
        hora_fin = None
        if data.get('hora_inicio'):
            try:
                hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
            except ValueError:
                return jsonify({"error": "Formato de hora inválido. Use HH:MM"}), 400
        if data.get('hora_fin'):
            try:
                hora_fin = datetime.strptime(data['hora_fin'], '%H:%M').time()
            except ValueError:
                return jsonify({"error": "Formato de hora inválido. Use HH:MM"}), 400
        if (hora_inicio and not hora_fin) or (hora_fin and not hora_inicio):
            return jsonify({"error": "Si especifica hora, debe proporcionar ambas (inicio y fin)"}), 400
        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            return jsonify({"error": "La hora final debe ser mayor que la hora inicio"}), 400

        novedad = Novedad(
            empleado_id=data['empleado_id'],
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            tipo=data['tipo'],
            motivo=data.get('motivo'),
            activo=data.get('activo', True)
        )
        db.session.add(novedad)
        db.session.commit()
        return jsonify({"message": "Novedad creada", "novedad": novedad.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear novedad: {str(e)}"}), 500


@main_bp.route('/novedades/<int:id>', methods=['PUT'])
@permiso_requerido("editar_empleados")
def update_novedad(id):
    try:
        novedad = Novedad.query.get(id)
        if not novedad:
            return jsonify({"error": "Novedad no encontrada"}), 404
        data = request.get_json()
        if 'empleado_id' in data:
            empleado = Empleado.query.get(data['empleado_id'])
            if not empleado or not empleado.estado:
                return jsonify({"error": "Empleado no válido o inactivo"}), 400
            novedad.empleado_id = data['empleado_id']
        if 'fecha_inicio' in data:
            try:
                novedad.fecha_inicio = datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido"}), 400
        if 'fecha_fin' in data:
            try:
                novedad.fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido"}), 400
        if 'hora_inicio' in data:
            if data['hora_inicio']:
                try:
                    novedad.hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
                except ValueError:
                    return jsonify({"error": "Formato de hora inválido"}), 400
            else:
                novedad.hora_inicio = None
        if 'hora_fin' in data:
            if data['hora_fin']:
                try:
                    novedad.hora_fin = datetime.strptime(data['hora_fin'], '%H:%M').time()
                except ValueError:
                    return jsonify({"error": "Formato de hora inválido"}), 400
            else:
                novedad.hora_fin = None
        if 'tipo' in data:
            novedad.tipo = data['tipo']
        if 'motivo' in data:
            novedad.motivo = data['motivo']
        if 'activo' in data:
            novedad.activo = data['activo']
        if novedad.fecha_inicio > novedad.fecha_fin:
            return jsonify({"error": "La fecha inicio no puede ser mayor a fecha fin"}), 400
        if novedad.hora_inicio and novedad.hora_fin and novedad.hora_fin <= novedad.hora_inicio:
            return jsonify({"error": "La hora final debe ser mayor que la hora inicio"}), 400
        if (novedad.hora_inicio and not novedad.hora_fin) or (novedad.hora_fin and not novedad.hora_inicio):
            return jsonify({"error": "Si especifica hora, debe proporcionar ambas"}), 400
        db.session.commit()
        return jsonify({"message": "Novedad actualizada", "novedad": novedad.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar novedad: {str(e)}"}), 500


@main_bp.route('/novedades/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_empleados")
def delete_novedad(id):
    try:
        novedad = Novedad.query.get(id)
        if not novedad:
            return jsonify({"error": "Novedad no encontrada"}), 404
        db.session.delete(novedad)
        db.session.commit()
        return jsonify({"message": "Novedad eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar novedad: {str(e)}"}), 500