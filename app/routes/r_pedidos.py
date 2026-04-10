from flask import jsonify, request
from app.database import db
from app.Models.models import Pedido, DetallePedido, Venta, DetalleVenta, Producto, Cliente, AbonoPedido, Abono
from datetime import datetime
from app.routes import main_bp


# ============================================================
# MÓDULO: PEDIDOS
# ============================================================

@main_bp.route('/pedidos', methods=['GET'])
def get_pedidos():
    try:
        pedidos = Pedido.query.all()
        return jsonify([pedido.to_dict() for pedido in pedidos])
    except Exception as e:
        return jsonify({"error": f"Error al obtener pedidos: {str(e)}"}), 500


@main_bp.route('/pedidos', methods=['POST'])
def create_pedido():
    try:
        data = request.get_json()
        
        # 1. Validar campos requeridos
        required_fields = ['cliente_id', 'metodo_pago', 'items']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"El campo '{field}' es requerido"}), 400
        
        # 2. Validar cliente
        cliente = Cliente.query.get(data['cliente_id'])
        if not cliente:
            return jsonify({"error": "El cliente especificado no existe"}), 404
        if not cliente.estado:
            return jsonify({"error": "No se puede crear un pedido para un cliente inactivo"}), 400
        
        # 3. Validar método de pago
        metodo_pago = data['metodo_pago']
        if metodo_pago not in ['efectivo', 'transferencia', 'tarjeta']:
            return jsonify({"error": "Método de pago inválido. Opciones: efectivo, transferencia, tarjeta"}), 400
        
        # 4. Validar método de entrega
        metodo_entrega = data.get('metodo_entrega')
        if metodo_entrega and metodo_entrega not in ['tienda', 'domicilio']:
            return jsonify({"error": "Método de entrega inválido. Opciones: tienda, domicilio"}), 400
        
        # 5. Validar dirección de entrega si es domicilio
        if metodo_entrega == 'domicilio' and not data.get('direccion_entrega'):
            return jsonify({"error": "Para envío a domicilio, la dirección de entrega es requerida"}), 400
        
        # 6. Validar items
        items = data['items']
        if not isinstance(items, list) or len(items) == 0:
            return jsonify({"error": "El pedido debe tener al menos un item"}), 400
        
        # Crear pedido
        pedido = Pedido(
            cliente_id=data['cliente_id'],
            metodo_pago=metodo_pago,
            metodo_entrega=metodo_entrega,
            direccion_entrega=data.get('direccion_entrega', '').strip(),
            estado=data.get('estado', 'pendiente'),
            transferencia_comprobante=data.get('transferencia_comprobante'),
            total=0,
            abono_acumulado=0
        )
        
        db.session.add(pedido)
        db.session.flush()
        
        total_calculado = 0
        productos_procesados = []
        
        # 7. Procesar cada item
        for idx, item_data in enumerate(items):
            # Validar campos del item
            if 'producto_id' not in item_data:
                db.session.rollback()
                return jsonify({"error": f"El item {idx+1} no tiene 'producto_id'"}), 400
            if 'cantidad' not in item_data:
                db.session.rollback()
                return jsonify({"error": f"El item {idx+1} no tiene 'cantidad'"}), 400
            
            # Validar producto
            producto = Producto.query.get(item_data['producto_id'])
            if not producto:
                db.session.rollback()
                return jsonify({"error": f"El producto con ID {item_data['producto_id']} no existe"}), 404
            if not producto.estado:
                db.session.rollback()
                return jsonify({"error": f"El producto '{producto.nombre}' está inactivo"}), 400
            
            # Validar cantidad
            try:
                cantidad = int(item_data['cantidad'])
            except (ValueError, TypeError):
                db.session.rollback()
                return jsonify({"error": f"La cantidad del item {idx+1} debe ser un número válido"}), 400
            
            if cantidad <= 0:
                db.session.rollback()
                return jsonify({"error": f"La cantidad del item {idx+1} debe ser mayor a 0"}), 400
            
            # Validar stock
            if producto.stock < cantidad:
                db.session.rollback()
                return jsonify({
                    "error": f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock}, solicitado: {cantidad}"
                }), 400
            
            # Usar precio del producto o el enviado (con validación)
            precio = float(item_data.get('precio_unitario', producto.precio_venta))
            if precio <= 0:
                db.session.rollback()
                return jsonify({"error": f"El precio unitario del item {idx+1} debe ser mayor a 0"}), 400
            
            subtotal = cantidad * precio
            total_calculado += subtotal
            
            # Descontar stock
            producto.stock -= cantidad
            productos_procesados.append(producto)
            
            # Crear detalle
            detalle = DetallePedido(
                pedido_id=pedido.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=precio,
                subtotal=subtotal
            )
            db.session.add(detalle)
        
        pedido.total = total_calculado
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
        return jsonify({"error": f"Error al obtener pedido: {str(e)}"}), 500


