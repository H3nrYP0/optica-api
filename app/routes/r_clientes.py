from flask import jsonify, request
from app.database import db
from app.Models.models import Cliente, HistorialFormula, Usuario
from datetime import datetime
from app.routes import main_bp
import re

# Regex para validar email
EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
# Regex para validar teléfono (solo números, 7-15 dígitos)
PHONE_REGEX = re.compile(r'^\d{7,15}$')


# ============================================================
# MÓDULO: CLIENTES
# ============================================================

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
            if field not in data or not data[field]:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        
        # Validación: nombre y apellido no vacíos
        nombre = data['nombre'].strip()
        apellido = data['apellido'].strip()
        if not nombre:
            return jsonify({"error": "El nombre no puede estar vacío"}), 400
        if not apellido:
            return jsonify({"error": "El apellido no puede estar vacío"}), 400
        
        # Validación: documento único
        if Cliente.query.filter_by(numero_documento=data['numero_documento']).first():
            return jsonify({"success": False, "error": "Ya existe un cliente con este número de documento"}), 400
        
        # Validación: fecha de nacimiento (no puede ser futura)
        try:
            fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
            if fecha_nacimiento > datetime.now().date():
                return jsonify({"error": "La fecha de nacimiento no puede ser futura"}), 400
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
        
        # Validación: email (si se proporciona)
        correo = data.get('correo', '').strip()
        if correo and not EMAIL_REGEX.match(correo):
            return jsonify({"error": "Formato de correo electrónico inválido"}), 400
        
        # Validación: teléfono (si se proporciona)
        telefono = data.get('telefono', '').strip()
        if telefono and not PHONE_REGEX.match(telefono):
            return jsonify({"error": "El teléfono debe contener solo números (7-15 dígitos)"}), 400
        
        # Validación: teléfono emergencia (si se proporciona)
        telefono_emergencia = data.get('telefono_emergencia', '').strip()
        if telefono_emergencia and not PHONE_REGEX.match(telefono_emergencia):
            return jsonify({"error": "El teléfono de emergencia debe contener solo números (7-15 dígitos)"}), 400
        
        # Validación: género (si se proporciona)
        genero = data.get('genero', '').strip()
        if genero and genero not in ['Masculino', 'Femenino', 'Otro']:
            return jsonify({"error": "Género debe ser: Masculino, Femenino u Otro"}), 400
        
        cliente = Cliente(
            nombre=nombre,
            apellido=apellido,
            tipo_documento=data.get('tipo_documento', '').strip(),
            numero_documento=data['numero_documento'].strip(),
            fecha_nacimiento=fecha_nacimiento,
            genero=genero if genero else None,
            telefono=telefono if telefono else None,
            correo=correo if correo else None,
            municipio=data.get('municipio', '').strip(),
            direccion=data.get('direccion', '').strip(),
            ocupacion=data.get('ocupacion', '').strip(),
            telefono_emergencia=telefono_emergencia if telefono_emergencia else None,
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
        
        # Validación: nombre
        if 'nombre' in data:
            nombre = data['nombre'].strip()
            if not nombre:
                return jsonify({"error": "El nombre no puede estar vacío"}), 400
            cliente.nombre = nombre
            
        # Validación: apellido
        if 'apellido' in data:
            apellido = data['apellido'].strip()
            if not apellido:
                return jsonify({"error": "El apellido no puede estar vacío"}), 400
            cliente.apellido = apellido
            
        # Validación: documento único (si cambia)
        if 'numero_documento' in data:
            doc = data['numero_documento'].strip()
            existente = Cliente.query.filter_by(numero_documento=doc).first()
            if existente and existente.id != id:
                return jsonify({"error": "Ya existe otro cliente con este número de documento"}), 400
            cliente.numero_documento = doc
            
        # Validación: fecha de nacimiento
        if 'fecha_nacimiento' in data:
            try:
                fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
                if fecha_nacimiento > datetime.now().date():
                    return jsonify({"error": "La fecha de nacimiento no puede ser futura"}), 400
                cliente.fecha_nacimiento = fecha_nacimiento
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
                
        # Validación: email
        if 'correo' in data:
            correo = data['correo'].strip() if data['correo'] else None
            if correo and not EMAIL_REGEX.match(correo):
                return jsonify({"error": "Formato de correo electrónico inválido"}), 400
            cliente.correo = correo
            
        # Validación: teléfono
        if 'telefono' in data:
            telefono = data['telefono'].strip() if data['telefono'] else None
            if telefono and not PHONE_REGEX.match(telefono):
                return jsonify({"error": "El teléfono debe contener solo números (7-15 dígitos)"}), 400
            cliente.telefono = telefono
            
        # Validación: teléfono emergencia
        if 'telefono_emergencia' in data:
            telefono_emergencia = data['telefono_emergencia'].strip() if data['telefono_emergencia'] else None
            if telefono_emergencia and not PHONE_REGEX.match(telefono_emergencia):
                return jsonify({"error": "El teléfono de emergencia debe contener solo números (7-15 dígitos)"}), 400
            cliente.telefono_emergencia = telefono_emergencia
            
        # Validación: género
        if 'genero' in data:
            genero = data['genero'].strip() if data['genero'] else None
            if genero and genero not in ['Masculino', 'Femenino', 'Otro']:
                return jsonify({"error": "Género debe ser: Masculino, Femenino u Otro"}), 400
            cliente.genero = genero
            
        # Actualizar campos simples
        if 'tipo_documento' in data:
            cliente.tipo_documento = data['tipo_documento'].strip()
        if 'municipio' in data:
            cliente.municipio = data['municipio'].strip()
        if 'direccion' in data:
            cliente.direccion = data['direccion'].strip()
        if 'ocupacion' in data:
            cliente.ocupacion = data['ocupacion'].strip()
        if 'estado' in data:
            cliente.estado = data['estado']
            
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
        
        # Validación: No eliminar si tiene citas asociadas
        if cliente.citas and len(cliente.citas) > 0:
            return jsonify({"error": "No se puede eliminar un cliente que tiene citas asociadas"}), 400
        
        # Validación: No eliminar si tiene ventas asociadas
        if cliente.ventas and len(cliente.ventas) > 0:
            return jsonify({"error": "No se puede eliminar un cliente que tiene ventas asociadas"}), 400
        
        # Validación: No eliminar si tiene pedidos asociados
        if cliente.pedidos and len(cliente.pedidos) > 0:
            return jsonify({"error": "No se puede eliminar un cliente que tiene pedidos asociados"}), 400
        
        # Validación: No eliminar si tiene usuario asociado
        if cliente.usuario:
            return jsonify({"error": "No se puede eliminar un cliente que tiene un usuario asociado. Desactive el cliente en su lugar."}), 400
        
        db.session.delete(cliente)
        db.session.commit()
        return jsonify({"message": "Cliente eliminado correctamente"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar cliente: {str(e)}"}), 500


@main_bp.route('/clientes/usuario/<int:usuario_id>', methods=['GET'])
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


# ============================================================
# MÓDULO: HISTORIAL DE FÓRMULAS
# ============================================================

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
        
        # Validación: cliente existe
        cliente = Cliente.query.get(data['cliente_id'])
        if not cliente:
            return jsonify({"error": "El cliente especificado no existe"}), 404
        
        # Validación: cliente activo
        if not cliente.estado:
            return jsonify({"error": "No se puede agregar historial a un cliente inactivo"}), 400
        
        # Validación de valores de fórmula (opcional - validar que sean números válidos)
        def validar_valor_formula(valor):
            if valor is None:
                return True
            try:
                # Permite números positivos, negativos, decimales
                float(valor)
                return True
            except (ValueError, TypeError):
                return False
        
        campos_formula = ['od_esfera', 'od_cilindro', 'od_eje', 'oi_esfera', 'oi_cilindro', 'oi_eje']
        for campo in campos_formula:
            if campo in data and data[campo] is not None:
                if not validar_valor_formula(data[campo]):
                    return jsonify({"error": f"El campo {campo} debe ser un número válido"}), 400
        
        historial = HistorialFormula(
            cliente_id=data['cliente_id'],
            descripcion=data.get('descripcion', '').strip(),
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
        return jsonify({"error": f"Error al crear historial de fórmula: {str(e)}"}), 500


@main_bp.route('/historial-formula/<int:id>', methods=['PUT'])
def update_historial_formula(id):
    try:
        historial = HistorialFormula.query.get(id)
        if not historial:
            return jsonify({"error": "Historial de fórmula no encontrado"}), 404
            
        data = request.get_json()
        
        # Validación: cliente existe (si cambia)
        if 'cliente_id' in data:
            cliente = Cliente.query.get(data['cliente_id'])
            if not cliente:
                return jsonify({"error": "El cliente especificado no existe"}), 404
            if not cliente.estado:
                return jsonify({"error": "No se puede asignar historial a un cliente inactivo"}), 400
            historial.cliente_id = data['cliente_id']
            
        # Validación de valores de fórmula
        def validar_valor_formula(valor):
            if valor is None:
                return True
            try:
                float(valor)
                return True
            except (ValueError, TypeError):
                return False
        
        campos_formula = ['od_esfera', 'od_cilindro', 'od_eje', 'oi_esfera', 'oi_cilindro', 'oi_eje']
        for campo in campos_formula:
            if campo in data and data[campo] is not None:
                if not validar_valor_formula(data[campo]):
                    return jsonify({"error": f"El campo {campo} debe ser un número válido"}), 400
        
        if 'descripcion' in data:
            historial.descripcion = data['descripcion'].strip()
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
        return jsonify({"error": f"Error al actualizar historial de fórmula: {str(e)}"}), 500


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
        return jsonify({"error": f"Error al eliminar historial de fórmula: {str(e)}"}), 500


@main_bp.route('/clientes/<int:cliente_id>/historial', methods=['GET'])
def get_historial_cliente(cliente_id):
    try:
        # Validación: cliente existe
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404
            
        historiales = HistorialFormula.query.filter_by(cliente_id=cliente_id).all()
        return jsonify([historial.to_dict() for historial in historiales])
        
    except Exception as e:
        return jsonify({"error": f"Error al obtener historial del cliente: {str(e)}"}), 500