from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Marca

marca_bp = Blueprint('marcas', __name__)

@marca_bp.route('', methods=['POST'])
def create_marca():
    try:
        data = request.get_json()
        nombre = " ".join(data.get('nombre', '').split()).strip() # Limpia espacios internos múltiples
        
        if len(nombre) < 2:
            return jsonify({"error": "El nombre de la marca es demasiado corto"}), 400

        # Unicidad estricta
        if Marca.query.filter(Marca.nombre.ilike(nombre)).first():
            return jsonify({"error": f"La marca '{nombre}' ya existe en el sistema"}), 400

        nueva_marca = Marca(nombre=nombre, estado=data.get('estado', True))
        db.session.add(nueva_marca)
        db.session.commit()
        return jsonify(nueva_marca.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@marca_bp.route('/<int:id>', methods=['PUT'])
def update_marca(id):
    try:
        marca = db.session.get(Marca, id)
        if not marca:
            return jsonify({"error": "Marca no encontrada"}), 404
        
        data = request.get_json()
        if 'nombre' in data:
            nombre = " ".join(data['nombre'].split()).strip()
            if Marca.query.filter(Marca.nombre.ilike(nombre), Marca.id != id).first():
                return jsonify({"error": "Ya existe otra marca con este nombre"}), 400
            marca.nombre = nombre
            
        if 'estado' in data:
            nuevo_estado = bool(data['estado'])
            # REGLA: Si desactivas la marca, podrías querer advertir, 
            # pero aquí permitimos desactivar (los productos heredarán el estado visualmente)
            marca.estado = nuevo_estado
            
        db.session.commit()
        return jsonify(marca.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@marca_bp.route('/<int:id>', methods=['DELETE'])
def delete_marca(id):
    try:
        marca = db.session.get(Marca, id)
        if not marca: return jsonify({"error": "Marca no encontrada"}), 404

        # REGLA DE ORO: No se borra si se usó alguna vez
        if len(marca.productos) > 0:
            return jsonify({
                "error": f"No se puede eliminar '{marca.nombre}' porque está vinculada a {len(marca.productos)} productos. Desactívela para que no aparezca en ventas."
            }), 400

        db.session.delete(marca)
        db.session.commit()
        return jsonify({"message": "Marca eliminada físicamente"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error de integridad"}), 500