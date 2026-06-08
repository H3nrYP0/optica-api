"""
Módulo de compras y gestión de inventario.
Permisos granulares:
- Compras: ver_compras, crear_compras, editar_compras, eliminar_compras
- Detalles de compra: usar mismos permisos de compras
- Nota: La entidad 'compras' debe ser añadida al seed de permisos.
"""

from flask import jsonify, request
from app.database import db
from app.Models.models import Compra, DetalleCompra, Producto, Proveedor
from datetime import datetime
from app.routes import main_bp
from app.auth.decorators import permiso_requerido

MAX_PER_PAGE = 10

# ============================================================
# MÓDULO: COMPRAS
# ============================================================

@main_bp.route('/compras', methods=['GET'])
@permiso_requerido("ver_compras")
def get_compras():
    """
    Listar compras con paginación, búsqueda y filtros.
    Query params:
        page          (int)
        per_page      (int) máx 10
        search        (str) busca en proveedor (razón social)
        proveedor_id  (int)
        fecha_desde   (str) YYYY-MM-DD
        fecha_hasta   (str)
        estado_compra (bool) True/False
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        search = request.args.get('search', '', type=str).strip()
        proveedor_id = request.args.get('proveedor_id', type=int)
        fecha_desde = request.args.get('fecha_desde', '', type=str).strip()
        fecha_hasta = request.args.get('fecha_hasta', '', type=str).strip()
        estado_compra_param = request.args.get('estado_compra', '', type=str).strip().lower()

        query = Compra.query.join(Proveedor, Compra.proveedor_id == Proveedor.id)

        if proveedor_id:
            query = query.filter(Compra.proveedor_id == proveedor_id)
        if fecha_desde:
            try:
                fd = datetime.strptime(fecha_desde, '%Y-%m-%d')
                query = query.filter(Compra.fecha >= fd)
            except ValueError:
                return jsonify({"error": "Formato fecha_desde inválido"}), 400
        if fecha_hasta:
            try:
                fh = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                query = query.filter(Compra.fecha <= fh)
            except ValueError:
                return jsonify({"error": "Formato fecha_hasta inválido"}), 400
        if estado_compra_param != '':
            estado_bool = estado_compra_param == 'true'
            query = query.filter(Compra.estado_compra == estado_bool)
        if search:
            like = f"%{search}%"
            query = query.filter(Proveedor.razon_social_o_nombre.ilike(like))

        query = query.order_by(Compra.fecha.desc())

        has_pagination = 'page' in request.args or 'per_page' in request.args
        has_filters = proveedor_id or fecha_desde or fecha_hasta or estado_compra_param != '' or search
        if not has_pagination and not has_filters:
            compras = query.all()
            return jsonify([compra.to_dict() for compra in compras])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [compra.to_dict() for compra in pagination.items],
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
        return jsonify({"error": f"Error al obtener compras: {str(e)}"}), 500


@main_bp.route('/compras', methods=['POST'])
@permiso_requerido("crear_compras")
def create_compra():
    try:
        data = request.get_json()
        proveedor_id = data.get('proveedor_id')
        detalles_data = data.get('detalles', [])
        if not proveedor_id:
            return jsonify({"error": "El campo 'proveedor_id' es requerido"}), 400
        if not detalles_data:
            return jsonify({"error": "La compra debe tener al menos un detalle (producto)"}), 400
        proveedor = Proveedor.query.get(proveedor_id)
        if not proveedor:
            return jsonify({"error": "El proveedor especificado no existe"}), 404
        if not proveedor.estado:
            return jsonify({"error": "No se puede crear una compra con un proveedor inactivo"}), 400
        nueva_compra = Compra(
            proveedor_id=proveedor_id,
            total=0,
            estado_compra=data.get('estado_compra', True),
            fecha=datetime.utcnow()
        )
        db.session.add(nueva_compra)
        db.session.flush()
        total_calculado = 0
        productos_actualizados = []
        for idx, item in enumerate(detalles_data):
            prod_id = item.get('producto_id')
            cantidad = item.get('cantidad', 0)
            precio_u = item.get('precio_unidad', 0)
            if not prod_id:
                db.session.rollback()
                return jsonify({"error": f"El detalle {idx+1} no tiene 'producto_id'"}), 400
            try:
                cantidad = int(cantidad)
                precio_u = float(precio_u)
            except (ValueError, TypeError):
                db.session.rollback()
                return jsonify({"error": f"El detalle {idx+1}: cantidad y precio deben ser números válidos"}), 400
            if cantidad <= 0 or precio_u <= 0:
                db.session.rollback()
                return jsonify({"error": f"El detalle {idx+1}: cantidad y precio deben ser mayores a 0"}), 400
            producto = Producto.query.get(prod_id)
            if not producto:
                db.session.rollback()
                return jsonify({"error": f"El producto con ID {prod_id} no existe"}), 404
            if not producto.estado:
                db.session.rollback()
                return jsonify({"error": f"No se puede comprar el producto '{producto.nombre}' porque está inactivo"}), 400
            subtotal = cantidad * precio_u
            total_calculado += subtotal
            detalle = DetalleCompra(
                compra_id=nueva_compra.id,
                producto_id=prod_id,
                precio_unidad=precio_u,
                cantidad=cantidad,
                subtotal=subtotal
            )
            db.session.add(detalle)
            producto.stock += cantidad
            producto.precio_compra = precio_u
            productos_actualizados.append(producto)
        nueva_compra.total = total_calculado
        db.session.commit()
        return jsonify({"message": "Compra creada exitosamente", "compra": nueva_compra.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear compra: {str(e)}"}), 500


@main_bp.route('/compras/<int:id>', methods=['PUT'])
@permiso_requerido("editar_compras")
def update_compra(id):
    try:
        compra = Compra.query.get(id)
        if not compra:
            return jsonify({"error": "Compra no encontrada"}), 404
        data = request.get_json()
        if 'proveedor_id' in data:
            proveedor = Proveedor.query.get(data['proveedor_id'])
            if not proveedor:
                return jsonify({"error": "El proveedor especificado no existe"}), 404
            if not proveedor.estado:
                return jsonify({"error": "No se puede asignar un proveedor inactivo"}), 400
            compra.proveedor_id = data['proveedor_id']
        if 'total' in data:
            nuevo_total = float(data['total'])
            if nuevo_total < 0:
                return jsonify({"error": "El total no puede ser negativo"}), 400
            compra.total = nuevo_total
        if 'estado_compra' in data:
            compra.estado_compra = data['estado_compra']
        db.session.commit()
        return jsonify({"message": "Compra actualizada", "compra": compra.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar compra: {str(e)}"}), 500


@main_bp.route('/compras/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_compras")
def delete_compra(id):
    try:
        compra = Compra.query.get(id)
        if not compra:
            return jsonify({"error": "Compra no encontrada"}), 404
        for detalle in compra.detalles:
            producto = Producto.query.get(detalle.producto_id)
            if producto:
                if producto.stock < detalle.cantidad:
                    return jsonify({
                        "error": f"No se puede eliminar la compra: El producto '{producto.nombre}' ya se vendió y no hay suficiente stock para revertir."
                    }), 400
                producto.stock -= detalle.cantidad
        db.session.delete(compra)
        db.session.commit()
        return jsonify({"message": "Compra eliminada y stock revertido correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar compra: {str(e)}"}), 500


@main_bp.route('/compras/<int:compra_id>/detalles', methods=['GET'])
@permiso_requerido("ver_compras")
def get_detalles_compra_especifica(compra_id):
    try:
        compra = Compra.query.get(compra_id)
        if not compra:
            return jsonify({"error": "Compra no encontrada"}), 404
        detalles = DetalleCompra.query.filter_by(compra_id=compra_id).all()
        return jsonify([detalle.to_dict() for detalle in detalles])
    except Exception as e:
        return jsonify({"error": f"Error al obtener detalles de la compra: {str(e)}"}), 500


# ============================================================
# MÓDULO: DETALLES DE COMPRA
# ============================================================

@main_bp.route('/detalle-compra', methods=['GET'])
@permiso_requerido("ver_compras")
def get_detalles_compra():
    """
    Listar detalles de compra con paginación y filtros.
    Query params: page, per_page, compra_id, producto_id
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        compra_id = request.args.get('compra_id', type=int)
        producto_id = request.args.get('producto_id', type=int)

        query = DetalleCompra.query
        if compra_id:
            query = query.filter(DetalleCompra.compra_id == compra_id)
        if producto_id:
            query = query.filter(DetalleCompra.producto_id == producto_id)
        query = query.order_by(DetalleCompra.id.desc())

        if 'page' not in request.args and 'per_page' not in request.args and not compra_id and not producto_id:
            detalles = query.all()
            return jsonify([detalle.to_dict() for detalle in detalles])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [detalle.to_dict() for detalle in pagination.items],
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
        return jsonify({"error": "Error al obtener detalles de compra"}), 500


