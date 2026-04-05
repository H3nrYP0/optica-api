from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Empleado, Cita
from datetime import datetime

empleado_bp = Blueprint('empleados', __name__)

@empleado_bp.route('', methods=['GET'])
def get_empleados():
    try:
        empleados = Empleado.query.all()
        return jsonify([empleado.to_dict() for empleado in empleados]), 200
    except Exception as e:
        return jsonify({"error": f"Error al obtener empleados: {str(e)}"}), 500

@empleado_bp.route('', methods=['POST'])
def create_empleado():
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['nombre', 'numero_documento', 'fecha_ingreso']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        # Validar documento duplicado
        numero_doc = str(data.get('numero_documento', '')).strip()
        if Empleado.query.filter_by(numero_documento=numero_doc).first():
            return jsonify({"error": f"Ya existe un empleado con el documento {numero_doc}"}), 400

        # Convertir fecha
        fecha_ingreso = datetime.strptime(data['fecha_ingreso'], '%Y-%m-%d').date()
        
        empleado = Empleado(
            nombre=data['nombre'].strip(),
            tipo_documento=data.get('tipo_documento'),
            numero_documento=numero_doc,
            telefono=data.get('telefono'),
            correo=data.get('correo'),
            direccion=data.get('direccion'),
            fecha_ingreso=fecha_ingreso,
            cargo=data.get('cargo'),
            estado=data.get('estado', True)
        )
        
        db.session.add(empleado)
        db.session.commit()
        return jsonify(empleado.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear empleado: {str(e)}"}), 500

@empleado_bp.route('/<int:id>', methods=['PUT'])
def update_empleado(id):
    try:
        empleado = db.session.get(Empleado, id)
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404

        data = request.get_json()
        
        # Validar documento duplicado si se actualiza
        if 'numero_documento' in data:
            nuevo_doc = str(data['numero_documento']).strip()
            existente = Empleado.query.filter(
                Empleado.numero_documento == nuevo_doc, 
                Empleado.id != id
            ).first()
            if existente:
                return jsonify({"error": "Ese número de documento ya está asignado a otro empleado"}), 400
            empleado.numero_documento = nuevo_doc
        
        # Actualizar campos
        if 'nombre' in data:
            empleado.nombre = data['nombre'].strip()
        if 'tipo_documento' in data:
            empleado.tipo_documento = data['tipo_documento']
        if 'telefono' in data:
            empleado.telefono = data['telefono']
        if 'correo' in data:
            empleado.correo = data['correo']
        if 'direccion' in data:
            empleado.direccion = data['direccion']
        if 'fecha_ingreso' in data:
            empleado.fecha_ingreso = datetime.strptime(data['fecha_ingreso'], '%Y-%m-%d').date()
        if 'cargo' in data:
            empleado.cargo = data['cargo']
        if 'estado' in data:
            empleado.estado = data['estado']

        db.session.commit()
        return jsonify(empleado.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar empleado: {str(e)}"}), 500

@empleado_bp.route('/<int:id>', methods=['DELETE'])
def delete_empleado(id):
    try:
        empleado = db.session.get(Empleado, id)
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404

        # Verificar si el empleado tiene citas asociadas
        tiene_citas = Cita.query.filter_by(empleado_id=id).first()
        
        if tiene_citas:
            return jsonify({
                "error": "No se puede eliminar el empleado: Tiene citas registradas. Desactívelo para ocultarlo de la lista."
            }), 400

        db.session.delete(empleado)
        db.session.commit()
        return jsonify({"message": "Empleado eliminado correctamente"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar empleado: {str(e)}"}), 500