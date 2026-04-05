from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Producto, Marca, CategoriaProducto

producto_bp = Blueprint('productos', __name__)

@producto_bp.route('', methods=['POST'])
def create_producto():
    try:
        data = request.get_json()
        
        # 1. Validación de Negocio: Precios Lógicos
        p_venta = float(data.get('precio_venta', 0))
        p_compra = float(data.get('precio_compra', 0))
        
        if p_venta < p_compra:
            return jsonify({"error": "Alerta: El precio de venta no puede ser menor al de compra (Pérdida)"}), 400
        
        # 2. Validación de Integridad: ¿Existen y están activos los padres?
        marca = db.session.get(Marca, data.get('marca_id'))
        cat = db.session.get(CategoriaProducto, data.get('categoria_id'))
        
        if not marca or not cat:
            return jsonify({"error": "La Marca o Categoría seleccionada no existen"}), 400
            
        if not marca.estado or not cat.estado:
            return jsonify({"error": "No puede crear productos en Marcas o Categorías inactivas"}), 400

        # 3. Validación de Stock
        stock = int(data.get('stock', 0))
        if stock < 0:
            return jsonify({"error": "El stock inicial no puede ser negativo"}), 400

        nuevo = Producto(
            nombre=data['nombre'].strip(),
            precio_venta=p_venta,
            precio_compra=p_compra,
            stock=stock,
            stock_minimo=data.get('stock_minimo', 5),
            categoria_producto_id=data['categoria_id'],
            marca_id=data['marca_id'],
            estado=data.get('estado', True),
            descripcion=data.get('descripcion', '')
        )
        db.session.add(nuevo)
        db.session.commit()
        return jsonify(nuevo.to_dict()), 201
    except ValueError:
        return jsonify({"error": "Los precios y stock deben ser números válidos"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@producto_bp.route('/<int:id>', methods=['PUT'])
def update_producto(id):
    try:
        prod = db.session.get(Producto, id)
        if not prod: return jsonify({"error": "Producto no encontrado"}), 404
        
        data = request.get_json()
        
        # Validación de márgenes al editar
        if 'precio_venta' in data or 'precio_compra' in data:
            nuevo_pv = float(data.get('precio_venta', prod.precio_venta))
            nuevo_pc = float(data.get('precio_compra', prod.precio_compra))
            if nuevo_pv < nuevo_pc:
                return jsonify({"error": "El precio de venta es menor al de compra"}), 400
            prod.precio_venta = nuevo_pv
            prod.precio_compra = nuevo_pc

        # Si se intenta activar un producto, validar que su marca esté activa
        if data.get('estado') is True:
            marca = db.session.get(Marca, prod.marca_id)
            if not marca.estado:
                return jsonify({"error": "No puede activar un producto de una marca inactiva"}), 400

        # Actualizar otros campos
        for key in ['nombre', 'stock', 'stock_minimo', 'descripcion', 'estado']:
            if key in data:
                setattr(prod, key, data[key])
        
        db.session.commit()
        return jsonify(prod.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500