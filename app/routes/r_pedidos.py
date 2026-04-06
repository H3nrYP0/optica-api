from flask import jsonify, request
from app.database import db
from app.Models.models import Pedido, DetallePedido, Venta, DetalleVenta, Producto
from datetime import datetime
from app.routes import main_bp

@main_bp.route('/pedidos', methods=['GET'])
def get_pedidos():
    try:
        pedidos = Pedido.query.all()
        return jsonify([pedido.to_dict() for pedido in pedidos])
    except Exception as e:
        return jsonify({"error": "Error al obtener pedidos"}), 500

@main_bp.route('/pedidos', methods=['POST'])
def create_pedido():
    try:
        data = request.get_json()
        required_fields = ['cliente_id', 'metodo_pago', 'metodo_entrega']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo '{field}' es requerido"}), 400
        pedido = Pedido(
            cliente_id=data['cliente_id'],
            metodo_pago=data['metodo_pago'],
            metodo_entrega=data['metodo_entrega'],
            direccion_entrega=data.get('direccion_entrega'),
            estado=data.get('estado', 'pendiente'),
            transferencia_comprobante=data.get('transferencia_comprobante')
        )
        total_calculado = 0
        if 'items' in data and isinstance(data['items'], list):
            for item_data in data['items']:
                if not all(k in item_data for k in ('producto_id', 'cantidad', 'precio_unitario')):
                    return jsonify({"error": "Cada item debe tener producto_id, cantidad y precio_unitario"}), 400
                cantidad = int(item_data['cantidad'])
                precio = float(item_data['precio_unitario'])
                subtotal = cantidad * precio
                detalle = DetallePedido(
                    producto_id=item_data['producto_id'],
                    cantidad=cantidad,
                    precio_unitario=precio,
                    subtotal=subtotal
                )
                pedido.items.append(detalle)
                total_calculado += subtotal
            pedido.total = total_calculado
        else:
            if 'total' not in data:
                return jsonify({"error": "Debe enviar 'total' o la lista de 'items'"}), 400
            pedido.total = float(data['total'])
        db.session.add(pedido)
        db.session.commit()
        return jsonify({"message": "Pedido creado exitosamente", "pedido": pedido.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear pedido: {str(e)}"}), 500

@main_bp.route('/pedidos/<int:id>', methods=['GET'])
def get_pedido(id):
    try:
        pedido = Pedido.query.get(id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404
        return jsonify(pedido.to_dict())
    except Exception as e:
        return jsonify({"error": "Error al obtener pedido"}), 500

@main_bp.route('/pedidos/<int:id>', methods=['PUT'])
def update_pedido(id):
    try:
        pedido = Pedido.query.get(id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404
        data = request.get_json()
        estado_anterior = pedido.estado
        nuevo_estado = data.get('estado', pedido.estado)
        if nuevo_estado == 'entregado' and estado_anterior != 'entregado':
            estados_permitidos = ['enviado', 'confirmado', 'en_preparacion']
            if pedido.estado not in estados_permitidos:
                return jsonify({"error": f"No se puede entregar un pedido en estado '{pedido.estado}'"}), 400
            if hasattr(pedido, 'venta') and pedido.venta:
                return jsonify({"error": "Este pedido ya generó una venta anteriormente"}), 400
            venta = Venta(
                pedido_id=pedido.id,
                cliente_id=pedido.cliente_id,
                fecha_pedido=pedido.fecha,
                fecha_venta=datetime.utcnow(),
                total=pedido.total,
                metodo_pago=pedido.metodo_pago,
                metodo_entrega=pedido.metodo_entrega,
                direccion_entrega=pedido.direccion_entrega,
                transferencia_comprobante=pedido.transferencia_comprobante,
                estado='completada'
            )
            db.session.add(venta)
            db.session.flush()
            for detalle_pedido in pedido.items:
                detalle_venta = DetalleVenta(
                    venta_id=venta.id,
                    producto_id=detalle_pedido.producto_id,
                    cantidad=detalle_pedido.cantidad,
                    precio_unitario=detalle_pedido.precio_unitario,
                    subtotal=detalle_pedido.subtotal
                )
                db.session.add(detalle_venta)
            for detalle in pedido.items:
                producto = Producto.query.get(detalle.producto_id)
                if producto:
                    producto.stock -= detalle.cantidad
                    if producto.stock < 0:
                        producto.stock = 0
        if 'estado' in data:
            pedido.estado = data['estado']
        if 'transferencia_comprobante' in data:
            pedido.transferencia_comprobante = data['transferencia_comprobante']
        if 'direccion_entrega' in data:
            pedido.direccion_entrega = data['direccion_entrega']
        if 'metodo_pago' in data:
            pedido.metodo_pago = data['metodo_pago']
        if 'metodo_entrega' in data:
            pedido.metodo_entrega = data['metodo_entrega']
        if 'total' in data:
            pedido.total = float(data['total'])
        db.session.commit()
        return jsonify({"message": "Pedido actualizado", "pedido": pedido.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar pedido: {str(e)}"}), 500

@main_bp.route('/pedidos/<int:id>', methods=['DELETE'])
def delete_pedido(id):
    try:
        pedido = Pedido.query.get(id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404
        venta_asociada = Venta.query.filter_by(pedido_id=id).first()
        if venta_asociada:
            return jsonify({"error": "No se puede eliminar un pedido que ya generó una venta"}), 400
        DetallePedido.query.filter_by(pedido_id=id).delete()
        db.session.delete(pedido)
        db.session.commit()
        return jsonify({"message": "Pedido eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar pedido: {str(e)}"}), 500

@main_bp.route('/pedidos/cliente/<int:cliente_id>', methods=['GET'])
def get_pedidos_cliente(cliente_id):
    try:
        pedidos = Pedido.query.filter_by(cliente_id=cliente_id).order_by(Pedido.fecha.desc()).all()
        return jsonify([pedido.to_dict() for pedido in pedidos])
    except Exception as e:
        return jsonify({"error": "Error al obtener pedidos del cliente"}), 500

@main_bp.route('/pedidos/<int:pedido_id>/detalles', methods=['GET'])
def get_detalles_de_pedido(pedido_id):
    try:
        detalles = DetallePedido.query.filter_by(pedido_id=pedido_id).all()
        return jsonify([detalle.to_dict() for detalle in detalles])
    except Exception as e:
        return jsonify({"error": "Error al obtener detalles del pedido"}), 500

@main_bp.route('/detalle-pedido', methods=['GET'])
def get_detalles_pedido():
    try:
        pedido_id = request.args.get('pedido_id', type=int)
        if pedido_id:
            detalles = DetallePedido.query.filter_by(pedido_id=pedido_id).all()
        else:
            detalles = DetallePedido.query.all()
        return jsonify([detalle.to_dict() for detalle in detalles])
    except Exception as e:
        return jsonify({"error": "Error al obtener detalles de pedido"}), 500

@main_bp.route('/detalle-pedido', methods=['POST'])
def create_detalle_pedido():
    try:
        data = request.get_json()
        required_fields = ['pedido_id', 'producto_id', 'cantidad', 'precio_unitario']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo '{field}' es requerido"}), 400
        pedido = Pedido.query.get(data['pedido_id'])
        if not pedido:
            return jsonify({"error": "El pedido especificado no existe"}), 404
        if pedido.estado in ['entregado', 'cancelado']:
            return jsonify({"error": f"No se puede modificar un pedido en estado '{pedido.estado}'"}), 400
        cantidad = int(data['cantidad'])
        precio = float(data['precio_unitario'])
        subtotal = cantidad * precio
        detalle = DetallePedido(
            pedido_id=data['pedido_id'],
            producto_id=data['producto_id'],
            cantidad=cantidad,
            precio_unitario=precio,
            subtotal=subtotal
        )
        db.session.add(detalle)
        pedido.total += subtotal
        db.session.commit()
        return jsonify({"message": "Detalle de pedido creado", "detalle": detalle.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear detalle de pedido: {str(e)}"}), 500

@main_bp.route('/detalle-pedido/<int:id>', methods=['PUT'])
def update_detalle_pedido(id):
    try:
        detalle = DetallePedido.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de pedido no encontrado"}), 404
        pedido = Pedido.query.get(detalle.pedido_id)
        if not pedido:
            return jsonify({"error": "El pedido asociado no existe"}), 404
        if pedido.estado in ['entregado', 'cancelado']:
            return jsonify({"error": f"No se puede modificar un pedido en estado '{pedido.estado}'"}), 400
        data = request.get_json()
        old_subtotal = detalle.subtotal
        if 'producto_id' in data:
            detalle.producto_id = data['producto_id']
        if 'cantidad' in data:
            detalle.cantidad = int(data['cantidad'])
        if 'precio_unitario' in data:
            detalle.precio_unitario = float(data['precio_unitario'])
        nuevo_subtotal = detalle.cantidad * detalle.precio_unitario
        detalle.subtotal = nuevo_subtotal
        pedido.total = pedido.total - old_subtotal + nuevo_subtotal
        db.session.commit()
        return jsonify({"message": "Detalle de pedido actualizado", "detalle": detalle.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar detalle de pedido: {str(e)}"}), 500

@main_bp.route('/detalle-pedido/<int:id>', methods=['DELETE'])
def delete_detalle_pedido(id):
    try:
        detalle = DetallePedido.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de pedido no encontrado"}), 404
        pedido = Pedido.query.get(detalle.pedido_id)
        if not pedido:
            return jsonify({"error": "El pedido asociado no existe"}), 404
        if pedido.estado in ['entregado', 'cancelado']:
            return jsonify({"error": f"No se puede modificar un pedido en estado '{pedido.estado}'"}), 400
        pedido.total -= detalle.subtotal
        db.session.delete(detalle)
        db.session.commit()
        return jsonify({"message": "Detalle de pedido eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar detalle de pedido: {str(e)}"}), 500