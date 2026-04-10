from flask import jsonify, request
from app.database import db
from app.Models.models import Venta, DetalleVenta, Abono, Producto, Cliente, EstadoVenta
from datetime import datetime
from app.routes import main_bp


# ============================================================
# MÓDULO: VENTAS
# ============================================================

@main_bp.route('/ventas', methods=['GET'])
def get_ventas():
    try:
        ventas = Venta.query.all()
        return jsonify([venta.to_dict() for venta in ventas])
    except Exception as e:
        return jsonify({"error": f"Error al obtener ventas: {str(e)}"}), 500

@main_bp.route('/ventas', methods=['POST'])
def create_venta():
    try:
        data = request.get_json()
        
        # 1. Validar campos requeridos
        cliente_id = data.get('cliente_id')
        detalles_data = data.get('detalles', [])
        
        if not cliente_id:
            return jsonify({"error": "El campo 'cliente_id' es requerido"}), 400
        if not detalles_data:
            return jsonify({"error": "La venta debe tener al menos un detalle (producto)"}), 400
        
        # 2. Validar cliente
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({"error": "El cliente especificado no existe"}), 404
        if not cliente.estado:
            return jsonify({"error": "No se puede crear una venta para un cliente inactivo"}), 400
        
        # 3. Validar método de pago
        metodo_pago = data.get('metodo_pago', 'efectivo')
        if metodo_pago not in ['efectivo', 'transferencia', 'tarjeta']:
            return jsonify({"error": "Método de pago inválido. Opciones: efectivo, transferencia, tarjeta"}), 400
        
        # 4. Validar método de entrega
        metodo_entrega = data.get('metodo_entrega')
        if metodo_entrega and metodo_entrega not in ['tienda', 'domicilio']:
            return jsonify({"error": "Método de entrega inválido. Opciones: tienda, domicilio"}), 400
        
        # 5. Validar dirección de entrega si es domicilio
        if metodo_entrega == 'domicilio' and not data.get('direccion_entrega'):
            return jsonify({"error": "Para envío a domicilio, la dirección de entrega es requerida"}), 400
        
        # Crear la venta
        nueva_venta = Venta(
            cliente_id=cliente_id,
            pedido_id=data.get('pedido_id'),
            fecha_pedido=data.get('fecha_pedido'),
            fecha_venta=datetime.utcnow(),
            total=0,
            metodo_pago=metodo_pago,
            metodo_entrega=metodo_entrega,
            direccion_entrega=data.get('direccion_entrega', '').strip(),
            transferencia_comprobante=data.get('transferencia_comprobante'),
            estado=data.get('estado', 'completada')
        )
        
        db.session.add(nueva_venta)
        db.session.flush()
        
        total_venta = 0
        productos_vendidos = []
        
        # 6. Procesar cada detalle
        for idx, item in enumerate(detalles_data):
            producto_id = item.get('producto_id')
            cantidad = item.get('cantidad', 0)
            
            # Validar campos del detalle
            if not producto_id:
                db.session.rollback()
                return jsonify({"error": f"El detalle {idx+1} no tiene 'producto_id'"}), 400
            
            # Validar producto
            producto = Producto.query.get(producto_id)
            if not producto:
                db.session.rollback()
                return jsonify({"error": f"El producto con ID {producto_id} no existe"}), 404
            if not producto.estado:
                db.session.rollback()
                return jsonify({"error": f"El producto '{producto.nombre}' está inactivo"}), 400
            
            # Validar cantidad
            try:
                cantidad = int(cantidad)
            except (ValueError, TypeError):
                db.session.rollback()
                return jsonify({"error": f"La cantidad del detalle {idx+1} debe ser un número válido"}), 400
            
            if cantidad <= 0:
                db.session.rollback()
                return jsonify({"error": f"La cantidad del detalle {idx+1} debe ser mayor a 0"}), 400
            
            # Validar stock
            if producto.stock < cantidad:
                db.session.rollback()
                return jsonify({
                    "error": f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock}, solicitado: {cantidad}"
                }), 400
            
            # Validar precio
            try:
                precio_unitario = float(item.get('precio_unitario', producto.precio_venta))
            except (ValueError, TypeError):
                db.session.rollback()
                return jsonify({"error": f"El precio del detalle {idx+1} debe ser un número válido"}), 400
            
            if precio_unitario <= 0:
                db.session.rollback()
                return jsonify({"error": f"El precio unitario del detalle {idx+1} debe ser mayor a 0"}), 400
            
            # Validar descuento
            descuento = float(item.get('descuento', 0))
            if descuento < 0:
                db.session.rollback()
                return jsonify({"error": f"El descuento del detalle {idx+1} no puede ser negativo"}), 400
            if descuento > precio_unitario * cantidad:
                db.session.rollback()
                return jsonify({"error": f"El descuento del detalle {idx+1} no puede ser mayor al subtotal"}), 400
            
            subtotal = (cantidad * precio_unitario) - descuento
            total_venta += subtotal
            
            # Descontar stock
            producto.stock -= cantidad
            productos_vendidos.append(producto)
            
            # Crear detalle
            detalle = DetalleVenta(
                venta_id=nueva_venta.id,
                producto_id=producto_id,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                descuento=descuento,
                subtotal=subtotal
            )
            db.session.add(detalle)
        
        nueva_venta.total = total_venta
        db.session.commit()
        
        return jsonify({"message": "Venta creada exitosamente", "venta": nueva_venta.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear venta: {str(e)}"}), 500


@main_bp.route('/ventas/<int:id>', methods=['GET'])
def get_venta(id):
    try:
        venta = Venta.query.get(id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
        return jsonify(venta.to_dict())
    except Exception as e:
        return jsonify({"error": f"Error al obtener venta: {str(e)}"}), 500


@main_bp.route('/ventas/<int:id>', methods=['PUT'])
def update_venta(id):
    try:
        venta = Venta.query.get(id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
        
        data = request.get_json()
        
        # Validar estado
        if 'estado' in data:
            estados_validos = ['completada', 'anulada', 'pendiente_pago']
            if data['estado'] not in estados_validos:
                return jsonify({"error": f"Estado inválido. Opciones: {', '.join(estados_validos)}"}), 400
            
            # No permitir cambiar estado si ya está anulada
            if venta.estado == 'anulada' and data['estado'] != 'anulada':
                return jsonify({"error": "No se puede modificar una venta anulada"}), 400
            
            venta.estado = data['estado']
        
        # Validar método de pago
        if 'metodo_pago' in data:
            if data['metodo_pago'] not in ['efectivo', 'transferencia', 'tarjeta']:
                return jsonify({"error": "Método de pago inválido"}), 400
            venta.metodo_pago = data['metodo_pago']
        
        # Validar método de entrega
        if 'metodo_entrega' in data:
            if data['metodo_entrega'] not in ['tienda', 'domicilio']:
                return jsonify({"error": "Método de entrega inválido"}), 400
            venta.metodo_entrega = data['metodo_entrega']
        
        # Validar dirección
        if 'direccion_entrega' in data:
            venta.direccion_entrega = data['direccion_entrega'].strip()
        
        # Validar comprobante
        if 'transferencia_comprobante' in data:
            venta.transferencia_comprobante = data['transferencia_comprobante']
        
        # Validar total (no puede ser negativo)
        if 'total' in data:
            nuevo_total = float(data['total'])
            if nuevo_total < 0:
                return jsonify({"error": "El total no puede ser negativo"}), 400
            venta.total = nuevo_total
        
        db.session.commit()
        return jsonify({"message": "Venta actualizada", "venta": venta.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar venta: {str(e)}"}), 500


@main_bp.route('/ventas/<int:id>', methods=['DELETE'])
def delete_venta(id):
    try:
        venta = Venta.query.get(id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
        
        # 1. Validar que no tenga abonos registrados
        if venta.abonos and len(venta.abonos) > 0:
            return jsonify({"error": "No se puede eliminar una venta con abonos registrados"}), 400
        
        # 2. Validar que no esté anulada (opcional)
        if venta.estado == 'anulada':
            return jsonify({"error": "No se puede eliminar una venta ya anulada"}), 400
        
        # 3. Devolver stock al inventario antes de eliminar
        for detalle in venta.detalles:
            producto = Producto.query.get(detalle.producto_id)
            if producto:
                producto.stock += detalle.cantidad
        
        db.session.delete(venta)
        db.session.commit()
        return jsonify({"message": "Venta eliminada correctamente y stock restaurado"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar venta: {str(e)}"}), 500


@main_bp.route('/ventas/<int:venta_id>/detalles', methods=['GET'])
def get_detalles_venta_especifica(venta_id):
    try:
        venta = Venta.query.get(venta_id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
            
        detalles = DetalleVenta.query.filter_by(venta_id=venta_id).all()
        return jsonify([detalle.to_dict() for detalle in detalles])
        
    except Exception as e:
        return jsonify({"error": f"Error al obtener detalles de la venta: {str(e)}"}), 500


# ============================================================
# MÓDULO: TABLAS MAESTRAS - ESTADO VENTA
# ============================================================

@main_bp.route('/estado-venta', methods=['GET'])
def get_estados_venta():
    try:
        estados = EstadoVenta.query.all()
        return jsonify([estado.to_dict() for estado in estados])
    except Exception as e:
        return jsonify({"error": "Error al obtener estados de venta"}), 500

@main_bp.route('/estado-venta', methods=['POST'])
def create_estado_venta():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400

        estado = EstadoVenta(nombre=data['nombre'])
        db.session.add(estado)
        db.session.commit()
        return jsonify({"message": "Estado de venta creado", "estado": estado.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear estado de venta"}), 500

@main_bp.route('/estado-venta/<int:id>', methods=['PUT'])
def update_estado_venta(id):
    try:
        estado = EstadoVenta.query.get(id)
        if not estado:
            return jsonify({"error": "Estado de venta no encontrado"}), 404

        data = request.get_json()
        if 'nombre' in data:
            estado.nombre = data['nombre']

        db.session.commit()
        return jsonify({"message": "Estado de venta actualizado", "estado": estado.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar estado de venta"}), 500

@main_bp.route('/estado-venta/<int:id>', methods=['DELETE'])
def delete_estado_venta(id):
    try:
        estado = EstadoVenta.query.get(id)
        if not estado:
            return jsonify({"error": "Estado de venta no encontrado"}), 404

        db.session.delete(estado)
        db.session.commit()
        return jsonify({"message": "Estado de venta eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar estado de venta"}), 500


# ============================================================
# MÓDULO: ABONOS
# ============================================================

@main_bp.route('/ventas/<int:venta_id>/abonos', methods=['POST'])
def add_abono(venta_id):
    try:
        venta = Venta.query.get(venta_id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
        
        # Validar que la venta no esté anulada
        if venta.estado == 'anulada':
            return jsonify({"error": "No se pueden registrar abonos en una venta anulada"}), 400
        
        data = request.get_json()
        
        if 'monto_abonado' not in data:
            return jsonify({"error": "El campo 'monto_abonado' es requerido"}), 400
        
        try:
            monto = float(data['monto_abonado'])
        except (ValueError, TypeError):
            return jsonify({"error": "El monto debe ser un número válido"}), 400
        
        if monto <= 0:
            return jsonify({"error": "El monto del abono debe ser mayor a 0"}), 400
        
        # Calcular total abonado hasta ahora
        total_abonado = sum([a.monto_abonado for a in venta.abonos]) if venta.abonos else 0
        
        # Verificar que no exceda el total de la venta
        if total_abonado + monto > venta.total:
            restante = venta.total - total_abonado
            return jsonify({"error": f"El abono excede el saldo pendiente. Saldo restante: {restante}"}), 400
        
        abono = Abono(
            venta_id=venta.id,
            monto_abonado=monto,
            fecha=datetime.utcnow()
        )
        
        db.session.add(abono)
        db.session.commit()
        
        return jsonify({"message": "Abono registrado", "abono": abono.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al registrar abono: {str(e)}"}), 500


@main_bp.route('/ventas/<int:venta_id>/abonos', methods=['GET'])
def get_abonos(venta_id):
    try:
        venta = Venta.query.get(venta_id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404
            
        abonos = Abono.query.filter_by(venta_id=venta_id).all()
        return jsonify([abono.to_dict() for abono in abonos])
        
    except Exception as e:
        return jsonify({"error": f"Error al obtener abonos: {str(e)}"}), 500


@main_bp.route('/abonos/<int:id>', methods=['DELETE'])
def delete_abono(id):
    try:
        abono = Abono.query.get(id)
        if not abono:
            return jsonify({"error": "Abono no encontrado"}), 404
        
        venta = Venta.query.get(abono.venta_id)
        if venta and venta.estado == 'anulada':
            return jsonify({"error": "No se puede eliminar un abono de una venta anulada"}), 400
        
        db.session.delete(abono)
        db.session.commit()
        return jsonify({"message": "Abono eliminado correctamente"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar abono: {str(e)}"}), 500


# ============================================================
# MÓDULO: DETALLES DE VENTA
# ============================================================

@main_bp.route('/detalle-venta', methods=['GET'])
def get_detalles_venta():
    try:
        detalles = DetalleVenta.query.all()
        return jsonify([detalle.to_dict() for detalle in detalles])
    except Exception as e:
        return jsonify({"error": f"Error al obtener detalles de venta: {str(e)}"}), 500


@main_bp.route('/detalle-venta', methods=['POST'])
def create_detalle_venta():
    try:
        data = request.get_json()
        required_fields = ['venta_id', 'producto_id', 'cantidad', 'precio_unitario']
        
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        
        # Validar venta
        venta = Venta.query.get(data['venta_id'])
        if not venta:
            return jsonify({"error": "La venta especificada no existe"}), 404
        if venta.estado == 'anulada':
            return jsonify({"error": "No se puede agregar detalles a una venta anulada"}), 400
        
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
            precio_unitario = float(data['precio_unitario'])
        except (ValueError, TypeError):
            return jsonify({"error": "El precio unitario debe ser un número válido"}), 400
        
        if precio_unitario <= 0:
            return jsonify({"error": "El precio unitario debe ser mayor a 0"}), 400
        
        # Validar descuento
        descuento = float(data.get('descuento', 0))
        if descuento < 0:
            return jsonify({"error": "El descuento no puede ser negativo"}), 400
        
        subtotal = (cantidad * precio_unitario) - descuento
        if subtotal < 0:
            return jsonify({"error": "El subtotal no puede ser negativo"}), 400
        
        # Descontar stock
        producto.stock -= cantidad
        
        # Actualizar total de la venta
        venta.total += subtotal
        
        detalle = DetalleVenta(
            venta_id=data['venta_id'],
            producto_id=data['producto_id'],
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            descuento=descuento,
            subtotal=subtotal
        )
        
        db.session.add(detalle)
        db.session.commit()
        
        return jsonify({"message": "Detalle de venta creado", "detalle": detalle.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear detalle de venta: {str(e)}"}), 500


@main_bp.route('/detalle-venta/<int:id>', methods=['PUT'])
def update_detalle_venta(id):
    try:
        detalle = DetalleVenta.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de venta no encontrado"}), 404
        
        venta = Venta.query.get(detalle.venta_id)
        if not venta:
            return jsonify({"error": "La venta asociada no existe"}), 404
        if venta.estado == 'anulada':
            return jsonify({"error": "No se puede modificar una venta anulada"}), 400
        
        data = request.get_json()
        
        # Guardar valores antiguos para recalcular
        old_subtotal = detalle.subtotal
        old_cantidad = detalle.cantidad
        old_producto_id = detalle.producto_id
        
        # Actualizar producto
        if 'producto_id' in data:
            producto_nuevo = Producto.query.get(data['producto_id'])
            if not producto_nuevo:
                return jsonify({"error": "El producto especificado no existe"}), 404
            if not producto_nuevo.estado:
                return jsonify({"error": "No se puede asignar un producto inactivo"}), 400
            
            # Revertir stock del producto anterior
            producto_anterior = Producto.query.get(old_producto_id)
            if producto_anterior:
                producto_anterior.stock += old_cantidad
            
            detalle.producto_id = data['producto_id']
            
            # Validar stock del nuevo producto
            if producto_nuevo.stock < detalle.cantidad:
                return jsonify({"error": f"Stock insuficiente para '{producto_nuevo.nombre}'"}), 400
            
            producto_nuevo.stock -= detalle.cantidad
        
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
                producto_actual.stock += old_cantidad
                if producto_actual.stock < nueva_cantidad:
                    return jsonify({"error": f"Stock insuficiente para '{producto_actual.nombre}'"}), 400
                producto_actual.stock -= nueva_cantidad
            
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
        
        # Actualizar descuento
        if 'descuento' in data:
            nuevo_descuento = float(data['descuento'])
            if nuevo_descuento < 0:
                return jsonify({"error": "El descuento no puede ser negativo"}), 400
            detalle.descuento = nuevo_descuento
        
        # Recalcular subtotal
        detalle.subtotal = (detalle.cantidad * detalle.precio_unitario) - detalle.descuento
        if detalle.subtotal < 0:
            return jsonify({"error": "El subtotal no puede ser negativo"}), 400
        
        # Actualizar total de la venta
        venta.total = venta.total - old_subtotal + detalle.subtotal
        
        db.session.commit()
        return jsonify({"message": "Detalle de venta actualizado", "detalle": detalle.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar detalle de venta: {str(e)}"}), 500


@main_bp.route('/detalle-venta/<int:id>', methods=['DELETE'])
def delete_detalle_venta(id):
    try:
        detalle = DetalleVenta.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de venta no encontrado"}), 404
        
        venta = Venta.query.get(detalle.venta_id)
        if not venta:
            return jsonify({"error": "La venta asociada no existe"}), 404
        if venta.estado == 'anulada':
            return jsonify({"error": "No se puede modificar una venta anulada"}), 400
        
        # Revertir stock
        producto = Producto.query.get(detalle.producto_id)
        if producto:
            producto.stock += detalle.cantidad
        
        # Actualizar total de la venta
        venta.total -= detalle.subtotal
        
        db.session.delete(detalle)
        db.session.commit()
        
        return jsonify({"message": "Detalle de venta eliminado correctamente y stock restaurado"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar detalle de venta: {str(e)}"}), 500