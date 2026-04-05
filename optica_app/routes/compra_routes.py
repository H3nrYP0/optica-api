from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Compra, DetalleCompra, Producto, Proveedor
from datetime import datetime

compra_bp = Blueprint('compras', __name__)

@compra_bp.route('', methods=['GET'])
def get_compras():
    try:
        # Usamos join para traer el nombre del proveedor de una vez
        compras = Compra.query.all()
        return jsonify([c.to_dict() for c in compras]), 200
    except Exception as e:
        return jsonify({"error": "Error al obtener compras"}), 500

@compra_bp.route('', methods=['POST'])
def create_compra():
    try:
        data = request.get_json()
        
        # 1. VALIDACIONES DE NEGOCIO REALES
        proveedor_id = data.get('proveedor_id')
        detalles_data = data.get('detalles', []) # Esperamos una lista de productos

        if not proveedor_id or not detalles_data:
            return jsonify({"error": "Una compra requiere un proveedor y al menos un producto"}), 400

        proveedor = db.session.get(Proveedor, proveedor_id)
        if not proveedor or not proveedor.estado:
            return jsonify({"error": "El proveedor no existe o está inactivo"}), 400

        # 2. INICIO DE TRANSACCIÓN
        nueva_compra = Compra(
            proveedor_id=proveedor_id,
            total=0, # Lo calcularemos sumando los subtotales
            estado_compra=True,
            fecha=datetime.utcnow()
        )
        db.session.add(nueva_compra)
        db.session.flush() # Para obtener el ID de la compra sin cerrar la transacción

        total_calculado = 0

        # 3. PROCESAR CADA PRODUCTO
        for item in detalles_data:
            prod_id = item.get('producto_id')
            cantidad = int(item.get('cantidad', 0))
            precio_u = float(item.get('precio_unidad', 0))

            if cantidad <= 0 or precio_u <= 0:
                db.session.rollback()
                return jsonify({"error": f"Cantidad y precio deben ser mayores a 0 para el producto ID {prod_id}"}), 400

            producto = db.session.get(Producto, prod_id)
            if not producto:
                db.session.rollback()
                return jsonify({"error": f"El producto con ID {prod_id} no existe"}), 404

            subtotal = cantidad * precio_u
            total_calculado += subtotal

            # Crear el detalle
            detalle = DetalleCompra(
                compra_id=nueva_compra.id,
                producto_id=prod_id,
                precio_unidad=precio_u,
                cantidad=cantidad,
                subtotal=subtotal
            )
            db.session.add(detalle)

            # --- Aumentar el stock automáticamente ---
            producto.stock += cantidad
            # Actualizar precio de compra del producto si el nuevo es diferente (opcional)
            producto.precio_compra = precio_u 

        # 4. FINALIZAR COMPRA
        nueva_compra.total = total_calculado
        db.session.commit()

        return jsonify(nueva_compra.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error crítico: {str(e)}"}), 500

@compra_bp.route('/<int:id>', methods=['DELETE'])
def delete_compra(id):
    """
    REGLA DE NEGOCIO: Eliminar una compra es delicado porque ya alteró el stock.
    Aquí restaremos el stock que se había sumado.
    """
    try:
        compra = db.session.get(Compra, id)
        if not compra:
            return jsonify({"error": "Compra no encontrada"}), 404

        # Revertir el stock de cada producto antes de borrar
        for detalle in compra.detalles:
            producto = db.session.get(Producto, detalle.producto_id)
            if producto:
                if producto.stock < detalle.cantidad:
                    return jsonify({"error": f"No se puede eliminar la compra: El producto {producto.nombre} ya se vendió y no hay suficiente stock para revertir."}), 400
                producto.stock -= detalle.cantidad

        db.session.delete(compra)
        db.session.commit()
        return jsonify({"message": "Compra eliminada y stock revertido"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500