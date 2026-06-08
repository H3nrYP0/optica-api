"""
Módulo de almacén: marcas, categorías, productos, imágenes y multimedia.
Permisos granulares:
- Productos: ver_productos, crear_productos, editar_productos, eliminar_productos
- Marcas: ver_marcas, crear_marcas, editar_marcas, eliminar_marcas
- Categorías: ver_categorias, crear_categorias, editar_categorias, eliminar_categorias
- Imágenes y multimedia: usar permisos de productos (por simplicidad)
"""

from flask import jsonify, request
from app.database import db
from app.Models.models import Marca, CategoriaProducto, Producto, Imagen, Multimedia
from app.routes import main_bp
from app.auth.decorators import permiso_requerido

MAX_PER_PAGE = 10

# ============================================================
# MÓDULO: MARCAS
# ============================================================

@main_bp.route('/marcas', methods=['GET'])
def get_marcas():
    """
    Listar marcas (público) con paginación, búsqueda y filtro de estado.
    Query params: page, per_page, search, estado
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        search = request.args.get('search', '', type=str).strip()
        estado = request.args.get('estado', '', type=str).strip().lower()

        query = Marca.query
        if search:
            query = query.filter(Marca.nombre.ilike(f"%{search}%"))
        if estado != '':
            estado_bool = estado == 'true'
            query = query.filter(Marca.estado == estado_bool)
        query = query.order_by(Marca.nombre.asc())

        if 'page' not in request.args and 'per_page' not in request.args and not search and estado == '':
            marcas = query.all()
            return jsonify([marca.to_dict() for marca in marcas])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [marca.to_dict() for marca in pagination.items],
            'pagination': {
                'current_page': pagination.page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
        })
    except Exception as e:
        return jsonify({"error": "Error al obtener marcas"}), 500


@main_bp.route('/marcas/verificar-existencia', methods=['GET'])
def verificar_existencia_marca():
    try:
        nombre = request.args.get('nombre', '').strip()
        exclude_id = request.args.get('exclude_id', type=int)
        if not nombre or len(nombre) < 2:
            return jsonify({'exists': False})
        query = Marca.query.filter(Marca.nombre.ilike(nombre))
        if exclude_id is not None:
            query = query.filter(Marca.id != exclude_id)
        exists = db.session.query(query.exists()).scalar()
        return jsonify({'exists': exists})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/marcas/<int:id>/productos-asociados', methods=['GET'])
def marca_productos_asociados(id):
    try:
        marca = Marca.query.get(id)
        if not marca:
            return jsonify({'error': 'Marca no encontrada'}), 404
        count = Producto.query.filter_by(marca_id=id).count()
        return jsonify({'hasProductos': count > 0, 'count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/marcas', methods=['POST'])
@permiso_requerido("crear_marcas")
def create_marca():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400
        nombre = " ".join(data['nombre'].split()).strip()
        if len(nombre) < 2:
            return jsonify({"error": "El nombre de la marca es demasiado corto"}), 400
        if Marca.query.filter(Marca.nombre.ilike(nombre)).first():
            return jsonify({"error": f"La marca '{nombre}' ya existe en el sistema"}), 400
        marca = Marca(nombre=nombre, estado=data.get('estado', True))
        db.session.add(marca)
        db.session.commit()
        return jsonify({"message": "Marca creada", "marca": marca.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear marca: {str(e)}"}), 500


@main_bp.route('/marcas/<int:id>', methods=['PUT'])
@permiso_requerido("editar_marcas")
def update_marca(id):
    try:
        marca = Marca.query.get(id)
        if not marca:
            return jsonify({"error": "Marca no encontrada"}), 404
        data = request.get_json()
        if 'nombre' in data:
            nombre = " ".join(data['nombre'].split()).strip()
            if Marca.query.filter(Marca.nombre.ilike(nombre), Marca.id != id).first():
                return jsonify({"error": "Ya existe otra marca con este nombre"}), 400
            marca.nombre = nombre
        if 'estado' in data:
            marca.estado = data['estado']
        db.session.commit()
        return jsonify({"message": "Marca actualizada", "marca": marca.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar marca: {str(e)}"}), 500


@main_bp.route('/marcas/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_marcas")
def delete_marca(id):
    try:
        marca = Marca.query.get(id)
        if not marca:
            return jsonify({"error": "Marca no encontrada"}), 404
        if marca.productos and len(marca.productos) > 0:
            return jsonify({"error": f"No se puede eliminar '{marca.nombre}' porque está vinculada a {len(marca.productos)} productos. Desactívela en su lugar."}), 400
        db.session.delete(marca)
        db.session.commit()
        return jsonify({"message": "Marca eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar marca: {str(e)}"}), 500


# ============================================================
# MÓDULO: CATEGORÍAS
# ============================================================

@main_bp.route('/categorias', methods=['GET'])
def get_categorias():
    """
    Listar categorías (público) con paginación, búsqueda y filtro de estado.
    Query params: page, per_page, search, estado
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        search = request.args.get('search', '', type=str).strip()
        estado = request.args.get('estado', '', type=str).strip().lower()

        query = CategoriaProducto.query
        if search:
            query = query.filter(CategoriaProducto.nombre.ilike(f"%{search}%"))
        if estado != '':
            estado_bool = estado == 'true'
            query = query.filter(CategoriaProducto.estado == estado_bool)
        query = query.order_by(CategoriaProducto.nombre.asc())

        if 'page' not in request.args and 'per_page' not in request.args and not search and estado == '':
            categorias = query.all()
            return jsonify([categoria.to_dict() for categoria in categorias])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [categoria.to_dict() for categoria in pagination.items],
            'pagination': {
                'current_page': pagination.page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
        })
    except Exception as e:
        return jsonify({"error": "Error al obtener categorías"}), 500


