from flask import Blueprint, jsonify, request
from app.database import db
from app.models import Producto, Imagen

producto_bp = Blueprint('productos', __name__)

@producto_bp.route('', methods=['GET'])
def get_productos():
    try:
        return jsonify([p.to_dict() for p in Producto.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener productos"}), 500

@producto_bp.route('', methods=['POST'])
def create_producto():
    try:
        data = request.get_json()
        required = ['nombre', 'precio_venta', 'precio_compra', 'categoria_id', 'marca_id']
        for field in required:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        producto = Producto(
            nombre=data['nombre'],
            precio_venta=float(data['precio_venta']),
            precio_compra=float(data['precio_compra']),
            stock=data.get('stock', 0),
            stock_minimo=data.get('stock_minimo', 5),
            descripcion=data.get('descripcion', ''),
            categoria_producto_id=data['categoria_id'],
            marca_id=data['marca_id'],
            estado=data.get('estado', True)
        )
        db.session.add(producto)
        db.session.commit()
        return jsonify({"message": "Producto creado", "producto": producto.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear producto"}), 500

@producto_bp.route('/<int:id>', methods=['PUT'])
def update_producto(id):
    try:
        producto = Producto.query.get(id)
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data: producto.nombre = data['nombre']
        if 'precio_venta' in data: producto.precio_venta = float(data['precio_venta'])
        if 'precio_compra' in data: producto.precio_compra = float(data['precio_compra'])
        if 'stock' in data: producto.stock = data['stock']
        if 'stock_minimo' in data: producto.stock_minimo = data['stock_minimo']
        if 'descripcion' in data: producto.descripcion = data['descripcion']
        if 'categoria_id' in data: producto.categoria_producto_id = data['categoria_id']
        if 'marca_id' in data: producto.marca_id = data['marca_id']
        if 'estado' in data: producto.estado = data['estado']
        db.session.commit()
        return jsonify({"message": "Producto actualizado", "producto": producto.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar producto"}), 500

@producto_bp.route('/<int:id>', methods=['DELETE'])
def delete_producto(id):
    try:
        producto = Producto.query.get(id)
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404
        db.session.delete(producto)
        db.session.commit()
        return jsonify({"message": "Producto eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar producto"}), 500

@producto_bp.route('/imagenes', methods=['POST'])
def crear_imagen():
    try:
        data = request.get_json()
        if not data or not data.get('url') or not data.get('producto_id'):
            return jsonify({"error": "url y producto_id requeridos"}), 400
        producto = Producto.query.get(data['producto_id'])
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404
        imagen = Imagen(url=data['url'], producto_id=data['producto_id'])
        db.session.add(imagen)
        db.session.commit()
        return jsonify({"message": "Imagen creada", "imagen": imagen.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@producto_bp.route('/imagenes/<int:id>', methods=['DELETE'])
def delete_imagen(id):
    try:
        imagen = Imagen.query.get(id)
        if not imagen:
            return jsonify({"error": "Imagen no encontrada"}), 404
        db.session.delete(imagen)
        db.session.commit()
        return jsonify({"message": "Imagen eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
        