from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import CategoriaProducto, Multimedia

categoria_bp = Blueprint('categorias', __name__)

@categoria_bp.route('', methods=['GET'])
def get_categorias():
    try:
        return jsonify([c.to_dict() for c in CategoriaProducto.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener categorías"}), 500

@categoria_bp.route('', methods=['POST'])
def create_categoria():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400
        categoria = CategoriaProducto(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', ''),
            estado=data.get('estado', True)
        )
        db.session.add(categoria)
        db.session.commit()
        return jsonify({"message": "Categoría creada", "categoria": categoria.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear categoría"}), 500

@categoria_bp.route('/<int:id>', methods=['PUT'])
def update_categoria(id):
    try:
        categoria = CategoriaProducto.query.get(id)
        if not categoria:
            return jsonify({"error": "Categoría no encontrada"}), 404
        data = request.get_json()
        if 'nombre' in data:
            categoria.nombre = data['nombre']
        if 'descripcion' in data:
            categoria.descripcion = data['descripcion']
        if 'estado' in data:
            categoria.estado = data['estado']
        db.session.commit()
        return jsonify({"message": "Categoría actualizada", "categoria": categoria.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar categoría"}), 500

@categoria_bp.route('/<int:id>', methods=['DELETE'])
def delete_categoria(id):
    try:
        categoria = CategoriaProducto.query.get(id)
        if not categoria:
            return jsonify({"error": "Categoría no encontrada"}), 404
        db.session.delete(categoria)
        db.session.commit()
        return jsonify({"message": "Categoría eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar categoría"}), 500

@categoria_bp.route('-con-imagen', methods=['GET'])
def categorias_con_imagen():
    try:
        categorias = CategoriaProducto.query.all()
        resultado = []
        for categoria in categorias:
            cat_dict = categoria.to_dict()
            imagen = Multimedia.query.filter_by(tipo='categoria', categoria_id=categoria.id).first()
            cat_dict['imagen_url'] = imagen.url if imagen else None
            resultado.append(cat_dict)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500