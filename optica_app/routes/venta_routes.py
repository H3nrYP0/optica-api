from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Venta, DetalleVenta, Producto, Cliente, Empleado
from datetime import datetime

venta_bp = Blueprint('ventas', __name__)

@venta_bp.route('', methods=['GET'])
def get_ventas():
    try:
        ventas = Venta.query.all()
        return jsonify([v.to_dict() for v in ventas]), 200
    except Exception:
        return jsonify({"error": "Error al obtener historial de ventas"}), 500

@venta_bp.route('', methods=['POST'])
def create_venta():
    try:
        data = request.get_json()
        
        # 1. VALIDACIONES INICIALES
        cliente_id = data.get('cliente_id')
        empleado_id = data.get('empleado_id') # El vendedor
        detalles_data = data.get('detalles', [])

        if not all([cliente_id, empleado_id, detalles_data]):
            return jsonify({"error": "Faltan datos: Cliente, Vendedor o Productos"}), 400

        # 2. INICIO DE TRANSACCIÓN
        nueva_venta = Venta(
            cliente_id=cliente_id,
            empleado_id=empleado_id,
            total=0, # Se calculará dinámicamente
            fecha=datetime.utcnow(),
            metodo_pago=data.get('metodo_pago', 'Efectivo')
        )
        db.session.add(nueva_venta)
        db.session.flush() # Para obtener el ID de venta

        total_venta = 0

        # 3. PROCESAR PRODUCTOS Y VALIDAR STOCK
        for item in detalles_data:
            prod_id = item.get('producto_id')
            cantidad = int(item.get('cantidad', 0))
            
            if cantidad <= 0:
                db.session.rollback()
                return jsonify({"error": "La cantidad debe ser mayor a 0"}), 400

            producto = db.session.get(Producto, prod_id)
            if not producto:
                db.session.rollback()
                return jsonify({"error": f"Producto ID {prod_id} no encontrado"}), 404

            # --- REGLA DE ORO: Validar Stock ---
            if producto.stock < cantidad:
                db.session.rollback()
                return jsonify({
                    "error": f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock}"
                }), 400

            precio_venta = float(item.get('precio_unitario', producto.precio_venta))
            subtotal = cantidad * precio_venta
            total_venta += subtotal

            # Crear detalle de venta
            detalle = DetalleVenta(
                venta_id=nueva_venta.id,
                producto_id=prod_id,
                cantidad=cantidad,
                precio_unitario=precio_venta,
                subtotal=subtotal
            )
            db.session.add(detalle)

            # --- Restar Stock automáticamente ---
            producto.stock -= cantidad

        # 4. FINALIZAR
        nueva_venta.total = total_venta
        db.session.commit()

        return jsonify(nueva_venta.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error crítico en venta: {str(e)}"}), 500

@venta_bp.route('/<int:id>', methods=['DELETE'])
def cancel_venta(id):
    """
    Anular una venta implica devolver los productos al inventario.
    """
    try:
        venta = db.session.get(Venta, id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404

        # Devolver stock de cada producto
        for detalle in venta.detalles:
            producto = db.session.get(Producto, detalle.producto_id)
            if producto:
                producto.stock += detalle.cantidad

        db.session.delete(venta)
        db.session.commit()
        return jsonify({"message": "Venta anulada y stock devuelto al inventario"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500