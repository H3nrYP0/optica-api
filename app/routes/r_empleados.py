"""
Módulo de empleados, horarios y novedades.
Permisos granulares:
- Empleados: ver_empleados, crear_empleados, editar_empleados, eliminar_empleados
- Horarios y novedades: mismos permisos de empleados
"""

from flask import jsonify, request
from app.database import db
from app.Models.models import Empleado, Cita, Horario, Novedad
from datetime import datetime
from app.routes import main_bp
from app.auth.decorators import permiso_requerido
import re

EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
PHONE_REGEX = re.compile(r'^\d{7,15}$')

# ============================================================
# MÓDULO: EMPLEADOS (CRUD)
# ============================================================

@main_bp.route('/empleados', methods=['GET'])
@permiso_requerido("ver_empleados")
def get_empleados():
    try:
        empleados = Empleado.query.order_by(Empleado.id.desc()).all()
        return jsonify([e.to_dict() for e in empleados])
    except Exception as e:
        return jsonify({"error": "Error interno al obtener empleados", "detalle": str(e)}), 500

@main_bp.route('/empleados/<int:id>', methods=['GET'])
@permiso_requerido("ver_empleados")
def get_empleado(id):
    try:
        empleado = Empleado.query.get(id)
        if not empleado:
            return jsonify({"error": f"No existe un empleado con ID {id}"}), 404
        return jsonify(empleado.to_dict())
    except Exception as e:
        return jsonify({"error": "Error interno al obtener empleado", "detalle": str(e)}), 500

