from flask import jsonify, request
from app.database import db
from app.Models.models import Cliente, HistorialFormula, Usuario, Cita
from app.auth.decorators import permiso_requerido, get_usuario_actual
from datetime import datetime
from app.routes import main_bp
import re

EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
PHONE_REGEX = re.compile(r'^\d{7,15}$')

# ============================================================
# RUTAS PÚBLICAS (para landing page) — SIN @permiso_requerido
# ============================================================

@main_bp.route('/clientes', methods=['GET'])
def get_clientes_publico():
    try:
        clientes = Cliente.query.all()
        return jsonify([cliente.to_dict() for cliente in clientes])
    except Exception as e:
        return jsonify({"error": "Error al obtener clientes"}), 500

@main_bp.route('/clientes', methods=['POST'])
def create_cliente_publico():
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
            departamento=data.get('departamento'),
            barrio=data.get('barrio'),
            codigo_postal=data.get('codigo_postal'),
            ocupacion=data.get('ocupacion'),
            telefono_emergencia=data.get('telefono_emergencia'),
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
        return jsonify({"success": False, "error": f"Error al crear cliente: {str(e)}"}), 500

@main_bp.route('/clientes/<int:id>', methods=['PUT'])
def update_cliente_publico(id):
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
        if 'departamento' in data: cliente.departamento = data['departamento']
        if 'barrio' in data: cliente.barrio = data['barrio']
        if 'codigo_postal' in data: cliente.codigo_postal = data['codigo_postal']
        if 'ocupacion' in data: cliente.ocupacion = data['ocupacion']
        if 'telefono_emergencia' in data: cliente.telefono_emergencia = data['telefono_emergencia']
        db.session.commit()
        return jsonify({"success": True, "message": "Cliente actualizado", "cliente": cliente.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@main_bp.route('/clientes/<int:id>', methods=['DELETE'])
def delete_cliente_publico(id):
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


# ============================================================
# CLIENTE VE SU PROPIO PERFIL — requiere JWT (cualquier rol)
# ============================================================

@main_bp.route('/cliente/perfil', methods=['GET'])
def get_mi_perfil():
    try:
        claims = get_usuario_actual()
        usuario_id = claims.get('id')
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        if not usuario.cliente_id:
            return jsonify({"error": "No tienes un perfil de cliente asociado"}), 404
        cliente = Cliente.query.get(usuario.cliente_id)
        return jsonify(cliente.to_dict())
    except Exception as e:
        return jsonify({"error": f"Error al obtener perfil: {str(e)}"}), 500


@main_bp.route('/cliente/perfil', methods=['PUT'])
def update_mi_perfil():
    try:
        claims = get_usuario_actual()
        usuario_id = claims.get('id')
        usuario = Usuario.query.get(usuario_id)
        if not usuario or not usuario.cliente_id:
            return jsonify({"error": "No tienes un perfil de cliente asociado"}), 404
        cliente = Cliente.query.get(usuario.cliente_id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data: cliente.nombre = data['nombre'].strip()
        if 'apellido' in data: cliente.apellido = data['apellido'].strip()
        if 'telefono' in data:
            telefono = data['telefono'].strip()
            if telefono and not PHONE_REGEX.match(telefono):
                return jsonify({"error": "Teléfono inválido"}), 400
            cliente.telefono = telefono
        if 'direccion' in data: cliente.direccion = data['direccion'].strip()
        if 'correo' in data:
            correo = data['correo'].strip()
            if correo and not EMAIL_REGEX.match(correo):
                return jsonify({"error": "Correo inválido"}), 400
            cliente.correo = correo
        if 'departamento' in data: cliente.departamento = data['departamento'].strip()
        if 'municipio' in data: cliente.municipio = data['municipio'].strip()
        if 'barrio' in data: cliente.barrio = data['barrio'].strip()
        if 'codigo_postal' in data: cliente.codigo_postal = data['codigo_postal'].strip()
        db.session.commit()
        return jsonify({"success": True, "message": "Perfil actualizado", "cliente": cliente.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar perfil: {str(e)}"}), 500


@main_bp.route('/cliente/cambiar-contrasenia', methods=['POST'])
def cambiar_mi_contrasenia():
    try:
        claims = get_usuario_actual()
        usuario_id = claims.get('id')
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404
        data = request.get_json()
        from app.auth.helpers import verificar_contrasenia
        from werkzeug.security import generate_password_hash
        if not verificar_contrasenia(data.get('contrasenia_actual'), usuario.contrasenia, usuario.id, db):
            return jsonify({"error": "Contraseña actual incorrecta"}), 401
        if len(data.get('nueva_contrasenia', '')) < 6:
            return jsonify({"error": "La nueva contraseña debe tener al menos 6 caracteres"}), 400
        usuario.contrasenia = generate_password_hash(data['nueva_contrasenia'])
        db.session.commit()
        return jsonify({"success": True, "message": "Contraseña actualizada"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al cambiar contraseña: {str(e)}"}), 500


@main_bp.route('/cliente/citas', methods=['GET'])
def get_mis_citas():
    try:
        claims = get_usuario_actual()
        usuario_id = claims.get('id')
        usuario = Usuario.query.get(usuario_id)
        if not usuario or not usuario.cliente_id:
            return jsonify({"error": "No tienes un perfil de cliente asociado"}), 404
        citas = Cita.query.filter_by(cliente_id=usuario.cliente_id).order_by(Cita.fecha.desc(), Cita.hora.desc()).all()
        return jsonify([cita.to_dict() for cita in citas])
    except Exception as e:
        return jsonify({"error": f"Error al obtener citas: {str(e)}"}), 500


@main_bp.route('/cliente/citas/<int:cita_id>', methods=['DELETE'])
def cancelar_mi_cita(cita_id):
    try:
        claims = get_usuario_actual()
        usuario_id = claims.get('id')
        usuario = Usuario.query.get(usuario_id)
        if not usuario or not usuario.cliente_id:
            return jsonify({"error": "No tienes un perfil de cliente asociado"}), 404
        cita = Cita.query.get(cita_id)
        if not cita:
            return jsonify({"error": "Cita no encontrada"}), 404
        if cita.cliente_id != usuario.cliente_id:
            return jsonify({"error": "No puedes cancelar una cita que no te pertenece"}), 403
        if cita.estado_cita_id not in [1, 2]:
            return jsonify({"error": "Solo se pueden cancelar citas pendientes o confirmadas"}), 400
        ahora = datetime.utcnow()
        fecha_hora_cita = datetime.combine(cita.fecha, cita.hora)
        if fecha_hora_cita < ahora:
            return jsonify({"error": "No se puede cancelar una cita que ya pasó"}), 400
        cita.estado_cita_id = 4
        db.session.commit()
        cliente_nombre = f"{usuario.cliente.nombre} {usuario.cliente.apellido}"
        servicio_nombre = cita.servicio.nombre if cita.servicio else "servicio"
        return jsonify({
            "success": True,
            "message": "Cita cancelada correctamente",
            "cita": {
                "id": cita.id,
                "servicio": servicio_nombre,
                "fecha": cita.fecha.strftime('%d/%m/%Y'),
                "hora": cita.hora.strftime('%H:%M'),
                "cliente": cliente_nombre
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al cancelar cita: {str(e)}"}), 500


@main_bp.route('/cliente/historial', methods=['GET'])
def get_mi_historial():
    try:
        claims = get_usuario_actual()
        usuario_id = claims.get('id')
        usuario = Usuario.query.get(usuario_id)
        if not usuario or not usuario.cliente_id:
            return jsonify([])
        historiales = HistorialFormula.query.filter_by(cliente_id=usuario.cliente_id).all()
        return jsonify([historial.to_dict() for historial in historiales])
    except Exception as e:
        return jsonify({"error": f"Error al obtener historial: {str(e)}"}), 500


# ============================================================
# ADMIN GESTIONA CLIENTES — requiere permiso 'clientes'
# ============================================================

@main_bp.route('/admin/clientes', methods=['GET'])
@permiso_requerido('clientes')
def get_clientes():
    try:
        clientes = Cliente.query.all()
        return jsonify([cliente.to_dict() for cliente in clientes])
    except Exception as e:
        return jsonify({"error": "Error al obtener clientes"}), 500


@main_bp.route('/admin/clientes', methods=['POST'])
@permiso_requerido('clientes')
def create_cliente():
    try:
        data = request.get_json()
        required_fields = ['nombre', 'apellido', 'numero_documento', 'fecha_nacimiento']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        nombre = data['nombre'].strip()
        apellido = data['apellido'].strip()
        if not nombre or not apellido:
            return jsonify({"error": "Nombre y apellido son requeridos"}), 400
        if Cliente.query.filter_by(numero_documento=data['numero_documento']).first():
            return jsonify({"error": "Ya existe un cliente con este número de documento"}), 400
        try:
            fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
            if fecha_nacimiento > datetime.now().date():
                return jsonify({"error": "La fecha de nacimiento no puede ser futura"}), 400
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
        correo = data.get('correo', '').strip()
        if correo and not EMAIL_REGEX.match(correo):
            return jsonify({"error": "Formato de correo electrónico inválido"}), 400
        telefono = data.get('telefono', '').strip()
        if telefono and not PHONE_REGEX.match(telefono):
            return jsonify({"error": "El teléfono debe contener solo números (7-15 dígitos)"}), 400
        cliente = Cliente(
            nombre=nombre,
            apellido=apellido,
            tipo_documento=data.get('tipo_documento', '').strip(),
            numero_documento=data['numero_documento'].strip(),
            fecha_nacimiento=fecha_nacimiento,
            genero=data.get('genero', '').strip() or None,
            telefono=telefono or None,
            correo=correo or None,
            municipio=data.get('municipio', '').strip(),
            direccion=data.get('direccion', '').strip(),
            departamento=data.get('departamento', '').strip(),
            barrio=data.get('barrio', '').strip(),
            codigo_postal=data.get('codigo_postal', '').strip(),
            ocupacion=data.get('ocupacion', '').strip(),
            telefono_emergencia=data.get('telefono_emergencia', '').strip() or None,
            estado=data.get('estado', True)
        )
        db.session.add(cliente)
        db.session.commit()
        return jsonify({"success": True, "message": "Cliente creado exitosamente", "cliente": cliente.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear cliente: {str(e)}"}), 500


@main_bp.route('/admin/clientes/<int:id>', methods=['GET'])
@permiso_requerido('clientes')
def get_cliente(id):
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
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404
        data = request.get_json()
        if 'nombre' in data: cliente.nombre = data['nombre'].strip()
        if 'apellido' in data: cliente.apellido = data['apellido'].strip()
        if 'tipo_documento' in data: cliente.tipo_documento = data['tipo_documento'].strip()
        if 'numero_documento' in data:
            doc = data['numero_documento'].strip()
            existente = Cliente.query.filter_by(numero_documento=doc).first()
            if existente and existente.id != id:
                return jsonify({"error": "Ya existe otro cliente con este número de documento"}), 400
            cliente.numero_documento = doc
        if 'fecha_nacimiento' in data:
            try:
                cliente.fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
        if 'genero' in data: cliente.genero = data['genero'].strip() or None
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
        if 'municipio' in data: cliente.municipio = data['municipio'].strip()
        if 'direccion' in data: cliente.direccion = data['direccion'].strip()
        if 'departamento' in data: cliente.departamento = data['departamento'].strip()
        if 'barrio' in data: cliente.barrio = data['barrio'].strip()
        if 'codigo_postal' in data: cliente.codigo_postal = data['codigo_postal'].strip()
        if 'ocupacion' in data: cliente.ocupacion = data['ocupacion'].strip()
        if 'telefono_emergencia' in data: cliente.telefono_emergencia = data['telefono_emergencia'].strip() or None
        if 'estado' in data: cliente.estado = data['estado']
        db.session.commit()
        return jsonify({"success": True, "message": "Cliente actualizado", "cliente": cliente.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al actualizar cliente: {str(e)}"}), 500


@main_bp.route('/admin/clientes/<int:id>', methods=['DELETE'])
@permiso_requerido('clientes')
def delete_cliente(id):
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404
        if cliente.citas and len(cliente.citas) > 0:
            return jsonify({"error": "No se puede eliminar un cliente que tiene citas asociadas"}), 400
        if cliente.ventas and len(cliente.ventas) > 0:
            return jsonify({"error": "No se puede eliminar un cliente que tiene ventas asociadas"}), 400
        if cliente.pedidos and len(cliente.pedidos) > 0:
            return jsonify({"error": "No se puede eliminar un cliente que tiene pedidos asociados"}), 400
        if cliente.usuario:
            return jsonify({"error": "No se puede eliminar un cliente con usuario asociado. Desactívelo en su lugar."}), 400
        db.session.delete(cliente)
        db.session.commit()
        return jsonify({"message": "Cliente eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al eliminar cliente: {str(e)}"}), 500


# ============================================================
# HISTORIAL DE FÓRMULAS
# ============================================================

@main_bp.route('/admin/clientes/<int:cliente_id>/historial', methods=['GET'])
@permiso_requerido('clientes')
def get_historial_cliente(cliente_id):
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
    try:
        data = request.get_json()
        if not data.get('cliente_id'):
            return jsonify({"error": "El cliente_id es requerido"}), 400
        cliente = Cliente.query.get(data['cliente_id'])
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404
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
        return jsonify({"message": "Historial creado", "historial": historial.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al crear historial: {str(e)}"}), 500


@main_bp.route('/admin/historial-formula/<int:id>', methods=['DELETE'])
@permiso_requerido('clientes')
def delete_historial_formula(id):
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