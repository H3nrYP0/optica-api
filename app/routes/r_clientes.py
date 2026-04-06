from flask import jsonify, request
from app.database import db
from app.Models.models import Cliente, HistorialFormula
from datetime import datetime
from app.routes import main_bp

@main_bp.route('/clientes', methods=['GET'])
def get_clientes():
    try:
        clientes = Cliente.query.all()
        return jsonify([cliente.to_dict() for cliente in clientes])
    except Exception as e:
        return jsonify({"error": "Error al obtener clientes"}), 500

@main_bp.route('/clientes', methods=['POST'])
def create_cliente():
    try:
        data = request.get_json()
        required_fields = ['nombre', 'apellido', 'numero_documento', 'fecha_nacimiento']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        cliente_existente = Cliente.query.filter_by(numero_documento=data['numero_documento']).first()
        if cliente_existente:
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

@main_bp.route('/clientes/<int:id>', methods=['PUT'])
def update_cliente(id):
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data:
            cliente.nombre = data['nombre']
        if 'apellido' in data:
            cliente.apellido = data['apellido']
        if 'tipo_documento' in data:
            cliente.tipo_documento = data['tipo_documento']
        if 'numero_documento' in data:
            cliente.numero_documento = data['numero_documento']
        if 'fecha_nacimiento' in data:
            cliente.fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
        if 'genero' in data:
            cliente.genero = data['genero']
        if 'telefono' in data:
            cliente.telefono = data['telefono']
        if 'correo' in data:
            cliente.correo = data['correo']
        if 'municipio' in data:
            cliente.municipio = data['municipio']
        if 'direccion' in data:
            cliente.direccion = data['direccion']
        if 'ocupacion' in data:
            cliente.ocupacion = data['ocupacion']
        if 'telefono_emergencia' in data:
            cliente.telefono_emergencia = data['telefono_emergencia']
        db.session.commit()
        return jsonify({"success": True, "message": "Cliente actualizado exitosamente", "cliente": cliente.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Error al actualizar cliente: {str(e)}"}), 500

@main_bp.route('/clientes/<int:id>', methods=['DELETE'])
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

@main_bp.route('/historial-formula', methods=['GET'])
def get_historiales_formula():
    try:
        historiales = HistorialFormula.query.all()
        return jsonify([historial.to_dict() for historial in historiales])
    except Exception as e:
        return jsonify({"error": "Error al obtener historial de fórmulas"}), 500

@main_bp.route('/historial-formula', methods=['POST'])
def create_historial_formula():
    try:
        data = request.get_json()
        if not data.get('cliente_id'):
            return jsonify({"error": "El cliente_id es requerido"}), 400
        historial = HistorialFormula(
            cliente_id=data['cliente_id'],
            descripcion=data.get('descripcion', ''),
            od_esfera=data.get('od_esfera'),
            od_cilindro=data.get('od_cilindro'),
            od_eje=data.get('od_eje'),
            oi_esfera=data.get('oi_esfera'),
            oi_cilindro=data.get('oi_cilindro'),
            oi_eje=data.get('oi_eje')
        )
        db.session.add(historial)
        db.session.commit()
        return jsonify({"message": "Historial de fórmula creado", "historial": historial.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear historial de fórmula"}), 500

@main_bp.route('/historial-formula/<int:id>', methods=['PUT'])
def update_historial_formula(id):
    try:
        historial = HistorialFormula.query.get(id)
        if not historial:
            return jsonify({"error": "Historial de fórmula no encontrado"}), 404
        data = request.get_json()
        if 'cliente_id' in data:
            historial.cliente_id = data['cliente_id']
        if 'descripcion' in data:
            historial.descripcion = data['descripcion']
        if 'od_esfera' in data:
            historial.od_esfera = data['od_esfera']
        if 'od_cilindro' in data:
            historial.od_cilindro = data['od_cilindro']
        if 'od_eje' in data:
            historial.od_eje = data['od_eje']
        if 'oi_esfera' in data:
            historial.oi_esfera = data['oi_esfera']
        if 'oi_cilindro' in data:
            historial.oi_cilindro = data['oi_cilindro']
        if 'oi_eje' in data:
            historial.oi_eje = data['oi_eje']
        db.session.commit()
        return jsonify({"message": "Historial de fórmula actualizado", "historial": historial.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar historial de fórmula"}), 500

@main_bp.route('/historial-formula/<int:id>', methods=['DELETE'])
def delete_historial_formula(id):
    try:
        historial = HistorialFormula.query.get(id)
        if not historial:
            return jsonify({"error": "Historial de fórmula no encontrado"}), 404
        db.session.delete(historial)
        db.session.commit()
        return jsonify({"message": "Historial de fórmula eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar historial de fórmula"}), 500

@main_bp.route('/clientes/<int:cliente_id>/historial', methods=['GET'])
def get_historial_cliente(cliente_id):
    try:
        historiales = HistorialFormula.query.filter_by(cliente_id=cliente_id).all()
        return jsonify([historial.to_dict() for historial in historiales])
    except Exception as e:
        return jsonify({"error": "Error al obtener historial del cliente"}), 500