@main_bp.route('/pedidos/<int:id>', methods=['PUT'])
def update_pedido(id):
    try:
        pedido = Pedido.query.get(id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404
        
        data = request.get_json()
        estado_anterior = pedido.estado
        nuevo_estado = data.get('estado', pedido.estado)
        
        # Validar estados permitidos
        estados_permitidos = ['pendiente', 'confirmado', 'en_preparacion', 'enviado', 'entregado', 'cancelado']
        if nuevo_estado not in estados_permitidos:
            return jsonify({"error": f"Estado inválido. Opciones: {', '.join(estados_permitidos)}"}), 400
        
        # TRANSICIÓN A ENTREGADO (crear venta)
        if nuevo_estado == 'entregado' and estado_anterior != 'entregado':
            # Validar que el pedido no esté cancelado
            if pedido.estado == 'cancelado':
                return jsonify({"error": "No se puede entregar un pedido cancelado"}), 400
            
            # Validar estado previo permitido
            estados_previos_permitidos = ['enviado', 'confirmado', 'en_preparacion']
            if pedido.estado not in estados_previos_permitidos:
                return jsonify({"error": f"No se puede entregar un pedido en estado '{pedido.estado}'. Debe estar en: {', '.join(estados_previos_permitidos)}"}), 400
            
            # Validar que no tenga venta asociada
            if hasattr(pedido, 'venta') and pedido.venta:
                return jsonify({"error": "Este pedido ya generó una venta anteriormente"}), 400
            
            # Crear la venta
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
            
            # Migrar detalles a DetalleVenta
            for detalle_pedido in pedido.items:
                detalle_venta = DetalleVenta(
                    venta_id=venta.id,
                    producto_id=detalle_pedido.producto_id,
                    cantidad=detalle_pedido.cantidad,
                    precio_unitario=detalle_pedido.precio_unitario,
                    subtotal=detalle_pedido.subtotal
                )
                db.session.add(detalle_venta)
            
            # Si el pedido tiene abonos acumulados, registrar el abono total en la tabla Abono
            if pedido.abono_acumulado > 0:
                abono_total = Abono(
                    venta_id=venta.id,
                    monto_abonado=pedido.abono_acumulado,
                    fecha=datetime.utcnow()
                )
                db.session.add(abono_total)
            
            # Nota: El stock ya se descontó al crear el pedido, no se descuenta nuevamente
        
        # TRANSICIÓN A CANCELADO (revertir stock)
        if nuevo_estado == 'cancelado' and estado_anterior != 'cancelado':
            if pedido.estado == 'entregado':
                return jsonify({"error": "No se puede cancelar un pedido que ya fue entregado"}), 400
            
            # Revertir stock de cada producto
            for detalle in pedido.items:
                producto = Producto.query.get(detalle.producto_id)
                if producto:
                    producto.stock += detalle.cantidad
        
        # Actualizar campos permitidos
        if 'estado' in data:
            pedido.estado = nuevo_estado
        if 'transferencia_comprobante' in data:
            pedido.transferencia_comprobante = data['transferencia_comprobante']
        if 'direccion_entrega' in data:
            pedido.direccion_entrega = data['direccion_entrega'].strip()
        if 'metodo_pago' in data:
            if data['metodo_pago'] not in ['efectivo', 'transferencia', 'tarjeta']:
                return jsonify({"error": "Método de pago inválido"}), 400
            pedido.metodo_pago = data['metodo_pago']
        if 'metodo_entrega' in data:
            if data['metodo_entrega'] not in ['tienda', 'domicilio']:
                return jsonify({"error": "Método de entrega inválido"}), 400
            pedido.metodo_entrega = data['metodo_entrega']
        if 'total' in data:
            nuevo_total = float(data['total'])
            if nuevo_total < 0:
                return jsonify({"error": "El total no puede ser negativo"}), 400
            pedido.total = nuevo_total
        
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
        
        # Validar que no tenga venta asociada
        venta_asociada = Venta.query.filter_by(pedido_id=id).first()
        if venta_asociada:
            return jsonify({"error": "No se puede eliminar un pedido que ya generó una venta"}), 400
        
        # Validar que no esté entregado
        if pedido.estado == 'entregado':
            return jsonify({"error": "No se puede eliminar un pedido entregado"}), 400
        
        # Revertir stock antes de eliminar
        for detalle in pedido.items:
            producto = Producto.query.get(detalle.producto_id)
            if producto:
                producto.stock += detalle.cantidad
        
        # Eliminar abonos del pedido primero
        AbonoPedido.query.filter_by(pedido_id=id).delete()
        
        # Eliminar detalles y pedido
        DetallePedido.query.filter_by(pedido_id=id).delete()
        db.session.delete(pedido)
        db.session.commit()
        
        return jsonify({"message": "Pedido eliminado correctamente y stock restaurado"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar pedido: {str(e)}"}), 500


@main_bp.route('/pedidos/cliente/<int:cliente_id>', methods=['GET'])
def get_pedidos_cliente(cliente_id):
    try:
        # Validar cliente
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404
        
        pedidos = Pedido.query.filter_by(cliente_id=cliente_id).order_by(Pedido.fecha.desc()).all()
        return jsonify([pedido.to_dict() for pedido in pedidos])
        
    except Exception as e:
        return jsonify({"error": f"Error al obtener pedidos del cliente: {str(e)}"}), 500


@main_bp.route('/pedidos/<int:pedido_id>/detalles', methods=['GET'])
def get_detalles_de_pedido(pedido_id):
    try:
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404
            
        detalles = DetallePedido.query.filter_by(pedido_id=pedido_id).all()
        return jsonify([detalle.to_dict() for detalle in detalles])
        
    except Exception as e:
        return jsonify({"error": f"Error al obtener detalles del pedido: {str(e)}"}), 500


# ============================================================
# MÓDULO: ABONOS DE PEDIDOS
# ============================================================

@main_bp.route('/pedidos/<int:id>/abonos', methods=['GET'])
def get_abonos_pedido(id):
    try:
        pedido = Pedido.query.get(id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404
        abonos = [a.to_dict() for a in pedido.abonos_pedido]
        return jsonify(abonos)
    except Exception as e:
        return jsonify({"error": f"Error al obtener abonos: {str(e)}"}), 500


@main_bp.route('/pedidos/<int:id>/abonos', methods=['POST'])
def add_abono_pedido(id):
    try:
        pedido = Pedido.query.get(id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404

        # No permitir abonos si ya está entregado o cancelado
        if pedido.estado in ['entregado', 'cancelado']:
            return jsonify({"error": f"No se pueden registrar abonos en un pedido {pedido.estado}"}), 400

        data = request.get_json()
        monto = data.get('monto_abonado')
        if not monto or float(monto) <= 0:
            return jsonify({"error": "El monto del abono debe ser mayor a 0"}), 400

        monto = float(monto)
        nuevo_acumulado = pedido.abono_acumulado + monto

        if nuevo_acumulado > pedido.total:
            return jsonify({"error": f"El abono excede el total del pedido. Máximo permitido: {pedido.total - pedido.abono_acumulado}"}), 400

        # Registrar el abono en la nueva tabla
        abono_pedido = AbonoPedido(
            pedido_id=pedido.id,
            monto=monto,
            observacion=data.get('observacion', '')
        )
        db.session.add(abono_pedido)

        # Actualizar acumulado
        pedido.abono_acumulado = nuevo_acumulado

        # Verificar si se completó el pago
        pago_completo = nuevo_acumulado >= pedido.total
        venta_id = None

        if pago_completo:
            # Crear venta si el pedido no está entregado
            if pedido.estado != 'entregado':
                # Verificar si ya existe venta
                venta_existente = Venta.query.filter_by(pedido_id=pedido.id).first()
                if not venta_existente:
                    # Crear la venta
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
                    venta_id = venta.id
                    
                    # Migrar detalles (DetallePedido -> DetalleVenta)
                    for detalle_pedido in pedido.items:
                        detalle_venta = DetalleVenta(
                            venta_id=venta.id,
                            producto_id=detalle_pedido.producto_id,
                            cantidad=detalle_pedido.cantidad,
                            precio_unitario=detalle_pedido.precio_unitario,
                            subtotal=detalle_pedido.subtotal
                        )
                        db.session.add(detalle_venta)
                    
                    # Registrar un Abono (tabla original) por el total pagado
                    abono_total = Abono(
                        venta_id=venta.id,
                        monto_abonado=pedido.total,
                        fecha=datetime.utcnow()
                    )
                    db.session.add(abono_total)

                # Cambiar estado del pedido a 'entregado'
                pedido.estado = 'entregado'

        db.session.commit()

        return jsonify({
            "message": "Abono registrado",
            "abono_acumulado": pedido.abono_acumulado,
            "saldo_pendiente": pedido.total - pedido.abono_acumulado,
            "pago_completo": pago_completo,
            "venta_id": venta_id if pago_completo else None
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al registrar abono: {str(e)}"}), 500


# ============================================================
# MÓDULO: DETALLES DE PEDIDO
# ============================================================

@main_bp.route('/detalle-pedido', methods=['GET'])
def get_detalles_pedido():
    try:
        pedido_id = request.args.get('pedido_id', type=int)
        if pedido_id:
            # Validar que el pedido existe
            pedido = Pedido.query.get(pedido_id)
            if not pedido:
                return jsonify({"error": "Pedido no encontrado"}), 404
            detalles = DetallePedido.query.filter_by(pedido_id=pedido_id).all()
        else:
            detalles = DetallePedido.query.all()
        return jsonify([detalle.to_dict() for detalle in detalles])
        
    except Exception as e:
        return jsonify({"error": f"Error al obtener detalles de pedido: {str(e)}"}), 500


@main_bp.route('/detalle-pedido', methods=['POST'])
def create_detalle_pedido():
    try:
        data = request.get_json()
        required_fields = ['pedido_id', 'producto_id', 'cantidad', 'precio_unitario']
        
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo '{field}' es requerido"}), 400
        
        # Validar pedido
        pedido = Pedido.query.get(data['pedido_id'])
        if not pedido:
            return jsonify({"error": "El pedido especificado no existe"}), 404
        
        # Validar estado del pedido
        estados_permitidos = ['pendiente', 'confirmado']
        if pedido.estado not in estados_permitidos:
            return jsonify({"error": f"No se puede modificar un pedido en estado '{pedido.estado}'. Solo se pueden modificar pedidos pendientes o confirmados"}), 400
        
        # Validar producto
        producto = Producto.query.get(data['producto_id'])
        if not producto:
            return jsonify({"error": "El producto especificado no existe"}), 404
        if not producto.estado:
            return jsonify({"error": "No se puede agregar un producto inactivo"}), 400
        
        # Validar cantidad
        try:
            cantidad = int(data['cantidad'])
        except (ValueError, TypeError):
            return jsonify({"error": "La cantidad debe ser un número válido"}), 400
        
        if cantidad <= 0:
            return jsonify({"error": "La cantidad debe ser mayor a 0"}), 400
        
        # Validar stock
        if producto.stock < cantidad:
            return jsonify({
                "error": f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock}"
            }), 400
        
        # Validar precio
        try:
            precio = float(data['precio_unitario'])
        except (ValueError, TypeError):
            return jsonify({"error": "El precio unitario debe ser un número válido"}), 400
        
        if precio <= 0:
            return jsonify({"error": "El precio unitario debe ser mayor a 0"}), 400
        
        subtotal = cantidad * precio
        
        # Descontar stock
        producto.stock -= cantidad
        
        # Crear detalle
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
        
        # Validar estado del pedido
        estados_permitidos = ['pendiente', 'confirmado']
        if pedido.estado not in estados_permitidos:
            return jsonify({"error": f"No se puede modificar un pedido en estado '{pedido.estado}'"}), 400
        
        data = request.get_json()
        old_subtotal = detalle.subtotal
        old_cantidad = detalle.cantidad
        old_producto_id = detalle.producto_id
        
        # Actualizar producto
        if 'producto_id' in data:
            producto = Producto.query.get(data['producto_id'])
            if not producto:
                return jsonify({"error": "El producto especificado no existe"}), 404
            if not producto.estado:
                return jsonify({"error": "No se puede asignar un producto inactivo"}), 400
            
            # Revertir stock del producto anterior
            producto_anterior = Producto.query.get(old_producto_id)
            if producto_anterior:
                producto_anterior.stock += old_cantidad
            
            detalle.producto_id = data['producto_id']
            
            # Validar stock del nuevo producto
            if producto.stock < detalle.cantidad:
                return jsonify({"error": f"Stock insuficiente para '{producto.nombre}'"}), 400
            
            producto.stock -= detalle.cantidad
        
        # Actualizar cantidad
        if 'cantidad' in data:
            try:
                nueva_cantidad = int(data['cantidad'])
            except (ValueError, TypeError):
                return jsonify({"error": "La cantidad debe ser un número válido"}), 400
            
            if nueva_cantidad <= 0:
                return jsonify({"error": "La cantidad debe ser mayor a 0"}), 400
            
            # Ajustar stock
            producto_actual = Producto.query.get(detalle.producto_id)
            if producto_actual:
                producto_actual.stock += old_cantidad  # Revertir vieja
                if producto_actual.stock < nueva_cantidad:
                    return jsonify({"error": f"Stock insuficiente para '{producto_actual.nombre}'"}), 400
                producto_actual.stock -= nueva_cantidad  # Aplicar nueva
            
            detalle.cantidad = nueva_cantidad
        
        # Actualizar precio
        if 'precio_unitario' in data:
            try:
                nuevo_precio = float(data['precio_unitario'])
            except (ValueError, TypeError):
                return jsonify({"error": "El precio debe ser un número válido"}), 400
            
            if nuevo_precio <= 0:
                return jsonify({"error": "El precio unitario debe ser mayor a 0"}), 400
            detalle.precio_unitario = nuevo_precio
        
        # Recalcular subtotal
        detalle.subtotal = detalle.cantidad * detalle.precio_unitario
        
        # Actualizar total del pedido
        pedido.total = pedido.total - old_subtotal + detalle.subtotal
        
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
        
        # Validar estado del pedido
        estados_permitidos = ['pendiente', 'confirmado']
        if pedido.estado not in estados_permitidos:
            return jsonify({"error": f"No se puede modificar un pedido en estado '{pedido.estado}'"}), 400
        
        # Revertir stock
        producto = Producto.query.get(detalle.producto_id)
        if producto:
            producto.stock += detalle.cantidad
        
        # Actualizar total del pedido
        pedido.total -= detalle.subtotal
        
        db.session.delete(detalle)
        db.session.commit()
        
        return jsonify({"message": "Detalle de pedido eliminado correctamente y stock restaurado"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar detalle de pedido: {str(e)}"}), 500