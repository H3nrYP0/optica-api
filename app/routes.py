from flask import Blueprint, jsonify, request
from app.database import db
from app.models import Marca, CategoriaProducto, Producto, Imagen

main_bp = Blueprint('main', __name__)

# ===== RUTAS PÚBLICAS =====
@main_bp.route('/')
def home():
    return jsonify({
        "message": "API Óptica - Módulo Productos", 
        "version": "1.0",
        "endpoints": {
            "marcas": "GET /marcas",
            "categorias": "GET /categorias", 
            "productos": "GET /productos",
            "imagenes": "GET /productos/<id>/imagenes"
        }
    })

# ===== MARCAS =====
@main_bp.route('/marcas', methods=['GET'])
def get_marcas():
    try:
        marcas = Marca.query.filter_by(estado=True).all()
        return jsonify([marca.to_dict() for marca in marcas])
    except Exception as e:
        return jsonify({"error": "Error al obtener marcas"}), 500

@main_bp.route('/marcas', methods=['POST'])
def create_marca():
    try:
        data = request.get_json()
        
        # Validaciones
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400
        
        # Verificar si ya existe
        if Marca.query.filter_by(nombre=data['nombre']).first():
            return jsonify({"error": "Ya existe una marca con este nombre"}), 400

        marca = Marca(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', '')
        )
        
        db.session.add(marca)
        db.session.commit()
        
        return jsonify({
            "message": "Marca creada exitosamente",
            "marca": marca.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear marca"}), 500

# ===== CATEGORÍAS =====
@main_bp.route('/categorias', methods=['GET'])
def get_categorias():
    try:
        categorias = CategoriaProducto.query.filter_by(estado=True).all()
        return jsonify([categoria.to_dict() for categoria in categorias])
    except Exception as e:
        return jsonify({"error": "Error al obtener categorías"}), 500

@main_bp.route('/categorias', methods=['POST'])
def create_categoria():
    try:
        data = request.get_json()
        
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400
        
        if CategoriaProducto.query.filter_by(nombre=data['nombre']).first():
            return jsonify({"error": "Ya existe una categoría con este nombre"}), 400

        categoria = CategoriaProducto(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', '')
        )
        
        db.session.add(categoria)
        db.session.commit()
        
        return jsonify({
            "message": "Categoría creada exitosamente", 
            "categoria": categoria.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear categoría"}), 500

# ===== PRODUCTOS =====
@main_bp.route('/productos', methods=['GET'])
def get_productos():
    try:
        # Filtros opcionales
        categoria_id = request.args.get('categoria_id', type=int)
        marca_id = request.args.get('marca_id', type=int)
        solo_activos = request.args.get('solo_activos', 'true').lower() == 'true'
        
        query = Producto.query
        
        if categoria_id:
            query = query.filter_by(categoria_producto_id=categoria_id)
        if marca_id:
            query = query.filter_by(marca_id=marca_id)
        if solo_activos:
            query = query.filter_by(estado=True)
            
        productos = query.all()
        
        return jsonify([producto.to_dict() for producto in productos])
        
    except Exception as e:
        return jsonify({"error": "Error al obtener productos"}), 500

@main_bp.route('/productos/<int:producto_id>', methods=['GET'])
def get_producto(producto_id):
    try:
        producto = Producto.query.get_or_404(producto_id)
        return jsonify(producto.to_dict())
    except Exception as e:
        return jsonify({"error": "Producto no encontrado"}), 404

@main_bp.route('/productos', methods=['POST'])
def create_producto():
    try:
        data = request.get_json()
        
        # Validaciones básicas
        required_fields = ['nombre', 'precio_venta', 'precio_compra', 'categoria_producto_id', 'marca_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        
        # Verificar que categoría y marca existan
        if not CategoriaProducto.query.get(data['categoria_producto_id']):
            return jsonify({"error": "La categoría no existe"}), 400
            
        if not Marca.query.get(data['marca_id']):
            return jsonify({"error": "La marca no existe"}), 400

        producto = Producto(
            nombre=data['nombre'],
            precio_venta=float(data['precio_venta']),
            precio_compra=float(data['precio_compra']),
            stock=data.get('stock', 0),
            stock_minimo=data.get('stock_minimo', 5),
            descripcion=data.get('descripcion', ''),
            categoria_producto_id=data['categoria_producto_id'],
            marca_id=data['marca_id']
        )
        
        db.session.add(producto)
        db.session.commit()
        
        return jsonify({
            "message": "Producto creado exitosamente",
            "producto": producto.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear producto"}), 500

@main_bp.route('/productos/<int:producto_id>', methods=['PUT'])
def update_producto(producto_id):
    try:
        producto = Producto.query.get_or_404(producto_id)
        data = request.get_json()
        
        # Campos actualizables
        updateable_fields = ['nombre', 'precio_venta', 'precio_compra', 'stock', 
                           'stock_minimo', 'descripcion', 'estado', 'categoria_producto_id', 'marca_id']
        
        for field in updateable_fields:
            if field in data:
                setattr(producto, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            "message": "Producto actualizado exitosamente",
            "producto": producto.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar producto"}), 500

# ===== IMÁGENES =====
@main_bp.route('/productos/<int:producto_id>/imagenes', methods=['GET'])
def get_imagenes_producto(producto_id):
    try:
        producto = Producto.query.get_or_404(producto_id)
        return jsonify([imagen.to_dict() for imagen in producto.imagenes])
    except Exception as e:
        return jsonify({"error": "Error al obtener imágenes"}), 500

@main_bp.route('/productos/<int:producto_id>/imagenes', methods=['POST'])
def add_imagen_producto(producto_id):
    try:
        data = request.get_json()
        
        if not data.get('url'):
            return jsonify({"error": "La URL es requerida"}), 400
        
        # Verificar que el producto existe
        Producto.query.get_or_404(producto_id)
        
        imagen = Imagen(
            producto_id=producto_id,
            url=data['url'],
            es_principal=data.get('es_principal', False)
        )
        
        # Si esta imagen es principal, quitar principal de otras
        if imagen.es_principal:
            Imagen.query.filter_by(producto_id=producto_id).update({'es_principal': False})
        
        db.session.add(imagen)
        db.session.commit()
        
        return jsonify({
            "message": "Imagen agregada exitosamente",
            "imagen": imagen.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al agregar imagen"}), 500

# ===== ESTADÍSTICAS =====
@main_bp.route('/dashboard/productos', methods=['GET'])
def get_estadisticas_productos():
    try:
        total_productos = Producto.query.count()
        productos_activos = Producto.query.filter_by(estado=True).count()
        productos_bajo_stock = Producto.query.filter(Producto.stock <= Producto.stock_minimo).count()
        total_categorias = CategoriaProducto.query.filter_by(estado=True).count()
        total_marcas = Marca.query.filter_by(estado=True).count()
        
        return jsonify({
            "total_productos": total_productos,
            "productos_activos": productos_activos,
            "productos_bajo_stock": productos_bajo_stock,
            "total_categorias": total_categorias,
            "total_marcas": total_marcas
        })
        
    except Exception as e:
        return jsonify({"error": "Error al obtener estadísticas"}), 500