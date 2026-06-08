"""
Módulo de campañas de salud.
Permisos granulares:
- Campañas: ver_campanas, crear_campanas, editar_campanas, eliminar_campanas
"""

from flask import jsonify, request
from app.database import db
from app.Models.models import CampanaSalud, EstadoCita, Empleado, Horario, Novedad, Cita
from datetime import datetime, timedelta
from app.routes import main_bp
from app.auth.decorators import permiso_requerido

MAX_PER_PAGE = 10

# Función auxiliar (copiada de r_agenda, pero adaptada)
def validar_disponibilidad_empleado(empleado_id, fecha, hora, duracion=60, exclude_campana_id=None):
    """Verifica disponibilidad para campañas (sin conflicto con citas y otras campañas)."""
    # Verificar novedades
    novedad = Novedad.query.filter(
        Novedad.empleado_id == empleado_id,
        Novedad.fecha_inicio <= fecha,
        Novedad.fecha_fin >= fecha,
        Novedad.activo == True
    ).first()
    if novedad:
        if novedad.hora_inicio is None and novedad.hora_fin is None:
            return {"disponible": False, "mensaje": "El empleado no está disponible (novedad todo el día)"}
        if novedad.hora_inicio and novedad.hora_fin:
            if novedad.hora_inicio <= hora <= novedad.hora_fin:
                return {"disponible": False, "mensaje": "El empleado no está disponible en ese horario por novedad"}
    # Horario laboral
    dia_semana = fecha.weekday()
    horario = Horario.query.filter_by(empleado_id=empleado_id, dia=dia_semana, activo=True).first()
    if not horario:
        return {"disponible": False, "mensaje": "El empleado no tiene horario configurado para este día"}
    if not (horario.hora_inicio <= hora <= horario.hora_final):
        return {"disponible": False, "mensaje": f"El empleado solo trabaja de {horario.hora_inicio.strftime('%H:%M')} a {horario.hora_final.strftime('%H:%M')}"}
    # Citas existentes
    inicio_solicitado = datetime.combine(fecha, hora)
    fin_solicitado = inicio_solicitado + timedelta(minutes=duracion)
    citas = Cita.query.filter(Cita.empleado_id == empleado_id, Cita.fecha == fecha).all()
    for cita in citas:
        inicio_cita = datetime.combine(cita.fecha, cita.hora)
        fin_cita = inicio_cita + timedelta(minutes=cita.duracion or 30)
        if inicio_solicitado < fin_cita and fin_solicitado > inicio_cita:
            return {"disponible": False, "mensaje": "El empleado ya tiene una cita en ese horario"}
    # Otras campañas del mismo empleado
    campanas_query = CampanaSalud.query.filter(
        CampanaSalud.empleado_id == empleado_id,
        CampanaSalud.fecha == fecha,
        CampanaSalud.hora == hora
    )
    if exclude_campana_id:
        campanas_query = campanas_query.filter(CampanaSalud.id != exclude_campana_id)
    if campanas_query.first():
        return {"disponible": False, "mensaje": "El empleado ya tiene otra campaña de salud en ese mismo horario"}
    return {"disponible": True, "mensaje": "Disponible"}

# ============================================================
# MÓDULO: CAMPAÑAS DE SALUD (permisos propios)
# ============================================================

@main_bp.route('/campanas-salud', methods=['GET'])
@permiso_requerido("ver_campanas")
def get_campanas_salud():
    """
    Listar campañas de salud con paginación, búsqueda y filtros.
    Query params:
        page          (int)
        per_page      (int) máx 10
        search        (str) busca en empresa, nit, contacto
        empleado_id   (int)
        estado_cita_id(int)
        fecha_desde   (str) YYYY-MM-DD
        fecha_hasta   (str)
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        search = request.args.get('search', '', type=str).strip()
        empleado_id = request.args.get('empleado_id', type=int)
        estado_cita_id = request.args.get('estado_cita_id', type=int)
        fecha_desde = request.args.get('fecha_desde', '', type=str).strip()
        fecha_hasta = request.args.get('fecha_hasta', '', type=str).strip()

        query = CampanaSalud.query
        if empleado_id:
            query = query.filter(CampanaSalud.empleado_id == empleado_id)
        if estado_cita_id:
            query = query.filter(CampanaSalud.estado_cita_id == estado_cita_id)
        if fecha_desde:
            try:
                fd = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                query = query.filter(CampanaSalud.fecha >= fd)
            except ValueError:
                return jsonify({"error": "Formato fecha_desde inválido"}), 400
        if fecha_hasta:
            try:
                fh = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                query = query.filter(CampanaSalud.fecha <= fh)
            except ValueError:
                return jsonify({"error": "Formato fecha_hasta inválido"}), 400
        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(
                    CampanaSalud.empresa.ilike(like),
                    CampanaSalud.nit_empresa.ilike(like),
                    CampanaSalud.contacto.ilike(like)
                )
            )
        query = query.order_by(CampanaSalud.fecha.desc(), CampanaSalud.hora.desc())

        has_pagination = 'page' in request.args or 'per_page' in request.args
        has_filters = empleado_id or estado_cita_id or fecha_desde or fecha_hasta or search
        if not has_pagination and not has_filters:
            campanas = query.all()
            return jsonify([campana.to_dict() for campana in campanas])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [campana.to_dict() for campana in pagination.items],
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
        return jsonify({"error": f"Error al obtener campañas: {str(e)}"}), 500


@main_bp.route('/campanas-salud/<int:id>', methods=['GET'])
@permiso_requerido("ver_campanas")
def get_campana_salud(id):
    try:
        campana = CampanaSalud.query.get(id)
        if not campana:
            return jsonify({"error": "Campaña no encontrada"}), 404
        return jsonify(campana.to_dict())
    except Exception as e:
        return jsonify({"error": f"Error al obtener campaña: {str(e)}"}), 500


@main_bp.route('/campanas-salud', methods=['POST'])
@permiso_requerido("crear_campanas")
def create_campana_salud():
    # ... (sin cambios)
    pass


@main_bp.route('/campanas-salud/<int:id>', methods=['PUT'])
@permiso_requerido("editar_campanas")
def update_campana_salud(id):
    # ... (sin cambios)
    pass


@main_bp.route('/campanas-salud/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_campanas")
def delete_campana_salud(id):
    # ... (sin cambios)
    pass


@main_bp.route('/empleados/<int:empleado_id>/campanas', methods=['GET'])
@permiso_requerido("ver_campanas")
def get_campanas_por_empleado(empleado_id):
    try:
        empleado = Empleado.query.get(empleado_id)
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404
        campanas = CampanaSalud.query.filter_by(empleado_id=empleado_id).order_by(CampanaSalud.fecha.desc(), CampanaSalud.hora.desc()).all()
        return jsonify([campana.to_dict() for campana in campanas])
    except Exception as e:
        return jsonify({"error": f"Error al obtener campañas del empleado: {str(e)}"}), 500