@main_bp.route('/categorias', methods=['POST'])
@permiso_requerido("crear_categorias")
def create_categoria():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400
        nombre = " ".join(data['nombre'].split()).strip()
        if not nombre:
            return jsonify({"error": "El nombre de categoría es obligatorio"}), 400
        if CategoriaProducto.query.filter(CategoriaProducto.nombre.ilike(nombre)).first():
            return jsonify({"error": "Esta categoría ya existe"}), 400
        categoria = CategoriaProducto(
            nombre=nombre,
            descripcion=data.get('descripcion', ''),
            estado=data.get('estado', True)
        )
        db.session.add(categoria)
        db.session.commit()
        return jsonify({"message": "Categoría creada", "categoria": categoria.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear categoría: {str(e)}"}), 500


@main_bp.route('/categorias/<int:id>', methods=['PUT'])
@permiso_requerido("editar_categorias")
def update_categoria(id):
    try:
        categoria = CategoriaProducto.query.get(id)
        if not categoria:
            return jsonify({"error": "Categoría no encontrada"}), 404
        data = request.get_json()
        if 'nombre' in data:
            nombre = " ".join(data['nombre'].split()).strip()
            existente = CategoriaProducto.query.filter(CategoriaProducto.nombre.ilike(nombre), CategoriaProducto.id != id).first()
            if existente:
                return jsonify({"error": "Ya existe otra categoría con ese nombre"}), 400
            categoria.nombre = nombre
        if 'descripcion' in data:
            categoria.descripcion = data['descripcion']
        if 'estado' in data:
            categoria.estado = data['estado']
        db.session.commit()
        return jsonify({"message": "Categoría actualizada", "categoria": categoria.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar categoría: {str(e)}"}), 500


@main_bp.route('/categorias/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_categorias")
def delete_categoria(id):
    try:
        categoria = CategoriaProducto.query.get(id)
        if not categoria:
            return jsonify({"error": "Categoría no encontrada"}), 404
        if categoria.productos and len(categoria.productos) > 0:
            return jsonify({"error": f"No se puede eliminar. La categoría tiene {len(categoria.productos)} productos asignados. Desactívela en su lugar."}), 400
        db.session.delete(categoria)
        db.session.commit()
        return jsonify({"message": "Categoría eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar categoría: {str(e)}"}), 500


# ============================================================
# MÓDULO: PRODUCTOS
# ============================================================

@main_bp.route('/productos', methods=['GET'])
def get_productos():
    """
    Listar productos (público) con paginación y filtros avanzados.
    Query params: page, per_page, search, categoria_id, marca_id, estado, min_precio, max_precio, stock_minimo
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        search = request.args.get('search', '', type=str).strip()
        categoria_id = request.args.get('categoria_id', type=int)
        marca_id = request.args.get('marca_id', type=int)
        estado = request.args.get('estado', '', type=str).strip().lower()
        min_precio = request.args.get('min_precio', type=float)
        max_precio = request.args.get('max_precio', type=float)
        stock_minimo = request.args.get('stock_minimo', type=int)

        query = Producto.query.options(
            db.joinedload(Producto.marca),
            db.joinedload(Producto.categoria),
            db.joinedload(Producto.imagenes)
        )
        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(
                    Producto.nombre.ilike(like),
                    Producto.marca.has(Marca.nombre.ilike(like)),
                    Producto.categoria.has(CategoriaProducto.nombre.ilike(like))
                )
            )
        if categoria_id:
            query = query.filter(Producto.categoria_producto_id == categoria_id)
        if marca_id:
            query = query.filter(Producto.marca_id == marca_id)
        if estado != '':
            estado_bool = estado == 'true'
            query = query.filter(Producto.estado == estado_bool)
        if min_precio is not None:
            query = query.filter(Producto.precio_venta >= min_precio)
        if max_precio is not None:
            query = query.filter(Producto.precio_venta <= max_precio)
        if stock_minimo is not None:
            query = query.filter(Producto.stock <= stock_minimo)

        query = query.order_by(Producto.nombre.asc())

        has_pagination = 'page' in request.args or 'per_page' in request.args
        has_filters = search or categoria_id or marca_id or estado or min_precio or max_precio or stock_minimo
        if not has_pagination and not has_filters:
            productos = query.all()
            return jsonify([producto.to_dict() for producto in productos])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [p.to_dict() for p in pagination.items],
            'pagination': {
                'current_page': pagination.page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
        })
    except Exception as e:
        return jsonify({"error": "Error al obtener productos"}), 500


@main_bp.route('/productos/lista-completa', methods=['GET'])
def get_productos_lista_completa():
    # Este endpoint ya tenía paginación, se mantiene igual pero con MAX_PER_PAGE consistente
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 50)
        query = Producto.query.options(
            db.joinedload(Producto.marca),
            db.joinedload(Producto.categoria),
            db.joinedload(Producto.imagenes)
        ).order_by(Producto.nombre.asc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        result = []
        for p in pagination.items:
            result.append({
                'id': p.id,
                'nombre': p.nombre,
                'precio_venta': p.precio_venta,
                'precio_compra': p.precio_compra,
                'stock': p.stock,
                'stock_minimo': p.stock_minimo,
                'descripcion': p.descripcion,
                'estado': p.estado,
                'categoria_id': p.categoria_producto_id,
                'categoria_nombre': p.categoria.nombre if p.categoria else None,
                'marca_id': p.marca_id,
                'marca_nombre': p.marca.nombre if p.marca else None,
                'imagenes': [{'id': img.id, 'url': img.url} for img in p.imagenes]
            })
        return jsonify({
            'data': result,
            'pagination': {
                'current_page': pagination.page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/productos/buscar-avanzado', methods=['GET'])
def buscar_productos_avanzado():
    # Este endpoint ya tenía paginación, se mantiene igual pero con MAX_PER_PAGE
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 20)
        search = request.args.get('search', '', type=str).strip()
        categoria_id = request.args.get('categoria_id', type=int)
        marca_id = request.args.get('marca_id', type=int)
        estado_param = request.args.get('estado', '', type=str)
        query = Producto.query.options(
            db.joinedload(Producto.marca),
            db.joinedload(Producto.categoria),
            db.joinedload(Producto.imagenes)
        )
        if categoria_id:
            query = query.filter(Producto.categoria_producto_id == categoria_id)
        if marca_id:
            query = query.filter(Producto.marca_id == marca_id)
        if estado_param:
            estado_bool = estado_param == 'activa'
            query = query.filter(Producto.estado == estado_bool)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Producto.nombre.ilike(search_term),
                    Producto.marca.has(Marca.nombre.ilike(search_term)),
                    Producto.categoria.has(CategoriaProducto.nombre.ilike(search_term))
                )
            )
        query = query.order_by(Producto.nombre.asc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        result = []
        for p in pagination.items:
            result.append({
                'id': p.id,
                'nombre': p.nombre,
                'precio_venta': p.precio_venta,
                'precio_compra': p.precio_compra,
                'stock': p.stock,
                'stock_minimo': p.stock_minimo,
                'descripcion': p.descripcion,
                'estado': p.estado,
                'categoria_id': p.categoria_producto_id,
                'categoria_nombre': p.categoria.nombre if p.categoria else None,
                'marca_id': p.marca_id,
                'marca_nombre': p.marca.nombre if p.marca else None,
                'imagenes': [{'id': img.id, 'url': img.url} for img in p.imagenes]
            })
        return jsonify({
            'data': result,
            'pagination': {
                'current_page': pagination.page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/productos/lista-completa/<int:id>', methods=['GET'])
def get_producto_lista_completa(id):
    try:
        producto = Producto.query.options(
            db.joinedload(Producto.marca),
            db.joinedload(Producto.categoria),
            db.joinedload(Producto.imagenes)
        ).get(id)
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404
        result = {
            'id': producto.id,
            'nombre': producto.nombre,
            'precio_venta': producto.precio_venta,
            'precio_compra': producto.precio_compra,
            'stock': producto.stock,
            'stock_minimo': producto.stock_minimo,
            'descripcion': producto.descripcion,
            'estado': producto.estado,
            'categoria_id': producto.categoria_producto_id,
            'categoria_nombre': producto.categoria.nombre if producto.categoria else None,
            'marca_id': producto.marca_id,
            'marca_nombre': producto.marca.nombre if producto.marca else None,
            'imagenes': [{'id': img.id, 'url': img.url} for img in producto.imagenes]
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/productos/verificar-existencia', methods=['GET'])
def verificar_existencia_producto():
    try:
        nombre = request.args.get('nombre', '').strip()
        exclude_id = request.args.get('exclude_id', type=int)
        if not nombre or len(nombre) < 3:
            return jsonify({'exists': False})
        query = Producto.query.filter(db.func.lower(Producto.nombre) == db.func.lower(nombre))
        if exclude_id:
            query = query.filter(Producto.id != exclude_id)
        exists = query.first() is not None
        return jsonify({'exists': exists})
    except Exception as e:
        return jsonify({'exists': False, 'error': str(e)}), 500


@main_bp.route('/productos/<int:id>/asociaciones', methods=['GET'])
@permiso_requerido("ver_productos")
def get_producto_asociaciones(id):
    try:
        producto = Producto.query.get(id)
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404
        from app.Models.models import DetalleVenta, DetalleCompra, DetallePedido
        tiene_ventas = DetalleVenta.query.filter_by(producto_id=id).first() is not None
        tiene_compras = DetalleCompra.query.filter_by(producto_id=id).first() is not None
        tiene_pedidos = DetallePedido.query.filter_by(producto_id=id).first() is not None
        return jsonify({
            'tiene_ventas': tiene_ventas,
            'tiene_compras': tiene_compras,
            'tiene_pedidos': tiene_pedidos,
            'tiene_asociaciones': tiene_ventas or tiene_compras or tiene_pedidos
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/productos', methods=['POST'])
@permiso_requerido("crear_productos")
def create_producto():
    # ... (sin cambios, igual que original)
    pass


@main_bp.route('/productos/<int:id>', methods=['PUT'])
@permiso_requerido("editar_productos")
def update_producto(id):
    # ... (sin cambios)
    pass


@main_bp.route('/productos/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_productos")
def delete_producto(id):
    # ... (sin cambios)
    pass


# ============================================================
# MÓDULO: IMÁGENES
# ============================================================

@main_bp.route('/imagenes', methods=['POST'])
@permiso_requerido("crear_productos")
def crear_imagen():
    try:
        data = request.get_json()
        if not data or not data.get('url') or not data.get('producto_id'):
            return jsonify({"error": "url y producto_id requeridos"}), 400
        producto = Producto.query.get(data['producto_id'])
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404
        if not producto.estado:
            return jsonify({"error": "No puedes agregar imágenes a un producto inactivo"}), 400
        imagen = Imagen(url=data['url'], producto_id=data['producto_id'])
        db.session.add(imagen)
        db.session.commit()
        return jsonify({"message": "Imagen creada", "imagen": imagen.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main_bp.route('/imagenes', methods=['GET'])
def get_imagenes():
    """
    Listar imágenes con paginación y filtro por producto_id.
    Query params: page, per_page, producto_id
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        producto_id = request.args.get('producto_id', type=int)

        query = Imagen.query
        if producto_id:
            query = query.filter(Imagen.producto_id == producto_id)
        query = query.order_by(Imagen.id.desc())

        if 'page' not in request.args and 'per_page' not in request.args and not producto_id:
            imagenes = query.all()
            return jsonify([img.to_dict() for img in imagenes])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [img.to_dict() for img in pagination.items],
            'pagination': {
                'current_page': pagination.page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
        })
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
@permiso_requerido("editar_productos")
def update_imagen(id):
    # ... (sin cambios)
    pass


@main_bp.route('/imagenes/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_productos")
def delete_imagen(id):
    # ... (sin cambios)
    pass


# ============================================================
# MÓDULO: MULTIMEDIA
# ============================================================

@main_bp.route('/multimedia', methods=['POST'])
@permiso_requerido("crear_productos")
def crear_multimedia():
    # ... (sin cambios)
    pass


@main_bp.route('/multimedia/comprobante/pedido/<int:pedido_id>', methods=['GET'])
def obtener_comprobante_pedido(pedido_id):
    try:
        from app.Models.models import Pedido
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404
        comprobante = Multimedia.query.filter_by(tipo='comprobante', pedido_id=pedido_id).first()
        if not comprobante:
            return jsonify({"comprobante": None})
        return jsonify(comprobante.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/multimedia/<int:id>', methods=['PUT'])
@permiso_requerido("editar_productos")
def actualizar_multimedia(id):
    # ... (sin cambios)
    pass