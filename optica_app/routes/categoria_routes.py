from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import CategoriaProducto

categoria_bp = Blueprint('categorias', __name__)

@categoria_bp.route('', methods=['POST'])
def create_categoria():
    try:
        data = request.get_json()
        nombre = " ".join(data.get('nombre', '').split()).strip()
        
        if not nombre:
            return jsonify({"error": "El nombre de categoría es obligatorio"}), 400

        if CategoriaProducto.query.filter(CategoriaProducto.nombre.ilike(nombre)).first():
            return jsonify({"error": "Esta categoría ya existe"}), 400

        nueva = CategoriaProducto(
            nombre=nombre,
            descripcion=data.get('descripcion', '').strip(),
            estado=data.get('estado', True)
        )
        db.session.add(nueva)
        db.session.commit()
        return jsonify(nueva.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@categoria_bp.route('/<int:id>', methods=['DELETE'])
def delete_categoria(id):
    try:
        cat = db.session.get(CategoriaProducto, id)
        if not cat: return jsonify({"error": "Categoría no encontrada"}), 404

        if cat.productos:
            return jsonify({"error": "Imposible eliminar: Categoría con productos asignados."}), 400

        db.session.delete(cat)
        db.session.commit()
        return jsonify({"message": "Categoría borrada"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error de sistema al eliminar"}), 500