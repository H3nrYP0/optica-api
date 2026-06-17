"""
Módulo de pedidos: gestión de pedidos de clientes, detalles, abonos y estados.
Permisos granulares:
- Pedidos: ver_pedidos, crear_pedidos, editar_pedidos, eliminar_pedidos
- Detalles de pedido y abonos: mismos permisos de pedidos
- Estados de pedido: gestionar_configuracion
Ahora soporta productos y servicios (item puede tener producto_id o servicio_id)
"""

from flask import jsonify, request
from app.database import db
from app.Models.models import Pedido, DetallePedido, Usuario, Venta, DetalleVenta, Producto, Servicio, Cliente, Abono, EstadoPedido
from datetime import datetime
from app.routes import main_bp
from app.auth.decorators import permiso_requerido
from flask_jwt_extended import jwt_required, get_jwt_identity

MAX_PER_PAGE = 10

# ============================================================
# MÓDULO: PEDIDOS (CRUD)
# ============================================================

@main_bp.route('/pedidos', methods=['GET'])
@permiso_requerido("ver_pedidos")
def get_pedidos():
    """
    Listar pedidos con paginación, búsqueda y filtros.
    Query params:
        page          (int)
        per_page      (int) máx 10
        search        (str) busca en cliente (nombre/apellido)
        cliente_id    (int)
        estado_id     (int)
        metodo_pago   (str)
        metodo_entrega(str)
        fecha_desde   (str) YYYY-MM-DD
        fecha_hasta   (str)
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        search = request.args.get('search', '', type=str).strip()
        cliente_id = request.args.get('cliente_id', type=int)
        estado_id = request.args.get('estado_id', type=int)
        metodo_pago = request.args.get('metodo_pago', '', type=str).strip().lower()
        metodo_entrega = request.args.get('metodo_entrega', '', type=str).strip().lower()
        fecha_desde = request.args.get('fecha_desde', '', type=str).strip()
        fecha_hasta = request.args.get('fecha_hasta', '', type=str).strip()

        query = Pedido.query.join(Cliente, Pedido.cliente_id == Cliente.id)

        if cliente_id:
            query = query.filter(Pedido.cliente_id == cliente_id)
        if estado_id:
            query = query.filter(Pedido.estado_id == estado_id)
        if metodo_pago:
            query = query.filter(Pedido.metodo_pago == metodo_pago)
        if metodo_entrega:
            query = query.filter(Pedido.metodo_entrega == metodo_entrega)
        if fecha_desde:
            try:
                fd = datetime.strptime(fecha_desde, '%Y-%m-%d')
                query = query.filter(Pedido.fecha >= fd)
            except ValueError:
                return jsonify({"error": "Formato fecha_desde inválido"}), 400
        if fecha_hasta:
            try:
                fh = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                query = query.filter(Pedido.fecha <= fh)
            except ValueError:
                return jsonify({"error": "Formato fecha_hasta inválido"}), 400
        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(
                    Cliente.nombre.ilike(like),
                    Cliente.apellido.ilike(like),
                    Cliente.correo.ilike(like),
                    Cliente.numero_documento.ilike(like)
                )
            )
        query = query.order_by(Pedido.fecha.desc())

        has_pagination = 'page' in request.args or 'per_page' in request.args
        has_filters = cliente_id or estado_id or metodo_pago or metodo_entrega or fecha_desde or fecha_hasta or search
        if not has_pagination and not has_filters:
            pedidos = query.all()
            return jsonify([pedido.to_dict() for pedido in pedidos])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [pedido.to_dict() for pedido in pagination.items],
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
        return jsonify({"error": f"Error al obtener pedidos: {str(e)}"}), 500


@main_bp.route('/pedidos', methods=['POST'])
@jwt_required()
def create_pedido():
    try:
        data = request.get_json()
        required_fields = ['cliente_id', 'metodo_pago', 'items']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"El campo '{field}' es requerido"}), 400

        # Obtener usuario autenticado desde el token
        usuario_actual_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_actual_id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        cliente_id_payload = data['cliente_id']

        # ============================================================
        # FIX: Autorización diferenciada
        # - Admin/empleado pueden elegir cualquier cliente_id
        # - Cliente común solo puede pedir para sí mismo
        # ============================================================
        if usuario.rol in ['admin', 'empleado']:
            # Permiso total: no se valida vinculación
            pass
        else:
            # Es cliente: debe tener cliente_id y coincidir con el payload
            if not usuario.cliente_id:
                return jsonify({"error": "El usuario no está vinculado a un cliente"}), 400
            if usuario.cliente_id != cliente_id_payload:
                return jsonify({"error": "No tienes permiso para crear pedidos en nombre de otro cliente"}), 403

        # Validar cliente
        cliente = Cliente.query.get(cliente_id_payload)
        if not cliente or not cliente.estado:
            return jsonify({"error": "Cliente no existe o está inactivo"}), 404

        # Validar método de pago
        metodo_pago = data['metodo_pago']
        if metodo_pago not in ['efectivo', 'transferencia', 'tarjeta']:
            return jsonify({"error": "Método de pago inválido. Opciones: efectivo, transferencia, tarjeta"}), 400

        metodo_entrega = data.get('metodo_entrega')
        if metodo_entrega and metodo_entrega not in ['tienda', 'domicilio']:
            return jsonify({"error": "Método de entrega inválido. Opciones: tienda, domicilio"}), 400
        if metodo_entrega == 'domicilio' and not data.get('direccion_entrega'):
            return jsonify({"error": "Para envío a domicilio, la dirección de entrega es requerida"}), 400

        items = data['items']
        if not isinstance(items, list) or len(items) == 0:
            return jsonify({"error": "El pedido debe tener al menos un item"}), 400

        estado_pendiente = EstadoPedido.query.filter_by(nombre='pendiente').first()
        if not estado_pendiente:
            return jsonify({"error": "Estado 'pendiente' no encontrado en la base de datos"}), 500

        total_calculado = 0.0
        detalles_temp = []
        productos_procesados = []

        for idx, item_data in enumerate(items):
            producto_id = item_data.get('producto_id')
            servicio_id = item_data.get('servicio_id')
            cantidad = item_data.get('cantidad', 1)

            if not producto_id and not servicio_id:
                db.session.rollback()
                return jsonify({"error": f"Item {idx+1}: debe tener 'producto_id' o 'servicio_id'"}), 400
            if producto_id and servicio_id:
                db.session.rollback()
                return jsonify({"error": f"Item {idx+1}: no puede tener ambos, solo uno"}), 400

            try:
                cantidad = int(cantidad)
                if cantidad <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                db.session.rollback()
                return jsonify({"error": f"Item {idx+1}: la cantidad debe ser un número positivo"}), 400

            precio_unitario = None
            if producto_id:
                producto = Producto.query.get(producto_id)
                if not producto or not producto.estado:
                    db.session.rollback()
                    return jsonify({"error": f"Producto ID {producto_id} no existe o está inactivo"}), 404
                if producto.stock < cantidad:
                    db.session.rollback()
                    return jsonify({"error": f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock}"}), 400
                precio_unitario = float(item_data.get('precio_unitario', producto.precio_venta))
                if precio_unitario <= 0:
                    db.session.rollback()
                    return jsonify({"error": f"Item {idx+1}: precio unitario inválido"}), 400
                productos_procesados.append((producto, cantidad))
            else:
                servicio = Servicio.query.get(servicio_id)
                if not servicio or not servicio.estado:
                    db.session.rollback()
                    return jsonify({"error": f"Servicio ID {servicio_id} no existe o está inactivo"}), 404
                precio_unitario = float(item_data.get('precio_unitario', servicio.precio))
                if precio_unitario <= 0:
                    db.session.rollback()
                    return jsonify({"error": f"Item {idx+1}: precio unitario inválido"}), 400

            subtotal = cantidad * precio_unitario
            total_calculado += subtotal

            detalles_temp.append({
                'producto_id': producto_id,
                'servicio_id': servicio_id,
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
                'subtotal': subtotal
            })

        costo_envio = 0.0
        if metodo_entrega == 'domicilio':
            costo_envio = 20000.0

        total_con_envio = total_calculado + costo_envio

        pedido = Pedido(
            cliente_id=cliente_id_payload,
            metodo_pago=metodo_pago,
            metodo_entrega=metodo_entrega,
            direccion_entrega=data.get('direccion_entrega', '').strip(),
            departamento_entrega=data.get('departamento_entrega', '').strip(),
            municipio_entrega=data.get('municipio_entrega', '').strip(),
            barrio_entrega=data.get('barrio_entrega', '').strip(),
            codigo_postal_entrega=data.get('codigo_postal_entrega', '').strip(),
            estado_id=estado_pendiente.id,
            transferencia_comprobante=data.get('transferencia_comprobante'),
            total=total_con_envio,
            costo_envio=costo_envio,
            abono_acumulado=0
        )
        db.session.add(pedido)
        db.session.flush()

        for detalle_data in detalles_temp:
            detalle = DetallePedido(
                pedido_id=pedido.id,
                producto_id=detalle_data['producto_id'],
                servicio_id=detalle_data['servicio_id'],
                cantidad=detalle_data['cantidad'],
                precio_unitario=detalle_data['precio_unitario'],
                subtotal=detalle_data['subtotal']
            )
            db.session.add(detalle)

        for producto, cantidad in productos_procesados:
            producto.stock -= cantidad

        db.session.commit()
        return jsonify({"message": "Pedido creado exitosamente", "pedido": pedido.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear pedido: {str(e)}"}), 500
    
    
@main_bp.route('/pedidos/<int:id>', methods=['GET'])
@permiso_requerido("ver_pedidos")
def get_pedido(id):
    try:
        pedido = Pedido.query.get(id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404
        return jsonify(pedido.to_dict())
    except Exception as e:
        return jsonify({"error": f"Error al obtener pedido: {str(e)}"}), 500


@main_bp.route('/pedidos/<int:id>', methods=['PUT'])
@permiso_requerido("editar_pedidos")
def update_pedido(id):
    try:
        pedido = Pedido.query.get(id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404

        data = request.get_json()
        estado_anterior_id = pedido.estado_id
        nuevo_estado_id = data.get('estado_id')
        if not nuevo_estado_id and 'estado' in data:
            estado_nombre = data['estado']
            estado_obj = EstadoPedido.query.filter_by(nombre=estado_nombre).first()
            if not estado_obj:
                return jsonify({"error": f"Estado '{estado_nombre}' no existe"}), 400
            nuevo_estado_id = estado_obj.id
        elif not nuevo_estado_id:
            nuevo_estado_id = estado_anterior_id

        nuevo_estado_obj = EstadoPedido.query.get(nuevo_estado_id)
        if not nuevo_estado_obj:
            return jsonify({"error": "Estado inválido"}), 400

        estado_anterior_nombre = pedido.estado.nombre if pedido.estado else None
        nuevo_estado_nombre = nuevo_estado_obj.nombre

        if nuevo_estado_nombre == 'anulado' and estado_anterior_nombre != 'anulado':
            if estado_anterior_nombre == 'pagado':
                return jsonify({"error": "No se puede anular un pedido ya pagado"}), 400
            for detalle in pedido.items:
                if detalle.producto_id:
                    producto = Producto.query.get(detalle.producto_id)
                    if producto:
                        producto.stock += detalle.cantidad

        if nuevo_estado_nombre == 'pagado' and estado_anterior_nombre != 'pagado':
            if hasattr(pedido, 'venta') and pedido.venta:
                return jsonify({"error": "Este pedido ya generó una venta anteriormente"}), 400

            from app.Models.models import EstadoVenta
            estado_completada = EstadoVenta.query.filter_by(nombre='completada').first()
            if not estado_completada:
                return jsonify({"error": "Estado 'completada' no encontrado en EstadoVenta"}), 500

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
                estado_id=estado_completada.id
            )
            db.session.add(venta)
            db.session.flush()

            for detalle_pedido in pedido.items:
                detalle_venta = DetalleVenta(
                    venta_id=venta.id,
                    producto_id=detalle_pedido.producto_id,
                    servicio_id=detalle_pedido.servicio_id,
                    cantidad=detalle_pedido.cantidad,
                    precio_unitario=detalle_pedido.precio_unitario,
                    subtotal=detalle_pedido.subtotal,
                    descuento=0
                )
                db.session.add(detalle_venta)

            for abono in pedido.abonos:
                abono.pedido_id = None
                abono.venta_id = venta.id

        pedido.estado_id = nuevo_estado_id
        if 'transferencia_comprobante' in data:
            pedido.transferencia_comprobante = data['transferencia_comprobante']
        if 'direccion_entrega' in data:
            pedido.direccion_entrega = data['direccion_entrega'].strip()
        if 'departamento_entrega' in data:
            pedido.departamento_entrega = data['departamento_entrega'].strip()
        if 'municipio_entrega' in data:
            pedido.municipio_entrega = data['municipio_entrega'].strip()
        if 'barrio_entrega' in data:
            pedido.barrio_entrega = data['barrio_entrega'].strip()
        if 'codigo_postal_entrega' in data:
            pedido.codigo_postal_entrega = data['codigo_postal_entrega'].strip()
        if 'metodo_pago' in data:
            if data['metodo_pago'] not in ['efectivo', 'transferencia', 'tarjeta']:
                return jsonify({"error": "Método de pago inválido"}), 400
            pedido.metodo_pago = data['metodo_pago']
        if 'metodo_entrega' in data:
            if data['metodo_entrega'] not in ['tienda', 'domicilio']:
                return jsonify({"error": "Método de entrega inválido"}), 400
            pedido.metodo_entrega = data['metodo_entrega']
        if 'total' in data:
            return jsonify({"error": "No se puede modificar el total directamente. Se calcula automáticamente"}), 400

        db.session.commit()
        return jsonify({"message": "Pedido actualizado", "pedido": pedido.to_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar pedido: {str(e)}"}), 500


@main_bp.route('/pedidos/<int:id>', methods=['DELETE'])
@permiso_requerido("eliminar_pedidos")
def delete_pedido(id):
    try:
        pedido = Pedido.query.get(id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404

        venta_asociada = Venta.query.filter_by(pedido_id=id).first()
        if venta_asociada:
            return jsonify({"error": "No se puede eliminar un pedido que ya generó una venta"}), 400

        if pedido.estado.nombre in ['pagado', 'anulado']:
            return jsonify({"error": "No se puede eliminar un pedido pagado o anulado"}), 400

        for detalle in pedido.items:
            if detalle.producto_id:
                producto = Producto.query.get(detalle.producto_id)
                if producto:
                    producto.stock += detalle.cantidad

        Abono.query.filter_by(pedido_id=id).delete()
        DetallePedido.query.filter_by(pedido_id=id).delete()
        db.session.delete(pedido)
        db.session.commit()
        return jsonify({"message": "Pedido eliminado correctamente y stock restaurado"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar pedido: {str(e)}"}), 500


@main_bp.route('/pedidos/cliente/<int:cliente_id>', methods=['GET'])
@permiso_requerido("ver_pedidos")
def get_pedidos_cliente(cliente_id):
    try:
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404
        pedidos = Pedido.query.filter_by(cliente_id=cliente_id).order_by(Pedido.fecha.desc()).all()
        return jsonify([pedido.to_dict() for pedido in pedidos])
    except Exception as e:
        return jsonify({"error": f"Error al obtener pedidos del cliente: {str(e)}"}), 500


@main_bp.route('/pedidos/<int:pedido_id>/detalles', methods=['GET'])
@permiso_requerido("ver_pedidos")
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
@permiso_requerido("ver_pedidos")
def get_abonos_pedido(id):
    try:
        pedido = Pedido.query.get(id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404
        abonos = [abono.to_dict() for abono in pedido.abonos]
        return jsonify(abonos)
    except Exception as e:
        return jsonify({"error": f"Error al obtener abonos: {str(e)}"}), 500


@main_bp.route('/pedidos/<int:id>/abonos', methods=['POST'])
@permiso_requerido("editar_pedidos")
def add_abono_pedido(id):
    try:
        pedido = Pedido.query.get(id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404
        if pedido.estado.nombre in ['pagado', 'anulado']:
            return jsonify({"error": f"No se pueden registrar abonos en un pedido {pedido.estado.nombre}"}), 400

        data = request.get_json()
        monto = data.get('monto_abonado')
        if not monto or float(monto) <= 0:
            return jsonify({"error": "El monto del abono debe ser mayor a 0"}), 400
        monto = float(monto)

        nuevo_acumulado = pedido.abono_acumulado + monto
        if nuevo_acumulado > pedido.total:
            return jsonify({"error": f"El abono excede el total del pedido. Máximo permitido: {pedido.total - pedido.abono_acumulado}"}), 400

        abono = Abono(
            pedido_id=pedido.id,
            monto=monto,
            observacion=data.get('observacion', '')
        )
        db.session.add(abono)
        pedido.abono_acumulado = nuevo_acumulado
        db.session.commit()

        return jsonify({
            "message": "Abono registrado",
            "abono_acumulado": pedido.abono_acumulado,
            "saldo_pendiente": pedido.total - pedido.abono_acumulado
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al registrar abono: {str(e)}"}), 500


# ============================================================
# MÓDULO: DETALLES DE PEDIDO (CRUD independiente)
# ============================================================

@main_bp.route('/detalle-pedido', methods=['GET'])
@permiso_requerido("ver_pedidos")
def get_detalles_pedido():
    """
    Listar detalles de pedido con paginación y filtros.
    Query params: page, per_page, pedido_id
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        pedido_id = request.args.get('pedido_id', type=int)

        if pedido_id:
            query = DetallePedido.query.filter_by(pedido_id=pedido_id)
        else:
            query = DetallePedido.query

        query = query.order_by(DetallePedido.id.desc())

        if 'page' not in request.args and 'per_page' not in request.args and not pedido_id:
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
        return jsonify({"error": f"Error al obtener detalles de pedido: {str(e)}"}), 500


