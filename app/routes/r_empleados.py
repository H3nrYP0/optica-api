from flask import jsonify, request
from app.database import db
from app.Models.models import Empleado, Cita, Horario
from datetime import datetime
from app.routes import main_bp
import re

# Regex para validar email
EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
# Regex para validar teléfono (solo números, 7-15 dígitos)
PHONE_REGEX = re.compile(r'^\d{7,15}$')


# ============================================================
# MÓDULO: EMPLEADOS
# ============================================================

@main_bp.route('/empleados', methods=['GET'])
def get_empleados():
    try:
        empleados = Empleado.query.all()
        return jsonify([empleado.to_dict() for empleado in empleados])
    except Exception as e:
        return jsonify({"error": f"Error al obtener empleados: {str(e)}"}), 500

@main_bp.route('/empleados/<int:id>', methods=['GET'])
def get_empleado(id):
    try:
        empleado = Empleado.query.get(id)
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404
        return jsonify(empleado.to_dict())
    except Exception as e:
        return jsonify({"error": f"Error al obtener empleado: {str(e)}"}), 500


@main_bp.route('/empleados', methods=['POST'])
def create_empleado():
    try:
        data = request.get_json()
        
        # 1. Validar campos requeridos
        required_fields = ['nombre', 'numero_documento', 'fecha_ingreso']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        
        # 2. Validar nombre no vacío
        nombre = data['nombre'].strip()
        if not nombre:
            return jsonify({"error": "El nombre del empleado no puede estar vacío"}), 400
        
        # 3. Validar documento duplicado
        numero_documento = str(data['numero_documento']).strip()
        if not numero_documento:
            return jsonify({"error": "El número de documento no puede estar vacío"}), 400
        
        if Empleado.query.filter_by(numero_documento=numero_documento).first():
            return jsonify({"error": f"Ya existe un empleado con el documento {numero_documento}"}), 400
        
        # 4. Validar email (si se proporciona)
        correo = data.get('correo', '').strip()
        if correo and not EMAIL_REGEX.match(correo):
            return jsonify({"error": "Formato de correo electrónico inválido"}), 400
        
        # 5. Validar teléfono (si se proporciona)
        telefono = data.get('telefono', '').strip()
        if telefono and not PHONE_REGEX.match(telefono):
            return jsonify({"error": "El teléfono debe contener solo números (7-15 dígitos)"}), 400
        
        # 6. Validar fecha de ingreso (no puede ser futura)
        try:
            fecha_ingreso = datetime.strptime(data['fecha_ingreso'], '%Y-%m-%d').date()
            if fecha_ingreso > datetime.now().date():
                return jsonify({"error": "La fecha de ingreso no puede ser futura"}), 400
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
        
        # 7. Validar cargo (si se proporciona, longitud)
        cargo = data.get('cargo', '').strip()
        if cargo and len(cargo) > 50:
            return jsonify({"error": "El cargo no puede tener más de 50 caracteres"}), 400
        
        empleado = Empleado(
            nombre=nombre,
            tipo_documento=data.get('tipo_documento', '').strip(),
            numero_documento=numero_documento,
            telefono=telefono if telefono else None,
            correo=correo if correo else None,
            direccion=data.get('direccion', '').strip(),
            fecha_ingreso=fecha_ingreso,
            cargo=cargo if cargo else None,
            estado=data.get('estado', True)
        )
        
        db.session.add(empleado)
        db.session.commit()
        return jsonify({"message": "Empleado creado", "empleado": empleado.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear empleado: {str(e)}"}), 500


@main_bp.route('/empleados/<int:id>', methods=['PUT'])
def update_empleado(id):
    try:
        empleado = Empleado.query.get(id)
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404
        
        data = request.get_json()
        
        # Validar nombre
        if 'nombre' in data:
            nombre = data['nombre'].strip()
            if not nombre:
                return jsonify({"error": "El nombre del empleado no puede estar vacío"}), 400
            empleado.nombre = nombre
        
        # Validar documento duplicado si se actualiza
        if 'numero_documento' in data:
            nuevo_doc = str(data['numero_documento']).strip()
            if not nuevo_doc:
                return jsonify({"error": "El número de documento no puede estar vacío"}), 400
            
            existente = Empleado.query.filter(
                Empleado.numero_documento == nuevo_doc, 
                Empleado.id != id
            ).first()
            if existente:
                return jsonify({"error": "Ese número de documento ya está asignado a otro empleado"}), 400
            empleado.numero_documento = nuevo_doc
        
        # Validar email
        if 'correo' in data:
            correo = data['correo'].strip() if data['correo'] else None
            if correo and not EMAIL_REGEX.match(correo):
                return jsonify({"error": "Formato de correo electrónico inválido"}), 400
            empleado.correo = correo
        
        # Validar teléfono
        if 'telefono' in data:
            telefono = data['telefono'].strip() if data['telefono'] else None
            if telefono and not PHONE_REGEX.match(telefono):
                return jsonify({"error": "El teléfono debe contener solo números (7-15 dígitos)"}), 400
            empleado.telefono = telefono
        
        # Validar fecha de ingreso
        if 'fecha_ingreso' in data:
            try:
                fecha_ingreso = datetime.strptime(data['fecha_ingreso'], '%Y-%m-%d').date()
                if fecha_ingreso > datetime.now().date():
                    return jsonify({"error": "La fecha de ingreso no puede ser futura"}), 400
                empleado.fecha_ingreso = fecha_ingreso
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
        
        # Validar cargo
        if 'cargo' in data:
            cargo = data['cargo'].strip() if data['cargo'] else None
            if cargo and len(cargo) > 50:
                return jsonify({"error": "El cargo no puede tener más de 50 caracteres"}), 400
            empleado.cargo = cargo
        
        # Validar estado: No desactivar si tiene citas pendientes o activas
        if 'estado' in data and not data['estado']:
            # Verificar si tiene citas pendientes
            citas_pendientes = Cita.query.filter(
                Cita.empleado_id == id,
                Cita.estado_cita_id == 1  # 1 = pendiente
            ).first()
            
            if citas_pendientes:
                return jsonify({
                    "error": "No se puede desactivar el empleado porque tiene citas pendientes"
                }), 400
            
            # Verificar si tiene horarios activos
            horarios_activos = Horario.query.filter_by(empleado_id=id, activo=True).first()
            if horarios_activos:
                return jsonify({
                    "error": "No se puede desactivar el empleado porque tiene horarios activos. Desactive los horarios primero."
                }), 400
        
        # Actualizar campos simples
        if 'tipo_documento' in data:
            empleado.tipo_documento = data['tipo_documento'].strip()
        if 'direccion' in data:
            empleado.direccion = data['direccion'].strip()
        if 'estado' in data:
            empleado.estado = data['estado']
        
        db.session.commit()
        return jsonify({"message": "Empleado actualizado", "empleado": empleado.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar empleado: {str(e)}"}), 500


@main_bp.route('/empleados/<int:id>', methods=['DELETE'])
def delete_empleado(id):
    try:
        empleado = Empleado.query.get(id)
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404
        
        # 1. Verificar si el empleado tiene citas asociadas (cualquier estado)
        tiene_citas = Cita.query.filter_by(empleado_id=id).first()
        if tiene_citas:
            return jsonify({
                "error": "No se puede eliminar el empleado: Tiene citas registradas. Desactívelo para ocultarlo de la lista."
            }), 400
        
        # 2. Verificar si el empleado tiene horarios asociados
        tiene_horarios = Horario.query.filter_by(empleado_id=id).first()
        if tiene_horarios:
            return jsonify({
                "error": "No se puede eliminar el empleado: Tiene horarios registrados. Elimine los horarios primero."
            }), 400
        
        # 3. Verificar si el empleado tiene campañas asociadas
        tiene_campanas = empleado.campanas_salud and len(empleado.campanas_salud) > 0
        if tiene_campanas:
            return jsonify({
                "error": "No se puede eliminar el empleado: Tiene campañas de salud asociadas. Desactívelo en su lugar."
            }), 400
        
        # 4. Verificar si el empleado está activo (no se puede eliminar si está activo)
        if empleado.estado:
            return jsonify({
                "error": "Debes desactivar el empleado antes de eliminarlo"
            }), 400
        
        db.session.delete(empleado)
        db.session.commit()
        return jsonify({"message": "Empleado eliminado correctamente"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar empleado: {str(e)}"}), 500