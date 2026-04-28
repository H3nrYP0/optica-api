from flask import jsonify, request
from app.database import db
from app.Models.models import Cliente, HistorialFormula, Cita, Empleado
from app.auth.decorators import permiso_requerido
from datetime import datetime
from app.routes import main_bp
import re

EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
PHONE_REGEX = re.compile(r'^\d{7,15}$')

# ============================================================
# NOTA IMPORTANTE:
# Los clientes son SOLO para la landing page.
# NO tienen usuario en el sistema.
# NO tienen rol.
# NO acceden al panel administrativo.
# ============================================================

# ============================================================
# RUTAS PÚBLICAS (Landing page) — SIN autenticación
# ============================================================

@main_bp.route('/clientes', methods=['GET'])
def get_clientes_publico():
    """Listar clientes (público)"""
    try:
        clientes = Cliente.query.all()
        return jsonify([cliente.to_dict() for cliente in clientes])
    except Exception as e:
        return jsonify({"error": f"Error al obtener clientes: {str(e)}"}), 500


@main_bp.route('/clientes', methods=['POST'])
def create_cliente_publico():
    """
    Registro de cliente desde landing page.
    NO requiere autenticación.
    """
    try:
        data = request.get_json()

        required_fields = ['nombre', 'apellido', 'numero_documento', 'fecha_nacimiento']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        nombre = data['nombre'].strip()
        apellido = data['apellido'].strip()
        numero_documento = str(data['numero_documento']).strip()

        if not nombre or not apellido:
            return jsonify({"error": "Nombre y apellido son requeridos"}), 400

        # Validar documento único
        if Cliente.query.filter_by(numero_documento=numero_documento).first():
            return jsonify({
                "success": False,
                "error": "Ya existe un cliente con este número de documento"
            }), 400

        # Validar fecha de nacimiento
        try:
            fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
            if fecha_nacimiento > datetime.now().date():
                return jsonify({"error": "La fecha de nacimiento no puede ser futura"}), 400
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400

        # Validar correo si se envía
        correo = data.get('correo', '').strip() or None
        if correo and not EMAIL_REGEX.match(correo):
            return jsonify({"error": "Formato de correo electrónico inválido"}), 400

        # Validar teléfono si se envía
        telefono = data.get('telefono', '').strip() or None
        if telefono and not PHONE_REGEX.match(telefono):
            return jsonify({"error": "El teléfono debe contener solo números (7-15 dígitos)"}), 400

        cliente = Cliente(
            nombre=nombre,
            apellido=apellido,
            tipo_documento=data.get('tipo_documento', '').strip() or None,
            numero_documento=numero_documento,
            fecha_nacimiento=fecha_nacimiento,
            genero=data.get('genero', '').strip() or None,
            telefono=telefono,
            correo=correo,
            municipio=data.get('municipio', '').strip() or None,
            direccion=data.get('direccion', '').strip() or None,
            departamento=data.get('departamento', '').strip() or None,
            barrio=data.get('barrio', '').strip() or None,
            codigo_postal=data.get('codigo_postal', '').strip() or None,
            ocupacion=data.get('ocupacion', '').strip() or None,
            telefono_emergencia=data.get('telefono_emergencia', '').strip() or None,
            estado=data.get('estado', True)
        )

        db.session.add(cliente)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Cliente registrado exitosamente",
            "cliente": cliente.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Error al crear cliente: {str(e)}"}), 500


@main_bp.route('/clientes/<int:id>', methods=['PUT'])
def update_cliente_publico(id):
    """Actualizar cliente desde landing (público)"""
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404

        data = request.get_json()

        # Actualizar solo los campos permitidos
        if 'nombre' in data:
            cliente.nombre = data['nombre'].strip()
        if 'apellido' in data:
            cliente.apellido = data['apellido'].strip()
        if 'tipo_documento' in data:
            cliente.tipo_documento = data['tipo_documento'].strip() or None
        if 'numero_documento' in data:
            doc = str(data['numero_documento']).strip()
            existente = Cliente.query.filter_by(numero_documento=doc).first()
            if existente and existente.id != id:
                return jsonify({"error": "Ya existe otro cliente con este número de documento"}), 400
            cliente.numero_documento = doc
        if 'fecha_nacimiento' in data:
            try:
                cliente.fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
        if 'genero' in data:
            cliente.genero = data['genero'].strip() or None
        if 'telefono' in data:
            telefono = data['telefono'].strip() if data['telefono'] else None
            if telefono and not PHONE_REGEX.match(telefono):
                return jsonify({"error": "El teléfono debe contener solo números (7-15 dígitos)"}), 400
            cliente.telefono = telefono
        if 'correo' in data:
            correo = data['correo'].strip() if data['correo'] else None
            if correo and not EMAIL_REGEX.match(correo):
                return jsonify({"error": "Formato de correo electrónico inválido"}), 400
            cliente.correo = correo
        if 'municipio' in data:
            cliente.municipio = data['municipio'].strip() or None
        if 'direccion' in data:
            cliente.direccion = data['direccion'].strip() or None
        if 'departamento' in data:
            cliente.departamento = data['departamento'].strip() or None
        if 'barrio' in data:
            cliente.barrio = data['barrio'].strip() or None
        if 'codigo_postal' in data:
            cliente.codigo_postal = data['codigo_postal'].strip() or None
        if 'ocupacion' in data:
            cliente.ocupacion = data['ocupacion'].strip() or None
        if 'telefono_emergencia' in data:
            cliente.telefono_emergencia = data['telefono_emergencia'].strip() or None

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Cliente actualizado",
            "cliente": cliente.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@main_bp.route('/clientes/<int:id>', methods=['DELETE'])
