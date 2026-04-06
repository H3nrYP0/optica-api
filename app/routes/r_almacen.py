from flask import jsonify, request
from app.database import db
from app.Models.models import Marca, CategoriaProducto, Producto, Imagen, Multimedia
from app.routes import main_bp

# ===== MARCAS =====
@main_bp.route('/marcas', methods=['GET'])
def get_marcas():
    try:
        marcas = Marca.query.all()
        return jsonify([marca.to_dict() for marca in marcas])
    except Exception as e:
        return jsonify({"error": "Error al obtener marcas"}), 500

@main_bp.route('/marcas', methods=['POST'])
def create_marca():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400
        
        marca = Marca(
            nombre=data['nombre'],
            estado=data.get('estado', True)
        )
        db.session.add(marca)
        db.session.commit()
        return jsonify({"message": "Marca creada", "marca": marca.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear marca"}), 500

@main_bp.route('/marcas/<int:id>', methods=['PUT'])
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

@main_bp.route('/marcas/<int:id>', methods=['DELETE'])
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

# ===== CATEGORÍAS =====
@main_bp.route('/categorias', methods=['GET'])
def get_categorias():
    try:
        categorias = CategoriaProducto.query.all()
        return jsonify([categoria.to_dict() for categoria in categorias])
    except Exception as e:
        return jsonify({"error": "Error al obtener categorías"}), 500

@main_bp.route('/categorias', methods=['POST'])
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

@main_bp.route('/categorias/<int:id>', methods=['PUT'])
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

@main_bp.route('/categorias/<int:id>', methods=['DELETE'])
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

# ===== PRODUCTOS =====
@main_bp.route('/productos', methods=['GET'])
def get_productos():
    try:
        productos = Producto.query.all()
        return jsonify([producto.to_dict() for producto in productos])
    except Exception as e:
        return jsonify({"error": "Error al obtener productos"}), 500

@main_bp.route('/productos', methods=['POST'])
def create_producto():
    try:
        data = request.get_json()
        required_fields = ['nombre', 'precio_venta', 'precio_compra', 'categoria_id', 'marca_id']
        for field in required_fields:
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

@main_bp.route('/productos/<int:id>', methods=['PUT'])
def update_producto(id):
    try:
        producto = Producto.query.get(id)
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data:
            producto.nombre = data['nombre']
        if 'precio_venta' in data:
            producto.precio_venta = float(data['precio_venta'])
        if 'precio_compra' in data:
            producto.precio_compra = float(data['precio_compra'])
        if 'stock' in data:
            producto.stock = data['stock']
        if 'stock_minimo' in data:
            producto.stock_minimo = data['stock_minimo']
        if 'descripcion' in data:
            producto.descripcion = data['descripcion']
        if 'categoria_id' in data:
            producto.categoria_producto_id = data['categoria_id']
        if 'marca_id' in data:
            producto.marca_id = data['marca_id']
        if 'estado' in data:
            producto.estado = data['estado']
        db.session.commit()
        return jsonify({"message": "Producto actualizado", "producto": producto.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar producto"}), 500

@main_bp.route('/productos/<int:id>', methods=['DELETE'])
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

# ===== IMÁGENES =====
@main_bp.route('/imagenes', methods=['POST'])
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

@main_bp.route('/imagenes', methods=['GET'])
def get_imagenes():
    try:
        imagenes = Imagen.query.all()
        return jsonify([img.to_dict() for img in imagenes])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/imagenes/<int:id>', methods=['GET'])
def get_imagen(id):
    try:
        imagen = Imagen.query.get(id)
        if not imagen:
            return jsonify({"error": "Imagen no encontrada"}), 404
        return jsonify(imagen.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/imagenes/producto/<int:producto_id>', methods=['GET'])
def get_imagenes_por_producto(producto_id):
    try:
        producto = Producto.query.get(producto_id)
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404
        return jsonify({"producto_id": producto_id, "imagenes": [img.to_dict() for img in producto.imagenes]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/imagenes/<int:id>', methods=['PUT'])
def update_imagen(id):
    try:
        imagen = Imagen.query.get(id)
        if not imagen:
            return jsonify({"error": "Imagen no encontrada"}), 404
        data = request.get_json()
        if 'url' in data:
            imagen.url = data['url']
        if 'producto_id' in data:
            producto = Producto.query.get(data['producto_id'])
            if not producto:
                return jsonify({"error": "Producto no encontrado"}), 404
            imagen.producto_id = data['producto_id']
        db.session.commit()
        return jsonify({"message": "Imagen actualizada", "imagen": imagen.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main_bp.route('/imagenes/<int:id>', methods=['DELETE'])
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

# ===== MULTIMEDIA =====
@main_bp.route('/multimedia', methods=['POST'])
def crear_multimedia():
    try:
        data = request.get_json()
        if not data.get('url'):
            return jsonify({"error": "URL requerida"}), 400
        if not data.get('tipo'):
            return jsonify({"error": "Tipo requerido: 'categoria', 'comprobante' u 'otro'"}), 400
        tipo = data['tipo']
        if tipo not in ['categoria', 'comprobante', 'otro']:
            return jsonify({"error": "Tipo debe ser: 'categoria', 'comprobante' u 'otro'"}), 400
        if tipo == 'categoria' and not data.get('categoria_id'):
            return jsonify({"error": "Para tipo 'categoria' se requiere categoria_id"}), 400
        if tipo == 'comprobante' and not data.get('pedido_id'):
            return jsonify({"error": "Para tipo 'comprobante' se requiere pedido_id"}), 400
        if tipo == 'categoria':
            existente = Multimedia.query.filter_by(tipo='categoria', categoria_id=data['categoria_id']).first()
            if existente:
                existente.url = data['url']
                db.session.commit()
                return jsonify({"success": True, "message": "Imagen de categoría actualizada", "multimedia": existente.to_dict()})
        if tipo == 'comprobante':
            existente = Multimedia.query.filter_by(tipo='comprobante', pedido_id=data['pedido_id']).first()
            if existente:
                return jsonify({"error": "Este pedido ya tiene un comprobante"}), 400
        multimedia = Multimedia(url=data['url'], tipo=tipo, categoria_id=data.get('categoria_id'), pedido_id=data.get('pedido_id'))
        db.session.add(multimedia)
        db.session.commit()
        return jsonify({"success": True, "multimedia": multimedia.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main_bp.route('/multimedia/<string:tipo>', methods=['GET'])
def obtener_multimedia_tipo(tipo):
    try:
        if tipo not in ['categoria', 'comprobante', 'otro']:
            return jsonify({"error": "Tipo no válido"}), 400
        items = Multimedia.query.filter_by(tipo=tipo).all()
        return jsonify([item.to_dict() for item in items])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/multimedia/categoria/<int:categoria_id>', methods=['GET'])
def obtener_imagen_categoria(categoria_id):
    try:
        imagen = Multimedia.query.filter_by(tipo='categoria', categoria_id=categoria_id).first()
        if not imagen:
            return jsonify({"imagen": None})
        return jsonify(imagen.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/multimedia/comprobante/pedido/<int:pedido_id>', methods=['GET'])
def obtener_comprobante_pedido(pedido_id):
    try:
        comprobante = Multimedia.query.filter_by(tipo='comprobante', pedido_id=pedido_id).first()
        if not comprobante:
            return jsonify({"comprobante": None})
        return jsonify(comprobante.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/multimedia/<int:id>', methods=['PUT'])
def actualizar_multimedia(id):
    try:
        multimedia = Multimedia.query.get(id)
        if not multimedia:
            return jsonify({"error": "Elemento multimedia no encontrado"}), 404
        data = request.get_json()
        if 'url' in data:
            multimedia.url = data['url']
        if 'tipo' in data:
            tipo = data['tipo']
            if tipo not in ['categoria', 'comprobante', 'otro']:
                return jsonify({"error": "Tipo debe ser: 'categoria', 'comprobante' u 'otro'"}), 400
            multimedia.tipo = tipo
        if multimedia.tipo == 'categoria':
            if 'categoria_id' in data:
                multimedia.categoria_id = data['categoria_id']
            multimedia.pedido_id = None
        elif multimedia.tipo == 'comprobante':
            if 'pedido_id' in data:
                multimedia.pedido_id = data['pedido_id']
            multimedia.categoria_id = None
        else:
            multimedia.categoria_id = None
            multimedia.pedido_id = None
        db.session.commit()
        return jsonify({"success": True, "message": "Multimedia actualizado", "multimedia": multimedia.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main_bp.route('/multimedia/<int:id>', methods=['DELETE'])
def eliminar_multimedia(id):
    try:
        multimedia = Multimedia.query.get(id)
        if not multimedia:
            return jsonify({"error": "Elemento multimedia no encontrado"}), 404
        db.session.delete(multimedia)
        db.session.commit()
        return jsonify({"success": True, "message": "Multimedia eliminado"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main_bp.route('/multimedia', methods=['GET'])
def obtener_todo_multimedia():
    try:
        items = Multimedia.query.all()
        return jsonify([item.to_dict() for item in items])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/categorias-con-imagen', methods=['GET'])
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