@main_bp.route('/detalle-pedido', methods=['POST'])
@permiso_requerido("editar_pedidos")
def create_detalle_pedido():
    try:
        data = request.get_json()
        required_fields = ['pedido_id', 'cantidad', 'precio_unitario']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo '{field}' es requerido"}), 400

        producto_id = data.get('producto_id')
        servicio_id = data.get('servicio_id')
        if not producto_id and not servicio_id:
            return jsonify({"error": "Debe proporcionar 'producto_id' o 'servicio_id'"}), 400
        if producto_id and servicio_id:
            return jsonify({"error": "Solo uno de los dos: producto o servicio"}), 400

        pedido = Pedido.query.get(data['pedido_id'])
        if not pedido:
            return jsonify({"error": "El pedido especificado no existe"}), 404
        if pedido.estado.nombre != 'pendiente':
            return jsonify({"error": f"No se puede modificar un pedido en estado '{pedido.estado.nombre}'. Solo se pueden modificar pedidos pendientes"}), 400

        cantidad = int(data['cantidad'])
        if cantidad <= 0:
            return jsonify({"error": "La cantidad debe ser mayor a 0"}), 400

        precio = float(data['precio_unitario'])
        if precio <= 0:
            return jsonify({"error": "El precio unitario debe ser mayor a 0"}), 400

        if producto_id:
            producto = Producto.query.get(producto_id)
            if not producto or not producto.estado:
                return jsonify({"error": "Producto no existe o está inactivo"}), 404
            if producto.stock < cantidad:
                return jsonify({"error": f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock}"}), 400
            producto.stock -= cantidad
            detalle = DetallePedido(
                pedido_id=data['pedido_id'],
                producto_id=producto_id,
                cantidad=cantidad,
                precio_unitario=precio,
                subtotal=cantidad * precio
            )
        else:
            servicio = Servicio.query.get(servicio_id)
            if not servicio or not servicio.estado:
                return jsonify({"error": "Servicio no existe o está inactivo"}), 404
            detalle = DetallePedido(
                pedido_id=data['pedido_id'],
                servicio_id=servicio_id,
                cantidad=cantidad,
                precio_unitario=precio,
                subtotal=cantidad * precio
            )

        db.session.add(detalle)
        pedido.total += detalle.subtotal
        db.session.commit()

        return jsonify({"message": "Detalle de pedido creado", "detalle": detalle.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear detalle de pedido: {str(e)}"}), 500


@main_bp.route('/detalle-pedido/<int:id>', methods=['PUT'])
@permiso_requerido("editar_pedidos")
def update_detalle_pedido(id):
    try:
        detalle = DetallePedido.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de pedido no encontrado"}), 404

        pedido = Pedido.query.get(detalle.pedido_id)
        if not pedido:
            return jsonify({"error": "El pedido asociado no existe"}), 404
        if pedido.estado.nombre != 'pendiente':
            return jsonify({"error": f"No se puede modificar un pedido en estado '{pedido.estado.nombre}'. Solo se pueden modificar pedidos pendientes"}), 400

        data = request.get_json()
        if 'producto_id' in data or 'servicio_id' in data:
            return jsonify({"error": "No se puede cambiar el producto o servicio de un detalle existente. Elimine y cree uno nuevo."}), 400

        old_subtotal = detalle.subtotal
        old_cantidad = detalle.cantidad

        if 'cantidad' in data:
            nueva_cantidad = int(data['cantidad'])
            if nueva_cantidad <= 0:
                return jsonify({"error": "La cantidad debe ser mayor a 0"}), 400

            if detalle.producto_id:
                producto = Producto.query.get(detalle.producto_id)
                if producto:
                    producto.stock += old_cantidad
                    if producto.stock < nueva_cantidad:
                        return jsonify({"error": f"Stock insuficiente para '{producto.nombre}'"}), 400
                    producto.stock -= nueva_cantidad
            detalle.cantidad = nueva_cantidad

        if 'precio_unitario' in data:
            nuevo_precio = float(data['precio_unitario'])
            if nuevo_precio <= 0:
                return jsonify({"error": "El precio unitario debe ser mayor a 0"}), 400
            detalle.precio_unitario = nuevo_precio

        detalle.subtotal = detalle.cantidad * detalle.precio_unitario
        pedido.total = pedido.total - old_subtotal + detalle.subtotal
        db.session.commit()

        return jsonify({"message": "Detalle de pedido actualizado", "detalle": detalle.to_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar detalle de pedido: {str(e)}"}), 500


@main_bp.route('/detalle-pedido/<int:id>', methods=['DELETE'])
@permiso_requerido("editar_pedidos")
def delete_detalle_pedido(id):
    try:
        detalle = DetallePedido.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de pedido no encontrado"}), 404

        pedido = Pedido.query.get(detalle.pedido_id)
        if not pedido:
            return jsonify({"error": "El pedido asociado no existe"}), 404
        if pedido.estado.nombre != 'pendiente':
            return jsonify({"error": f"No se puede modificar un pedido en estado '{pedido.estado.nombre}'. Solo se pueden modificar pedidos pendientes"}), 400

        if detalle.producto_id:
            producto = Producto.query.get(detalle.producto_id)
            if producto:
                producto.stock += detalle.cantidad

        pedido.total -= detalle.subtotal
        db.session.delete(detalle)
        db.session.commit()

        return jsonify({"message": "Detalle de pedido eliminado correctamente y stock restaurado"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar detalle de pedido: {str(e)}"}), 500


# ============================================================
# MÓDULO: ESTADOS DE PEDIDO (opcional, con gestionar_configuracion)
# ============================================================

@main_bp.route('/estado-pedido', methods=['GET'])
@permiso_requerido("gestionar_configuracion")
def get_estados_pedido():
    """
    Listar estados de pedido con paginación y búsqueda.
    Query params: page, per_page, search
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', MAX_PER_PAGE, type=int), MAX_PER_PAGE)
        search = request.args.get('search', '', type=str).strip()

        query = EstadoPedido.query
        if search:
            query = query.filter(EstadoPedido.nombre.ilike(f"%{search}%"))
        query = query.order_by(EstadoPedido.nombre.asc())

        if 'page' not in request.args and 'per_page' not in request.args and not search:
            estados = query.all()
            return jsonify([estado.to_dict() for estado in estados])

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'data': [estado.to_dict() for estado in pagination.items],
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
        return jsonify({"error": "Error al obtener estados de pedido"}), 500


@main_bp.route('/estado-pedido', methods=['POST'])
@permiso_requerido("gestionar_configuracion")
def create_estado_pedido():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400
        estado = EstadoPedido(nombre=data['nombre'])
        db.session.add(estado)
        db.session.commit()
        return jsonify({"message": "Estado de pedido creado", "estado": estado.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear estado de pedido"}), 500


@main_bp.route('/estado-pedido/<int:id>', methods=['PUT'])
@permiso_requerido("gestionar_configuracion")
def update_estado_pedido(id):
    try:
        estado = EstadoPedido.query.get(id)
        if not estado:
            return jsonify({"error": "Estado de pedido no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data:
            estado.nombre = data['nombre']
        db.session.commit()
        return jsonify({"message": "Estado de pedido actualizado", "estado": estado.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar estado de pedido"}), 500


@main_bp.route('/estado-pedido/<int:id>', methods=['DELETE'])
@permiso_requerido("gestionar_configuracion")
def delete_estado_pedido(id):
    try:
        estado = EstadoPedido.query.get(id)
        if not estado:
            return jsonify({"error": "Estado de pedido no encontrado"}), 404
        if Pedido.query.filter_by(estado_id=id).first():
            return jsonify({"error": "No se puede eliminar un estado que está siendo usado por pedidos"}), 400
        db.session.delete(estado)
        db.session.commit()
        return jsonify({"message": "Estado de pedido eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar estado de pedido"}), 500