@main_bp.route('/empleados', methods=['POST'])
@permiso_requerido("crear_empleados")
def create_empleado():
    try:
        data = request.get_json()
        required_fields = ['nombre', 'apellido', 'numero_documento', 'fecha_ingreso']
        for field in required_fields:
            if not data.get(field, ''):
                return jsonify({"error": f"El campo '{field}' es obligatorio."}), 400
        nombre = data['nombre'].strip()
        apellido = data['apellido'].strip()
        numero_documento = str(data['numero_documento']).strip()
        if not nombre or not apellido:
            return jsonify({"error": "Nombre y apellido son requeridos"}), 400
        if Empleado.query.filter_by(numero_documento=numero_documento).first():
            return jsonify({"error": f"El documento '{numero_documento}' ya está registrado."}), 400
        correo = data.get('correo', '').strip() or None
        if correo:
            if not EMAIL_REGEX.match(correo):
                return jsonify({"error": f"El correo '{correo}' no tiene un formato válido."}), 400
            if Empleado.query.filter_by(correo=correo).first():
                return jsonify({"error": f"El correo '{correo}' ya está registrado para otro empleado."}), 400
        telefono = data.get('telefono', '').strip() or None
        if telefono and not PHONE_REGEX.match(telefono):
            return jsonify({"error": "El teléfono debe contener solo números y tener entre 7 y 15 dígitos."}), 400
        try:
            fecha_ingreso = datetime.strptime(data['fecha_ingreso'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "La fecha de ingreso debe tener el formato YYYY-MM-DD."}), 400
        if fecha_ingreso > datetime.now().date():
            return jsonify({"error": "La fecha de ingreso no puede ser una fecha futura."}), 400
        empleado = Empleado(
            nombre=nombre, apellido=apellido,
            tipo_documento=data.get('tipo_documento', '').strip() or None,
            numero_documento=numero_documento,
            telefono=telefono, correo=correo,
            direccion=data.get('direccion', '').strip() or None,
            fecha_ingreso=fecha_ingreso,
            cargo=data.get('cargo', '').strip() or None,
            estado=data.get('estado', True)
        )
        db.session.add(empleado)
        db.session.commit()
        return jsonify({"message": "Empleado creado exitosamente", "empleado": empleado.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error interno al crear empleado", "detalle": str(e)}), 500

@main_bp.route('/empleados/<int:id>', methods=['PUT'])
@permiso_requerido("editar_empleados")
def update_empleado(id):
    try:
        empleado = Empleado.query.get(id)
        if not empleado:
            return jsonify({"error": f"No existe un empleado con ID {id}"}), 404
        data = request.get_json()
        if 'nombre' in data:
            nombre = data['nombre'].strip()
            if not nombre:
                return jsonify({"error": "El nombre no puede estar vacío."}), 400
            empleado.nombre = nombre
        if 'apellido' in data:
            apellido = data['apellido'].strip()
            if not apellido:
                return jsonify({"error": "El apellido no puede estar vacío."}), 400
            empleado.apellido = apellido
        if 'numero_documento' in data:
            nuevo_doc = str(data['numero_documento']).strip()
            if not nuevo_doc:
                return jsonify({"error": "El número de documento no puede estar vacío."}), 400
            existente = Empleado.query.filter(Empleado.numero_documento == nuevo_doc, Empleado.id != id).first()
            if existente:
                return jsonify({"error": f"El documento '{nuevo_doc}' ya está asignado a otro empleado."}), 400
            empleado.numero_documento = nuevo_doc
        if 'correo' in data:
            correo = data['correo'].strip() if data['correo'] else None
            if correo:
                if not EMAIL_REGEX.match(correo):
                    return jsonify({"error": "Formato de correo inválido."}), 400
                existe = Empleado.query.filter(Empleado.correo == correo, Empleado.id != id).first()
                if existe:
                    return jsonify({"error": f"El correo '{correo}' ya está registrado para otro empleado."}), 400
            empleado.correo = correo
        if 'telefono' in data:
            telefono = data['telefono'].strip() if data['telefono'] else None
            if telefono and not PHONE_REGEX.match(telefono):
                return jsonify({"error": "Teléfono inválido (solo números, 7-15 dígitos)."}), 400
            empleado.telefono = telefono
        if 'fecha_ingreso' in data:
            try:
                fecha_ingreso = datetime.strptime(data['fecha_ingreso'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}), 400
            if fecha_ingreso > datetime.now().date():
                return jsonify({"error": "La fecha de ingreso no puede ser futura."}), 400
            empleado.fecha_ingreso = fecha_ingreso
        if 'tipo_documento' in data:
            empleado.tipo_documento = data['tipo_documento'].strip() or None
        if 'direccion' in data:
            empleado.direccion = data['direccion'].strip() or None
        if 'cargo' in data:
            empleado.cargo = data['cargo'].strip() or None
        if 'estado' in data and not data['estado']:
            if Cita.query.filter(Cita.empleado_id == id, Cita.estado_cita_id == 1).first():
                return jsonify({"error": "No se puede desactivar: el empleado tiene citas pendientes."}), 400
            if Horario.query.filter_by(empleado_id=id, activo=True).first():
                return jsonify({"error": "No se puede desactivar: el empleado tiene horarios activos."}), 400
            empleado.estado = False
        elif 'estado' in data:
            empleado.estado = data['estado']
        db.session.commit()
        return jsonify({"message": "Empleado actualizado correctamente", "empleado": empleado.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error interno al actualizar empleado", "detalle": str(e)}), 500

@main_bp.route('/empleados/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_empleados")
def delete_empleado(id):
    try:
        empleado = Empleado.query.get(id)
        if not empleado:
            return jsonify({"error": f"No existe un empleado con ID {id}"}), 404
        if empleado.estado:
            return jsonify({"error": "Debes desactivar el empleado antes de eliminarlo."}), 400
        if Cita.query.filter_by(empleado_id=id).first():
            return jsonify({"error": "No se puede eliminar: tiene citas registradas. Desactívelo."}), 400
        if Horario.query.filter_by(empleado_id=id).first():
            return jsonify({"error": "No se puede eliminar: tiene horarios registrados."}), 400
        if empleado.campanas_salud and len(empleado.campanas_salud) > 0:
            return jsonify({"error": "No se puede eliminar: tiene campañas de salud asociadas."}), 400
        db.session.delete(empleado)
        db.session.commit()
        return jsonify({"message": "Empleado eliminado permanentemente."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error interno al eliminar empleado", "detalle": str(e)}), 500

# ============================================================
# NOTA: Los endpoints de Horarios y Novedades ya están en r_agenda.py
# con los permisos de empleados (ver_empleados, crear_empleados, etc.)
# ============================================================