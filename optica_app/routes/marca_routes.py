from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Marca

marca_bp = Blueprint('marcas', __name__)

@marca_bp.route('', methods=['GET'])
def get_marcas():
    try:
        return jsonify([m.to_dict() for m in Marca.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener marcas"}), 500

@marca_bp.route('', methods=['POST'])
def create_marca():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400
        marca = Marca(nombre=data['nombre'], estado=data.get('estado', True))
        db.session.add(marca)
        db.session.commit()
        return jsonify({"message": "Marca creada", "marca": marca.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear marca"}), 500

@marca_bp.route('/<int:id>', methods=['PUT'])
def update_marca(id):
    try:
        marca = Marca.query.get(id)
        if not marca:
            return jsonify({"error": "Marca no encontrada"}), 404
        data = request.get_json()
        if 'nombre' in data:
            marca.nombre = data['nombre']
        if 'estado' in data:
            marca.estado = data['estado']
        db.session.commit()
        return jsonify({"message": "Marca actualizada", "marca": marca.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar marca"}), 500

@marca_bp.route('/<int:id>', methods=['DELETE'])
def delete_marca(id):
    try:
        marca = Marca.query.get(id)
        if not marca:
            return jsonify({"error": "Marca no encontrada"}), 404
        db.session.delete(marca)
        db.session.commit()
        return jsonify({"message": "Marca eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar marca"}), 500