def delete_cliente_publico(id):
    """Eliminar cliente (solo si no tiene asociaciones)"""
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404

        # Verificar si tiene citas, ventas o pedidos asociados
        if cliente.citas and len(cliente.citas) > 0:
            return jsonify({
                "error": "No se puede eliminar el cliente porque tiene citas asociadas. Desactívelo en su lugar."
            }), 400
        if cliente.ventas and len(cliente.ventas) > 0:
            return jsonify({
                "error": "No se puede eliminar el cliente porque tiene ventas asociadas. Desactívelo en su lugar."
            }), 400
        if cliente.pedidos and len(cliente.pedidos) > 0:
            return jsonify({
                "error": "No se puede eliminar el cliente porque tiene pedidos asociados. Desactívelo en su lugar."
            }), 400

        db.session.delete(cliente)
        db.session.commit()
        return jsonify({"message": "Cliente eliminado correctamente"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar cliente: {str(e)}"}), 500


# ============================================================
# ADMINISTRACIÓN DE CLIENTES — requiere permiso 'clientes'
# Solo el staff puede gestionar clientes desde el panel admin
# ============================================================

@main_bp.route('/admin/clientes', methods=['GET'])
@permiso_requerido('clientes')
def get_clientes():
    """Listar todos los clientes (admin)"""
    try:
        clientes = Cliente.query.all()
        return jsonify([cliente.to_dict() for cliente in clientes])
    except Exception as e:
        return jsonify({"error": f"Error al obtener clientes: {str(e)}"}), 500


@main_bp.route('/admin/clientes', methods=['POST'])
@permiso_requerido('clientes')
def create_cliente():
    """Crear cliente desde administración"""
    try:
        data = request.get_json()

        required_fields = ['nombre', 'apellido', 'numero_documento', 'fecha_nacimiento']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        nombre = data['nombre'].strip()
        apellido = data['apellido'].strip()
        numero_documento = str(data['numero_documento']).strip()

        if not nombre or not apellido:
            return jsonify({"error": "Nombre y apellido son requeridos"}), 400

        if Cliente.query.filter_by(numero_documento=numero_documento).first():
            return jsonify({"error": "Ya existe un cliente con este número de documento"}), 400

        try:
            fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
            if fecha_nacimiento > datetime.now().date():
                return jsonify({"error": "La fecha de nacimiento no puede ser futura"}), 400
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400

        correo = data.get('correo', '').strip() or None
        if correo and not EMAIL_REGEX.match(correo):
            return jsonify({"error": "Formato de correo electrónico inválido"}), 400

        telefono = data.get('telefono', '').strip() or None
        if telefono and not PHONE_REGEX.match(telefono):
            return jsonify({"error": "El teléfono debe contener solo números (7-15 dígitos)"}), 400

        cliente = Cliente(
            nombre=nombre,
            apellido=apellido,
            tipo_documento=data.get('tipo_documento', '').strip() or None,
            numero_documento=numero_documento,
            fecha_nacimiento=fecha_nacimiento,
            genero=data.get('genero', '').strip() or None,
            telefono=telefono,
            correo=correo,
            municipio=data.get('municipio', '').strip() or None,
            direccion=data.get('direccion', '').strip() or None,
            departamento=data.get('departamento', '').strip() or None,
            barrio=data.get('barrio', '').strip() or None,
            codigo_postal=data.get('codigo_postal', '').strip() or None,
            ocupacion=data.get('ocupacion', '').strip() or None,
            telefono_emergencia=data.get('telefono_emergencia', '').strip() or None,
            estado=data.get('estado', True)
        )

        db.session.add(cliente)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Cliente creado exitosamente",
            "cliente": cliente.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear cliente: {str(e)}"}), 500


@main_bp.route('/admin/clientes/<int:id>', methods=['GET'])
@permiso_requerido('clientes')
def get_cliente(id):
    """Obtener cliente por ID (admin)"""
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404
        return jsonify(cliente.to_dict())
    except Exception as e:
        return jsonify({"error": f"Error al obtener cliente: {str(e)}"}), 500


@main_bp.route('/admin/clientes/<int:id>', methods=['PUT'])
@permiso_requerido('clientes')
def update_cliente(id):
    """Actualizar cliente (admin)"""
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404

        data = request.get_json()

        if 'nombre' in data:
            cliente.nombre = data['nombre'].strip()
        if 'apellido' in data:
            cliente.apellido = data['apellido'].strip()
        if 'tipo_documento' in data:
            cliente.tipo_documento = data['tipo_documento'].strip() or None
        if 'numero_documento' in data:
            doc = str(data['numero_documento']).strip()
            existente = Cliente.query.filter_by(numero_documento=doc).first()
            if existente and existente.id != id:
                return jsonify({"error": "Ya existe otro cliente con este número de documento"}), 400
            cliente.numero_documento = doc
        if 'fecha_nacimiento' in data:
            try:
                cliente.fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
        if 'genero' in data:
            cliente.genero = data['genero'].strip() or None
        if 'telefono' in data:
            telefono = data['telefono'].strip() if data['telefono'] else None
            if telefono and not PHONE_REGEX.match(telefono):
                return jsonify({"error": "El teléfono debe contener solo números (7-15 dígitos)"}), 400
            cliente.telefono = telefono
        if 'correo' in data:
            correo = data['correo'].strip() if data['correo'] else None
            if correo and not EMAIL_REGEX.match(correo):
                return jsonify({"error": "Formato de correo electrónico inválido"}), 400
            cliente.correo = correo
        if 'municipio' in data:
            cliente.municipio = data['municipio'].strip() or None
        if 'direccion' in data:
            cliente.direccion = data['direccion'].strip() or None
        if 'departamento' in data:
            cliente.departamento = data['departamento'].strip() or None
        if 'barrio' in data:
            cliente.barrio = data['barrio'].strip() or None
        if 'codigo_postal' in data:
            cliente.codigo_postal = data['codigo_postal'].strip() or None
        if 'ocupacion' in data:
            cliente.ocupacion = data['ocupacion'].strip() or None
        if 'telefono_emergencia' in data:
            cliente.telefono_emergencia = data['telefono_emergencia'].strip() or None
        if 'estado' in data:
            cliente.estado = data['estado']

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Cliente actualizado",
            "cliente": cliente.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar cliente: {str(e)}"}), 500


@main_bp.route('/admin/clientes/<int:id>', methods=['DELETE'])
@permiso_requerido('clientes')
def delete_cliente(id):
    """Eliminar cliente (admin) - solo si está inactivo y sin asociaciones"""
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404

        if cliente.estado:
            return jsonify({
                "error": "Debes desactivar el cliente antes de eliminarlo",
                "codigo": "CLIENTE_ACTIVO"
            }), 400

        if cliente.citas and len(cliente.citas) > 0:
            return jsonify({
                "error": "No se puede eliminar un cliente que tiene citas asociadas"
            }), 400

        if cliente.ventas and len(cliente.ventas) > 0:
            return jsonify({
                "error": "No se puede eliminar un cliente que tiene ventas asociadas"
            }), 400

        if cliente.pedidos and len(cliente.pedidos) > 0:
            return jsonify({
                "error": "No se puede eliminar un cliente que tiene pedidos asociados"
            }), 400

        db.session.delete(cliente)
        db.session.commit()
        return jsonify({"message": "Cliente eliminado correctamente"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar cliente: {str(e)}"}), 500


# ============================================================
# HISTORIAL DE FÓRMULAS (solo admin)
# ============================================================

@main_bp.route('/admin/clientes/<int:cliente_id>/historial', methods=['GET'])
@permiso_requerido('clientes')
def get_historial_cliente(cliente_id):
    """Obtener historial de fórmulas de un cliente"""
    try:
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404

        historiales = HistorialFormula.query.filter_by(cliente_id=cliente_id).all()
        return jsonify([historial.to_dict() for historial in historiales])
    except Exception as e:
        return jsonify({"error": f"Error al obtener historial: {str(e)}"}), 500


@main_bp.route('/admin/historial-formula', methods=['POST'])
@permiso_requerido('clientes')
def create_historial_formula():
    """Crear entrada en historial de fórmulas"""
    try:
        data = request.get_json()

        if not data.get('cliente_id'):
            return jsonify({"error": "El cliente_id es requerido"}), 400

        cliente = Cliente.query.get(data['cliente_id'])
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404

        historial = HistorialFormula(
            cliente_id=data['cliente_id'],
            descripcion=data.get('descripcion', '').strip() or None,
            od_esfera=data.get('od_esfera'),
            od_cilindro=data.get('od_cilindro'),
            od_eje=data.get('od_eje'),
            oi_esfera=data.get('oi_esfera'),
            oi_cilindro=data.get('oi_cilindro'),
            oi_eje=data.get('oi_eje')
        )

        db.session.add(historial)
        db.session.commit()
        return jsonify({"message": "Historial creado", "historial": historial.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear historial: {str(e)}"}), 500


@main_bp.route('/admin/historial-formula/<int:id>', methods=['DELETE'])
@permiso_requerido('clientes')
def delete_historial_formula(id):
    """Eliminar entrada de historial de fórmulas"""
    try:
        historial = HistorialFormula.query.get(id)
        if not historial:
            return jsonify({"error": "Historial no encontrado"}), 404

        db.session.delete(historial)
        db.session.commit()
        return jsonify({"message": "Fórmula eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar historial: {str(e)}"}), 500