@main_bp.route('/detalle-compra', methods=['POST'])
@permiso_requerido("crear_compras")
def create_detalle_compra():
    try:
        data = request.get_json()
        required_fields = ['compra_id', 'producto_id', 'cantidad', 'precio_unidad']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        compra = Compra.query.get(data['compra_id'])
        if not compra:
            return jsonify({"error": "La compra especificada no existe"}), 404
        producto = Producto.query.get(data['producto_id'])
        if not producto:
            return jsonify({"error": "El producto especificado no existe"}), 404
        if not producto.estado:
            return jsonify({"error": "No se puede agregar un producto inactivo a la compra"}), 400
        try:
            cantidad = int(data['cantidad'])
            precio_unidad = float(data['precio_unidad'])
        except (ValueError, TypeError):
            return jsonify({"error": "Cantidad y precio deben ser números válidos"}), 400
        if cantidad <= 0 or precio_unidad <= 0:
            return jsonify({"error": "Cantidad y precio deben ser mayores a 0"}), 400
        subtotal = cantidad * precio_unidad
        detalle = DetalleCompra(
            compra_id=data['compra_id'],
            producto_id=data['producto_id'],
            cantidad=cantidad,
            precio_unidad=precio_unidad,
            subtotal=subtotal
        )
        db.session.add(detalle)
        compra.total += subtotal
        producto.stock += cantidad
        db.session.commit()
        return jsonify({"message": "Detalle de compra creado", "detalle": detalle.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear detalle de compra: {str(e)}"}), 500


@main_bp.route('/detalle-compra/<int:id>', methods=['PUT'])
@permiso_requerido("editar_compras")
def update_detalle_compra(id):
    try:
        detalle = DetalleCompra.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de compra no encontrado"}), 404
        data = request.get_json()
        compra = Compra.query.get(detalle.compra_id)
        old_cantidad = detalle.cantidad
        old_precio = detalle.precio_unidad
        old_subtotal = detalle.subtotal
        if 'compra_id' in data:
            nueva_compra = Compra.query.get(data['compra_id'])
            if not nueva_compra:
                return jsonify({"error": "La compra especificada no existe"}), 404
            detalle.compra_id = data['compra_id']
            compra = nueva_compra
        if 'producto_id' in data:
            producto = Producto.query.get(data['producto_id'])
            if not producto:
                return jsonify({"error": "El producto especificado no existe"}), 404
            if not producto.estado:
                return jsonify({"error": "No se puede asignar un producto inactivo"}), 400
            detalle.producto_id = data['producto_id']
        if 'cantidad' in data:
            try:
                nueva_cantidad = int(data['cantidad'])
            except (ValueError, TypeError):
                return jsonify({"error": "La cantidad debe ser un número válido"}), 400
            if nueva_cantidad <= 0:
                return jsonify({"error": "La cantidad debe ser mayor a 0"}), 400
            detalle.cantidad = nueva_cantidad
        if 'precio_unidad' in data:
            try:
                nuevo_precio = float(data['precio_unidad'])
            except (ValueError, TypeError):
                return jsonify({"error": "El precio debe ser un número válido"}), 400
            if nuevo_precio <= 0:
                return jsonify({"error": "El precio unitario debe ser mayor a 0"}), 400
            detalle.precio_unidad = nuevo_precio
        detalle.subtotal = detalle.cantidad * detalle.precio_unidad
        producto_afectado = Producto.query.get(detalle.producto_id)
        if producto_afectado:
            producto_afectado.stock -= old_cantidad
            producto_afectado.stock += detalle.cantidad
        compra.total = compra.total - old_subtotal + detalle.subtotal
        db.session.commit()
        return jsonify({"message": "Detalle de compra actualizado", "detalle": detalle.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar detalle de compra: {str(e)}"}), 500


@main_bp.route('/detalle-compra/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_compras")
def delete_detalle_compra(id):
    try:
        detalle = DetalleCompra.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de compra no encontrado"}), 404
        compra = Compra.query.get(detalle.compra_id)
        producto = Producto.query.get(detalle.producto_id)
        if producto and producto.stock < detalle.cantidad:
            return jsonify({
                "error": f"No se puede eliminar el detalle: El producto '{producto.nombre}' ya se vendió y no hay suficiente stock para revertir."
            }), 400
        if producto:
            producto.stock -= detalle.cantidad
        if compra:
            compra.total -= detalle.subtotal
        db.session.delete(detalle)
        db.session.commit()
        return jsonify({"message": "Detalle de compra eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar detalle de compra: {str(e)}"}), 500