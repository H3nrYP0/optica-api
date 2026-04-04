from flask import Blueprint, jsonify, request
from app.database import db
from app.models import Servicio

servicio_bp = Blueprint('servicios', __name__)


@servicio_bp.route('', methods=['GET'])
def get_servicios():
    try:
        return jsonify([s.to_dict() for s in Servicio.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener servicios"}), 500


@servicio_bp.route('/<int:id>', methods=['GET'])
def get_servicio(id):
    try:
        servicio = Servicio.query.get(id)
        if not servicio:
            return jsonify({"error": "Servicio no encontrado"}), 404
        return jsonify(servicio.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@servicio_bp.route('', methods=['POST'])
def create_servicio():
    try:
        data = request.get_json()
        required = ['nombre', 'duracion_min', 'precio']
        for field in required:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        servicio = Servicio(
            nombre=data['nombre'],
            duracion_min=data['duracion_min'],
            precio=float(data['precio']),
            descripcion=data.get('descripcion', ''),
            estado=data.get('estado', True)
        )
        db.session.add(servicio)
        db.session.commit()
        return jsonify({"message": "Servicio creado", "servicio": servicio.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear servicio"}), 500


@servicio_bp.route('/<int:id>', methods=['PUT'])
def update_servicio(id):
    try:
        servicio = Servicio.query.get(id)
        if not servicio:
            return jsonify({"error": "Servicio no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data:       servicio.nombre = data['nombre']
        if 'duracion_min' in data: servicio.duracion_min = data['duracion_min']
        if 'precio' in data:       servicio.precio = float(data['precio'])
        if 'descripcion' in data:  servicio.descripcion = data['descripcion']
        if 'estado' in data:       servicio.estado = data['estado']
        db.session.commit()
        return jsonify({"message": "Servicio actualizado", "servicio": servicio.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar servicio"}), 500


@servicio_bp.route('/<int:id>', methods=['DELETE'])
def delete_servicio(id):
    try:
        servicio = Servicio.query.get(id)
        if not servicio:
            return jsonify({"error": "Servicio no encontrado"}), 404
        db.session.delete(servicio)
        db.session.commit()
        return jsonify({"message": "Servicio eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar servicio"}), 500
