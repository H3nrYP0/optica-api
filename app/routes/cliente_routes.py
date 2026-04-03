from flask import Blueprint, jsonify, request
from app.database import db
from app.models import Cliente, HistorialFormula, Usuario
from datetime import datetime

cliente_bp = Blueprint('clientes', __name__)

@cliente_bp.route('', methods=['GET'])
def get_clientes():
    try:
        return jsonify([c.to_dict() for c in Cliente.query.all()])
    except Exception as e:
        return jsonify({"error": "Error al obtener clientes"}), 500

@cliente_bp.route('', methods=['POST'])
def create_cliente():
    try:
        data = request.get_json()
        required = ['nombre', 'apellido', 'numero_documento', 'fecha_nacimiento']
        for field in required:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        if Cliente.query.filter_by(numero_documento=data['numero_documento']).first():
            return jsonify({"success": False, "error": "Ya existe un cliente con este número de documento"}), 400
        cliente = Cliente(
            nombre=data['nombre'],
            apellido=data['apellido'],
            tipo_documento=data.get('tipo_documento'),
            numero_documento=data['numero_documento'],
            fecha_nacimiento=datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date(),
            genero=data.get('genero'),
            telefono=data.get('telefono'),
            correo=data.get('correo'),
            municipio=data.get('municipio'),
            direccion=data.get('direccion'),
            ocupacion=data.get('ocupacion'),
            telefono_emergencia=data.get('telefono_emergencia'),
            estado=data.get('estado', True)
        )
        db.session.add(cliente)
        db.session.commit()
        return jsonify({"success": True, "message": "Cliente creado exitosamente", "cliente": cliente.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Error al crear cliente: {str(e)}"}), 500

@cliente_bp.route('/<int:id>', methods=['PUT'])
def update_cliente(id):
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data: cliente.nombre = data['nombre']
        if 'apellido' in data: cliente.apellido = data['apellido']
        if 'tipo_documento' in data: cliente.tipo_documento = data['tipo_documento']
        if 'numero_documento' in data: cliente.numero_documento = data['numero_documento']
        if 'fecha_nacimiento' in data: cliente.fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
        if 'genero' in data: cliente.genero = data['genero']
        if 'telefono' in data: cliente.telefono = data['telefono']
        if 'correo' in data: cliente.correo = data['correo']
        if 'municipio' in data: cliente.municipio = data['municipio']
        if 'direccion' in data: cliente.direccion = data['direccion']
        if 'ocupacion' in data: cliente.ocupacion = data['ocupacion']
        if 'telefono_emergencia' in data: cliente.telefono_emergencia = data['telefono_emergencia']
        db.session.commit()
        return jsonify({"success": True, "message": "Cliente actualizado exitosamente", "cliente": cliente.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Error al actualizar cliente: {str(e)}"}), 500

@cliente_bp.route('/<int:id>', methods=['DELETE'])
def delete_cliente(id):
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404
        db.session.delete(cliente)
        db.session.commit()
        return jsonify({"message": "Cliente eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar cliente"}), 500

@cliente_bp.route('/usuario/<int:usuario_id>', methods=['GET'])
def get_cliente_by_usuario(usuario_id):
    try:
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
        if not usuario.cliente_id:
            return jsonify({"success": False, "error": "Este usuario no tiene cliente asociado"}), 404
        cliente = Cliente.query.get(usuario.cliente_id)
        if not cliente:
            return jsonify({"success": False, "error": "Cliente no encontrado"}), 404
        return jsonify({"success": True, "cliente": cliente.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al obtener cliente: {str(e)}"}), 500

@cliente_bp.route('/<int:cliente_id>/historial', methods=['GET'])
def get_historial_cliente(cliente_id):
    try:
        historiales = HistorialFormula.query.filter_by(cliente_id=cliente_id).all()
        return jsonify([h.to_dict() for h in historiales])
    except Exception as e:
        return jsonify({"error": "Error al obtener historial del cliente"}), 500