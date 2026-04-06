from flask import jsonify, request
from app.database import db
from app.Models.models import Empleado
from datetime import datetime
from app.routes import main_bp

# ===== EMPLEADOS =====
@main_bp.route('/empleados', methods=['GET'])
def get_empleados():
    try:
        empleados = Empleado.query.all()
        return jsonify([empleado.to_dict() for empleado in empleados])
    except Exception as e:
        return jsonify({"error": "Error al obtener empleados"}), 500

@main_bp.route('/empleados', methods=['POST'])
def create_empleado():
    try:
        data = request.get_json()
        required_fields = ['nombre', 'numero_documento', 'fecha_ingreso']
        for field in required_fields:
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

@main_bp.route('/empleados/<int:id>', methods=['PUT'])
def update_empleado(id):
    try:
        empleado = Empleado.query.get(id)
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data:
            empleado.nombre = data['nombre']
        if 'tipo_documento' in data:
            empleado.tipo_documento = data['tipo_documento']
        if 'numero_documento' in data:
            empleado.numero_documento = data['numero_documento']
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
        return jsonify({"message": "Empleado actualizado", "empleado": empleado.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar empleado"}), 500

@main_bp.route('/empleados/<int:id>', methods=['DELETE'])
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