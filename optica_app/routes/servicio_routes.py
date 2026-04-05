from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Servicio

servicio_bp = Blueprint('servicios', __name__)

@servicio_bp.route('', methods=['GET'])
def get_servicios():
    try:
        # Devuelve todos los servicios para que el Front los liste
        return jsonify([s.to_dict() for s in Servicio.query.all()]), 200
    except Exception:
        return jsonify({"error": "Error al obtener servicios"}), 500

@servicio_bp.route('', methods=['POST'])
def create_servicio():
    try:
        data = request.get_json()
        nombre = " ".join(data.get('nombre', '').split()).strip()
        precio = float(data.get('precio', 0))
        duracion = int(data.get('duracion', 30)) # Duración por defecto 30 min

        # 1. VALIDACIÓN: Datos básicos
        if not nombre or precio <= 0:
            return jsonify({"error": "Nombre obligatorio y precio debe ser mayor a 0"}), 400

        # 2. VALIDACIÓN: Unicidad
        if Servicio.query.filter(Servicio.nombre.ilike(nombre)).first():
            return jsonify({"error": f"El servicio '{nombre}' ya existe"}), 400

        nuevo_servicio = Servicio(
            nombre=nombre,
            descripcion=data.get('descripcion', '').strip(),
            precio=precio,
            duracion=duracion,
            estado=data.get('estado', True)
        )
        
        db.session.add(nuevo_servicio)
        db.session.commit()
        
        # Respuesta Limpia (Objeto directo)
        return jsonify(nuevo_servicio.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@servicio_bp.route('/<int:id>', methods=['PUT'])
def update_servicio(id):
    try:
        servicio = db.session.get(Servicio, id)
        if not servicio:
            return jsonify({"error": "Servicio no encontrado"}), 404
            
        data = request.get_json()
        
        # Si se intenta cambiar el nombre, validar que no choque con otro
        if 'nombre' in data:
            nombre = data['nombre'].strip()
            existente = Servicio.query.filter(Servicio.nombre.ilike(nombre), Servicio.id != id).first()
            if existente:
                return jsonify({"error": "Ya existe otro servicio con ese nombre"}), 400
            servicio.nombre = nombre

        # Actualización de otros campos con limpieza
        if 'precio' in data:
            servicio.precio = float(data['precio'])
        if 'duracion' in data:
            servicio.duracion = int(data['duracion'])
        if 'descripcion' in data:
            servicio.descripcion = data['descripcion'].strip()
        if 'estado' in data:
            servicio.estado = bool(data['estado'])

        db.session.commit()
        return jsonify(servicio.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@servicio_bp.route('/<int:id>', methods=['DELETE'])
def delete_servicio(id):
    try:
        servicio = db.session.get(Servicio, id)
        if not servicio:
            return jsonify({"error": "Servicio no encontrado"}), 404

        # REGLA DE NEGOCIO: No borrar si hay citas programadas con este servicio
        if len(servicio.citas) > 0:
            return jsonify({
                "error": "No se puede eliminar. Este servicio tiene citas registradas. Desactívelo en su lugar."
            }), 400

        db.session.delete(servicio)
        db.session.commit()
        return jsonify({"message": "Servicio eliminado correctamente"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error de integridad al eliminar el servicio"}), 500