from flask import jsonify, request
from app.database import db
from app.Models.models import CampanaSalud, EstadoCita, Empleado
from datetime import datetime
from app.routes import main_bp


# ============================================================
# MÓDULO: CAMPAÑAS DE SALUD
# ============================================================

@main_bp.route('/campanas-salud', methods=['GET'])
def get_campanas_salud():
    try:
        campanas = CampanaSalud.query.all()
        return jsonify([campana.to_dict() for campana in campanas])
    except Exception as e:
        return jsonify({"error": "Error al obtener campañas"}), 500


@main_bp.route('/campanas-salud/<int:id>', methods=['GET'])
def get_campana_salud(id):
    try:
        campana = CampanaSalud.query.get(id)
        if not campana:
            return jsonify({"error": "Campaña no encontrada"}), 404
        return jsonify(campana.to_dict())
    except Exception as e:
        return jsonify({"error": f"Error al obtener campaña: {str(e)}"}), 500


@main_bp.route('/campanas-salud', methods=['POST'])
def create_campana_salud():
    try:
        data = request.get_json()
        
        # 1. Validar campos obligatorios
        required_fields = ['empleado_id', 'empresa', 'fecha', 'hora']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"El campo '{field}' es requerido"}), 400
        
        # 2. Validar que el empleado existe y está ACTIVO
        empleado = Empleado.query.get(data['empleado_id'])
        if not empleado:
            return jsonify({"error": "El empleado especificado no existe"}), 404
        if hasattr(empleado, 'estado') and not empleado.estado:
            return jsonify({"error": "No se puede asignar una campaña a un empleado inactivo"}), 400
        
        # 3. Validar estado_cita_id (por defecto 2)
        estado_cita_id = data.get('estado_cita_id', 2)
        estado_cita = EstadoCita.query.get(estado_cita_id)
        if not estado_cita:
            return jsonify({"error": "El estado de cita especificado no existe"}), 400
        
        # 4. Validar formato de fecha y hora
        try:
            fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
            hora = datetime.strptime(data['hora'], '%H:%M').time()
        except ValueError:
            return jsonify({"error": "Formato inválido. Use YYYY-MM-DD para fecha y HH:MM para hora"}), 400
        
        # 5. Validar que la fecha no sea en el pasado (opcional)
        fecha_actual = datetime.now().date()
        if fecha < fecha_actual:
            return jsonify({"error": "No se pueden crear campañas en fechas pasadas"}), 400
        
        # 6. Validar que la empresa no esté vacía
        empresa = data['empresa'].strip()
        if not empresa:
            return jsonify({"error": "El nombre de la empresa es obligatorio"}), 400
        
        campana = CampanaSalud(
            empleado_id=data['empleado_id'],
            empresa=empresa,
            contacto=data.get('contacto', '').strip(),
            fecha=fecha,
            hora=hora,
            direccion=data.get('direccion', '').strip(),
            observaciones=data.get('observaciones', '').strip(),
            estado_cita_id=estado_cita_id
        )
        
        db.session.add(campana)
        db.session.commit()
        return jsonify({"message": "Campaña creada", "campana": campana.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear campaña: {str(e)}"}), 500

@main_bp.route('/campanas-salud/<int:id>', methods=['PUT'])
def update_campana_salud(id):
    try:
        campana = CampanaSalud.query.get(id)
        if not campana:
            return jsonify({"error": "Campaña no encontrada"}), 404
            
        data = request.get_json()
        
        # Validar y actualizar empleado
        if 'empleado_id' in data:
            nuevo_empleado = Empleado.query.get(data['empleado_id'])
            if not nuevo_empleado:
                return jsonify({"error": "El empleado especificado no existe"}), 404
            if hasattr(nuevo_empleado, 'estado') and not nuevo_empleado.estado:
                return jsonify({"error": "No se puede asignar una campaña a un empleado inactivo"}), 400
            campana.empleado_id = data['empleado_id']
        
        # Validar y actualizar empresa
        if 'empresa' in data:
            empresa = data['empresa'].strip()
            if not empresa:
                return jsonify({"error": "El nombre de la empresa no puede estar vacío"}), 400
            campana.empresa = empresa
            
        # Actualizar contacto
        if 'contacto' in data:
            campana.contacto = data['contacto'].strip()
            
        # Validar y actualizar fecha
        if 'fecha' in data:
            try:
                nueva_fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
                # Validar que no sea en el pasado (si la fecha está cambiando)
                fecha_actual = datetime.now().date()
                if nueva_fecha < fecha_actual:
                    return jsonify({"error": "No se puede reprogramar a una fecha pasada"}), 400
                campana.fecha = nueva_fecha
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido (use YYYY-MM-DD)"}), 400
                
        # Validar y actualizar hora
        if 'hora' in data:
            try:
                campana.hora = datetime.strptime(data['hora'], '%H:%M').time()
            except ValueError:
                return jsonify({"error": "Formato de hora inválido (use HH:MM)"}), 400
                
        # Actualizar dirección
        if 'direccion' in data:
            campana.direccion = data['direccion'].strip()
            
        # Actualizar observaciones
        if 'observaciones' in data:
            campana.observaciones = data['observaciones'].strip()
            
        # Validar y actualizar estado_cita_id
        if 'estado_cita_id' in data:
            estado_cita = EstadoCita.query.get(data['estado_cita_id'])
            if not estado_cita:
                return jsonify({"error": "El estado de cita especificado no existe"}), 400
            campana.estado_cita_id = data['estado_cita_id']
            
        db.session.commit()
        return jsonify({"message": "Campaña actualizada", "campana": campana.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar campaña: {str(e)}"}), 500


@main_bp.route('/campanas-salud/<int:id>', methods=['DELETE'])
def delete_campana_salud(id):
    try:
        campana = CampanaSalud.query.get(id)
        if not campana:
            return jsonify({"error": "Campaña no encontrada"}), 404
        
        # Validación opcional: No eliminar campañas completadas
        if campana.estado_cita_id:
            estado = EstadoCita.query.get(campana.estado_cita_id)
            if estado and estado.nombre.lower() == 'completada':
                return jsonify({"error": "No se puede eliminar una campaña que ya está completada"}), 400
            
        db.session.delete(campana)
        db.session.commit()
        return jsonify({"message": "Campaña eliminada correctamente"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar campaña: {str(e)}"}), 500


@main_bp.route('/empleados/<int:empleado_id>/campanas', methods=['GET'])
def get_campanas_por_empleado(empleado_id):
    try:
        # Validar que el empleado existe
        empleado = Empleado.query.get(empleado_id)
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404
            
        campanas = CampanaSalud.query.filter_by(empleado_id=empleado_id).all()
        return jsonify([campana.to_dict() for campana in campanas])
        
    except Exception as e:
        return jsonify({"error": f"Error al obtener campañas del empleado: {str(e)}"}), 500