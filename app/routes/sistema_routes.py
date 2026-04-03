from flask import Blueprint, jsonify, request
from app.database import db
from app.models import EstadoCita, EstadoVenta, Permiso, PermisoPorRol, DetalleCompra, DetalleVenta, Abono

sistema_bp = Blueprint('sistema', __name__)

# ── Estado Cita ──
@sistema_bp.route('/estado-cita', methods=['GET'])
def get_estados_cita():
    try:
        return jsonify([e.to_dict() for e in EstadoCita.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener estados de cita"}), 500

@sistema_bp.route('/estado-cita', methods=['POST'])
def create_estado_cita():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400
        estado = EstadoCita(nombre=data['nombre'])
        db.session.add(estado)
        db.session.commit()
        return jsonify({"message": "Estado de cita creado", "estado": estado.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear estado de cita"}), 500

@sistema_bp.route('/estado-cita/<int:id>', methods=['PUT'])
def update_estado_cita(id):
    try:
        estado = EstadoCita.query.get(id)
        if not estado:
            return jsonify({"error": "Estado no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data: estado.nombre = data['nombre']
        db.session.commit()
        return jsonify({"message": "Estado actualizado", "estado": estado.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar estado"}), 500

@sistema_bp.route('/estado-cita/<int:id>', methods=['DELETE'])
def delete_estado_cita(id):
    try:
        estado = EstadoCita.query.get(id)
        if not estado:
            return jsonify({"error": "Estado no encontrado"}), 404
        db.session.delete(estado)
        db.session.commit()
        return jsonify({"message": "Estado eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar estado"}), 500

# ── Estado Venta ──
@sistema_bp.route('/estado-venta', methods=['GET'])
def get_estados_venta():
    try:
        return jsonify([e.to_dict() for e in EstadoVenta.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener estados de venta"}), 500

@sistema_bp.route('/estado-venta', methods=['POST'])
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

@sistema_bp.route('/estado-venta/<int:id>', methods=['PUT'])
def update_estado_venta(id):
    try:
        estado = EstadoVenta.query.get(id)
        if not estado:
            return jsonify({"error": "Estado no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data: estado.nombre = data['nombre']
        db.session.commit()
        return jsonify({"message": "Estado actualizado", "estado": estado.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar estado"}), 500

@sistema_bp.route('/estado-venta/<int:id>', methods=['DELETE'])
def delete_estado_venta(id):
    try:
        estado = EstadoVenta.query.get(id)
        if not estado:
            return jsonify({"error": "Estado no encontrado"}), 404
        db.session.delete(estado)
        db.session.commit()
        return jsonify({"message": "Estado eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar estado"}), 500

# ── Permisos ──
@sistema_bp.route('/permiso', methods=['GET'])
def get_permisos():
    try:
        return jsonify([p.to_dict() for p in Permiso.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener permisos"}), 500

@sistema_bp.route('/permiso', methods=['POST'])
def create_permiso():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400
        permiso = Permiso(nombre=data['nombre'])
        db.session.add(permiso)
        db.session.commit()
        return jsonify({"message": "Permiso creado", "permiso": permiso.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear permiso"}), 500

@sistema_bp.route('/permiso/<int:id>', methods=['PUT'])
def update_permiso(id):
    try:
        permiso = Permiso.query.get(id)
        if not permiso:
            return jsonify({"error": "Permiso no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data: permiso.nombre = data['nombre']
        db.session.commit()
        return jsonify({"message": "Permiso actualizado", "permiso": permiso.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar permiso"}), 500

@sistema_bp.route('/permiso/<int:id>', methods=['DELETE'])
def delete_permiso(id):
    try:
        permiso = Permiso.query.get(id)
        if not permiso:
            return jsonify({"error": "Permiso no encontrado"}), 404
        db.session.delete(permiso)
        db.session.commit()
        return jsonify({"message": "Permiso eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar permiso"}), 500

# ── Detalle Compra ──
@sistema_bp.route('/detalle-compra', methods=['GET'])
def get_detalles_compra():
    try:
        return jsonify([d.to_dict() for d in DetalleCompra.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener detalles de compra"}), 500

@sistema_bp.route('/detalle-compra', methods=['POST'])
def create_detalle_compra():
    try:
        data = request.get_json()
        required = ['compra_id', 'producto_id', 'cantidad', 'precio_unidad']
        for field in required:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        detalle = DetalleCompra(
            compra_id=data['compra_id'],
            producto_id=data['producto_id'],
            cantidad=data['cantidad'],
            precio_unidad=float(data['precio_unidad']),
            subtotal=float(data['cantidad']) * float(data['precio_unidad'])
        )
        db.session.add(detalle)
        db.session.commit()
        return jsonify({"message": "Detalle de compra creado", "detalle": detalle.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear detalle de compra"}), 500

@sistema_bp.route('/detalle-compra/<int:id>', methods=['PUT'])
def update_detalle_compra(id):
    try:
        detalle = DetalleCompra.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle no encontrado"}), 404
        data = request.get_json()
        if 'cantidad' in data: detalle.cantidad = data['cantidad']
        if 'precio_unidad' in data: detalle.precio_unidad = float(data['precio_unidad'])
        if 'cantidad' in data and 'precio_unidad' in data:
            detalle.subtotal = float(data['cantidad']) * float(data['precio_unidad'])
        db.session.commit()
        return jsonify({"message": "Detalle actualizado", "detalle": detalle.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar detalle"}), 500

@sistema_bp.route('/detalle-compra/<int:id>', methods=['DELETE'])
def delete_detalle_compra(id):
    try:
        detalle = DetalleCompra.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle no encontrado"}), 404
        db.session.delete(detalle)
        db.session.commit()
        return jsonify({"message": "Detalle eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar detalle"}), 500

# ── Abono individual ──
@sistema_bp.route('/abonos/<int:id>', methods=['DELETE'])
def delete_abono(id):
    try:
        abono = Abono.query.get(id)
        if not abono:
            return jsonify({"error": "Abono no encontrado"}), 404
        db.session.delete(abono)
        db.session.commit()
        return jsonify({"message": "Abono eliminado"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar abono: {str(e)}"}), 500