from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import CampanaSalud, Empleado, EstadoCita
from datetime import datetime

campana_bp = Blueprint('campanas', __name__)

@campana_bp.route('', methods=['GET'])
def get_campanas():
    """Obtiene todas las campañas con sus relaciones cargadas."""
    try:
        campanas = CampanaSalud.query.all()
        return jsonify([c.to_dict() for c in campanas]), 200
    except Exception as e:
        return jsonify({"error": f"Error al obtener campañas: {str(e)}"}), 500

@campana_bp.route('/<int:id>', methods=['GET'])
def get_campana(id):
    """Obtiene una campaña específica por ID."""
    try:
        campana = CampanaSalud.query.get(id)
        if not campana:
            return jsonify({"error": "Campaña no encontrada"}), 404
        return jsonify(campana.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@campana_bp.route('', methods=['POST'])
def create_campana():
    """Crea una nueva campaña con validaciones de integridad y personal activo."""
    try:
        data = request.get_json()
        
        # 1. Validar campos obligatorios
        required = ['empleado_id', 'empresa', 'fecha', 'hora']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({"error": f"El campo '{field}' es requerido"}), 400

        # 2. BLINDAJE: Validar que el empleado existe y está ACTIVO
        empleado = Empleado.query.get(data['empleado_id'])
        if not empleado:
            return jsonify({"error": "El empleado especificado no existe"}), 404
        if hasattr(empleado, 'estado') and not empleado.estado:
            return jsonify({"error": "No se puede asignar una campaña a un empleado inactivo"}), 400

        # 3. BLINDAJE: Validar que el estado de cita existe (Por defecto 2: Programada)
        estado_id = data.get('estado_cita_id', 2)
        if not EstadoCita.query.get(estado_id):
            return jsonify({"error": "El estado de cita especificado no existe"}), 400

        # 4. Procesar fechas y horas (Manejo estricto de formatos)
        try:
            # .date() y .time() para asegurar compatibilidad con SQLAlchemy
            fecha_obj = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
            hora_obj = datetime.strptime(data['hora'], '%H:%M').time()
        except ValueError:
            return jsonify({"error": "Formato inválido. Use YYYY-MM-DD para fecha y HH:MM para hora"}), 400

        nueva_campana = CampanaSalud(
            empleado_id=data['empleado_id'],
            empresa=data['empresa'],
            contacto=data.get('contacto'),
            fecha=fecha_obj,
            hora=hora_obj,
            direccion=data.get('direccion'),
            observaciones=data.get('observaciones'),
            estado_cita_id=estado_id
        )

        db.session.add(nueva_campana)
        db.session.commit()
        
        return jsonify({
            "message": "Campaña creada exitosamente", 
            "campana": nueva_campana.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear campaña: {str(e)}"}), 500

@campana_bp.route('/<int:id>', methods=['PUT'])
def update_campana(id):
    """Actualiza una campaña existente validando nuevas asignaciones y estados."""
    try:
        campana = CampanaSalud.query.get(id)
        if not campana:
            return jsonify({"error": "Campaña no encontrada"}), 404

        data = request.get_json()

        # BLINDAJE: Validación de cambio de empleado
        if 'empleado_id' in data:
            nuevo_emp = Empleado.query.get(data['empleado_id'])
            if not nuevo_emp or (hasattr(nuevo_emp, 'estado') and not nuevo_emp.estado):
                return jsonify({"error": "Empleado inválido o inactivo"}), 400
            campana.empleado_id = data['empleado_id']

        # BLINDAJE: Validación de estado de cita
        if 'estado_cita_id' in data:
            if not EstadoCita.query.get(data['estado_cita_id']):
                return jsonify({"error": "Estado de cita no existe"}), 400
            campana.estado_cita_id = data['estado_cita_id']

        # Actualización de datos generales
        if 'empresa' in data: campana.empresa = data['empresa']
        if 'contacto' in data: campana.contacto = data['contacto']
        if 'direccion' in data: campana.direccion = data['direccion']
        if 'observaciones' in data: campana.observaciones = data['observaciones']
        
        # Actualización de tiempo
        if 'fecha' in data:
            campana.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        if 'hora' in data:
            campana.hora = datetime.strptime(data['hora'], '%H:%M').time()

        db.session.commit()
        return jsonify({
            "message": "Campaña actualizada exitosamente", 
            "campana": campana.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar: {str(e)}"}), 500

@campana_bp.route('/<int:id>', methods=['DELETE'])
def delete_campana(id):
    """Elimina una campaña de forma segura."""
    try:
        campana = CampanaSalud.query.get(id)
        if not campana:
            return jsonify({"error": "Campaña no encontrada"}), 404
        
        db.session.delete(campana)
        db.session.commit()
        return jsonify({"message": "Campaña eliminada correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500