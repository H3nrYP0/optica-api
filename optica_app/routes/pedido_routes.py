from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models.pedido import Pedido, DetallePedido
from optica_app.models.venta import Venta, DetalleVenta, Abono
from optica_app.models.producto import Producto
from datetime import datetime

pedido_bp = Blueprint('pedidos', __name__)

@pedido_bp.route('', methods=['GET'])
def get_pedidos():
    try:
        return jsonify([p.to_dict() for p in Pedido.query.all()])
    except Exception:
        return jsonify({"error": "Error al obtener pedidos"}), 500

@pedido_bp.route('/<int:id>', methods=['GET'])
def get_pedido(id):
    pedido = Pedido.query.get(id)
    if not pedido:
        return jsonify({"error": "Pedido no encontrado"}), 404
    return jsonify(pedido.to_dict())

@pedido_bp.route('', methods=['POST'])
def create_pedido():
    data = request.get_json()
    try:
        # 1. Validaciones de integridad inicial
        required = ['cliente_id', 'metodo_pago', 'items']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({"error": f"El campo '{field}' es requerido"}), 400

        # 2. Instancia del Pedido (Cero Nulls)
        pedido = Pedido(
            cliente_id=data['cliente_id'],
            metodo_pago=data['metodo_pago'],
            metodo_entrega=data.get('metodo_entrega'),
            direccion_entrega=data.get('direccion_entrega'),
            estado=data.get('estado', 'pendiente'),
            transferencia_comprobante=data.get('transferencia_comprobante'),
            total=0
        )

        db.session.add(pedido)
        db.session.flush()

        total_calculado = 0
        
        # 3. Procesamiento Atómico de Items y Stock
        for item in data['items']:
            producto = Producto.query.get(item['producto_id'])
            if not producto:
                db.session.rollback()
                return jsonify({"error": f"Producto ID {item['producto_id']} no existe"}), 404
            
            cantidad = int(item['cantidad'])
            
            # VALIDACIÓN DE STOCK (Blindaje Preventivo)
            if producto.stock < cantidad:
                db.session.rollback()
                return jsonify({"error": f"Stock insuficiente para {producto.nombre}"}), 400

            # Descontar stock inmediatamente para reservar el producto
            producto.stock -= cantidad
            
            precio = float(producto.precio) # Usar precio del servidor por seguridad
            subtotal = cantidad * precio
            total_calculado += subtotal

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
        return jsonify(pedido.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear pedido: {str(e)}"}), 500

@pedido_bp.route('/<int:id>', methods=['PUT'])
def update_pedido(id):
    try:
        pedido = Pedido.query.get(id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404

        data = request.get_json()
        nuevo_estado = data.get('estado', pedido.estado)

        # TRANSICIÓN A VENTA (Blindaje de Lógica de Negocio)
        if nuevo_estado == 'entregado' and pedido.estado != 'entregado':
            # Verificar si ya existe una venta asociada para evitar duplicidad
            if Venta.query.filter_by(pedido_id=pedido.id).first():
                return jsonify({"error": "Este pedido ya tiene una venta procesada"}), 400

            # Crear Venta Automática
            nueva_venta = Venta(
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
            
            db.session.add(nueva_venta)
            db.session.flush()

            # Migrar Detalles a Venta
            for dp in pedido.items:
                dv = DetalleVenta(
                    venta_id=nueva_venta.id,
                    producto_id=dp.producto_id,
                    cantidad=dp.cantidad,
                    precio_unitario=dp.precio_unitario,
                    subtotal=dp.subtotal
                )
                db.session.add(dv)

            # Registrar Abono Inicial si existe pago en el pedido
            monto_pago = data.get('monto_abono', 0)
            if monto_pago > 0:
                abono = Abono(
                    venta_id=nueva_venta.id,
                    monto_abonado=monto_pago,
                    fecha=datetime.utcnow()
                )
                db.session.add(abono)

        # Actualización de campos permitidos
        if 'estado' in data: pedido.estado = nuevo_estado
        if 'direccion_entrega' in data: pedido.direccion_entrega = data['direccion_entrega']
        if 'metodo_pago' in data: pedido.metodo_pago = data['metodo_pago']

        db.session.commit()
        return jsonify(pedido.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar pedido: {str(e)}"}), 500

@pedido_bp.route('/<int:id>', methods=['DELETE'])
def delete_pedido(id):
    try:
        pedido = Pedido.query.get(id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404
        
        # Integridad Referencial: No borrar si ya es una venta
        if Venta.query.filter_by(pedido_id=id).first():
            return jsonify({"error": "No se puede eliminar un pedido que ya generó una factura/venta"}), 400

        # Devolución de Stock antes de eliminar (Rollback manual de inventario)
        for dp in pedido.items:
            producto = Producto.query.get(dp.producto_id)
            if producto:
                producto.stock += dp.cantidad

        db.session.delete(pedido)
        db.session.commit()
        return jsonify({"message": "Pedido eliminado y stock restaurado"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500