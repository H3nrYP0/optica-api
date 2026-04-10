from flask import jsonify, request
from app.database import db
from app.Models.models import Empleado, Cita, Horario
from datetime import datetime
from app.routes import main_bp
import re

# Regex para validar email
EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
# Regex para validar teléfono (solo números, 7-15 dígitos)
PHONE_REGEX = re.compile(r'^\d{7,15}$')

# ============================================================
# MÓDULO: EMPLEADOS
# ============================================================

@main_bp.route('/empleados', methods=['GET'])
def get_empleados():
    try:
        empleados = Empleado.query.order_by(Empleado.id.desc()).all()
        return jsonify([empleado.to_dict() for empleado in empleados])
    except Exception as e:
        return jsonify({"error": "Error interno al obtener empleados", "detalle": str(e)}), 500

@main_bp.route('/empleados/<int:id>', methods=['GET'])
def get_empleado(id):
    try:
        empleado = Empleado.query.get(id)
        if not empleado:
            return jsonify({"error": f"No existe un empleado con ID {id}"}), 404
        return jsonify(empleado.to_dict())
    except Exception as e:
        return jsonify({"error": "Error interno al obtener empleado", "detalle": str(e)}), 500

@main_bp.route('/empleados', methods=['POST'])
def create_empleado():
    try:
        data = request.get_json()
        required_fields = ['nombre', 'numero_documento', 'fecha_ingreso']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "error": f"El campo '{field}' es obligatorio.",
                    "codigo": "CAMPO_REQUERIDO"
                }), 400

        nombre = data['nombre'].strip()
        if not nombre:
            return jsonify({
                "error": "El nombre del empleado no puede estar vacío.",
                "codigo": "NOMBRE_VACIO"
            }), 400

        numero_documento = str(data['numero_documento']).strip()
        if not numero_documento:
            return jsonify({
                "error": "El número de documento no puede estar vacío.",
                "codigo": "DOCUMENTO_VACIO"
            }), 400

        if Empleado.query.filter_by(numero_documento=numero_documento).first():
            return jsonify({
                "error": f"El documento '{numero_documento}' ya está registrado para otro empleado.",
                "codigo": "DOCUMENTO_DUPLICADO"
            }), 400

        # Validar email
        correo = data.get('correo', '').strip()
        if correo:
            if not EMAIL_REGEX.match(correo):
                return jsonify({
                    "error": f"El correo '{correo}' no tiene un formato válido (ejemplo: nombre@dominio.com).",
                    "codigo": "EMAIL_INVALIDO"
                }), 400
            # Opcional: verificar email duplicado
            if Empleado.query.filter_by(correo=correo).first():
                return jsonify({
                    "error": f"El correo '{correo}' ya está registrado para otro empleado.",
                    "codigo": "EMAIL_DUPLICADO"
                }), 400

        telefono = data.get('telefono', '').strip()
        if telefono and not PHONE_REGEX.match(telefono):
            return jsonify({
                "error": f"El teléfono '{telefono}' debe contener solo números y tener entre 7 y 15 dígitos.",
                "codigo": "TELEFONO_INVALIDO"
            }), 400

        try:
            fecha_ingreso = datetime.strptime(data['fecha_ingreso'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                "error": "La fecha de ingreso debe tener el formato YYYY-MM-DD (ejemplo: 2023-01-31).",
                "codigo": "FECHA_FORMATO_INVALIDO"
            }), 400

        if fecha_ingreso > datetime.now().date():
            return jsonify({
                "error": "La fecha de ingreso no puede ser una fecha futura.",
                "codigo": "FECHA_FUTURA"
            }), 400

        cargo = data.get('cargo', '').strip()
        if cargo and len(cargo) > 50:
            return jsonify({
                "error": "El cargo no puede tener más de 50 caracteres.",
                "codigo": "CARGO_LARGO"
            }), 400

        empleado = Empleado(
            nombre=nombre,
            tipo_documento=data.get('tipo_documento', '').strip(),
            numero_documento=numero_documento,
            telefono=telefono if telefono else None,
            correo=correo if correo else None,
            direccion=data.get('direccion', '').strip(),
            fecha_ingreso=fecha_ingreso,
            cargo=cargo if cargo else None,
            estado=data.get('estado', True)
        )

        db.session.add(empleado)
        db.session.commit()
        return jsonify({"message": "Empleado creado exitosamente", "empleado": empleado.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error interno al crear empleado", "detalle": str(e)}), 500


@main_bp.route('/empleados/<int:id>', methods=['PUT'])
def update_empleado(id):
    try:
        empleado = Empleado.query.get(id)
        if not empleado:
            return jsonify({"error": f"No existe un empleado con ID {id}"}), 404

        data = request.get_json()

        if 'nombre' in data:
            nombre = data['nombre'].strip()
            if not nombre:
                return jsonify({"error": "El nombre del empleado no puede estar vacío."}), 400
            empleado.nombre = nombre

        if 'numero_documento' in data:
            nuevo_doc = str(data['numero_documento']).strip()
            if not nuevo_doc:
                return jsonify({"error": "El número de documento no puede estar vacío."}), 400

            existente = Empleado.query.filter(
                Empleado.numero_documento == nuevo_doc,
                Empleado.id != id
            ).first()
            if existente:
                return jsonify({
                    "error": f"El documento '{nuevo_doc}' ya está asignado a otro empleado (ID {existente.id}).",
                    "codigo": "DOCUMENTO_DUPLICADO"
                }), 400
            empleado.numero_documento = nuevo_doc

        if 'correo' in data:
            correo = data['correo'].strip() if data['correo'] else None
            if correo:
                if not EMAIL_REGEX.match(correo):
                    return jsonify({
                        "error": f"El correo '{correo}' no tiene un formato válido.",
                        "codigo": "EMAIL_INVALIDO"
                    }), 400
                # Verificar duplicado
                existe_email = Empleado.query.filter(
                    Empleado.correo == correo,
                    Empleado.id != id
                ).first()
                if existe_email:
                    return jsonify({
                        "error": f"El correo '{correo}' ya está registrado para otro empleado.",
                        "codigo": "EMAIL_DUPLICADO"
                    }), 400
            empleado.correo = correo

        if 'telefono' in data:
            telefono = data['telefono'].strip() if data['telefono'] else None
            if telefono and not PHONE_REGEX.match(telefono):
                return jsonify({
                    "error": f"El teléfono '{telefono}' debe contener solo números y tener entre 7 y 15 dígitos.",
                    "codigo": "TELEFONO_INVALIDO"
                }), 400
            empleado.telefono = telefono

        if 'fecha_ingreso' in data:
            try:
                fecha_ingreso = datetime.strptime(data['fecha_ingreso'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    "error": "Formato de fecha inválido. Use YYYY-MM-DD.",
                    "codigo": "FECHA_FORMATO_INVALIDO"
                }), 400
            if fecha_ingreso > datetime.now().date():
                return jsonify({
                    "error": "La fecha de ingreso no puede ser futura.",
                    "codigo": "FECHA_FUTURA"
                }), 400
            empleado.fecha_ingreso = fecha_ingreso

        if 'cargo' in data:
            cargo = data['cargo'].strip() if data['cargo'] else None
            if cargo and len(cargo) > 50:
                return jsonify({
                    "error": "El cargo no puede tener más de 50 caracteres.",
                    "codigo": "CARGO_LARGO"
                }), 400
            empleado.cargo = cargo

        # Desactivación con restricciones
        if 'estado' in data and not data['estado']:
            citas_pendientes = Cita.query.filter(
                Cita.empleado_id == id,
                Cita.estado_cita_id == 1
            ).first()
            if citas_pendientes:
                return jsonify({
                    "error": "No se puede desactivar el empleado porque tiene citas pendientes. Primero complete o cancele esas citas.",
                    "codigo": "EMPLEADO_CON_CITAS_PENDIENTES"
                }), 400

            horarios_activos = Horario.query.filter_by(empleado_id=id, activo=True).first()
            if horarios_activos:
                return jsonify({
                    "error": "No se puede desactivar el empleado porque tiene horarios activos. Desactive los horarios primero.",
                    "codigo": "EMPLEADO_CON_HORARIOS_ACTIVOS"
                }), 400

        if 'tipo_documento' in data:
            empleado.tipo_documento = data['tipo_documento'].strip()
        if 'direccion' in data:
            empleado.direccion = data['direccion'].strip()
        if 'estado' in data:
            empleado.estado = data['estado']

        db.session.commit()
        return jsonify({"message": "Empleado actualizado correctamente", "empleado": empleado.to_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error interno al actualizar empleado", "detalle": str(e)}), 500


@main_bp.route('/empleados/<int:id>', methods=['DELETE'])
def delete_empleado(id):
    try:
        empleado = Empleado.query.get(id)
        if not empleado:
            return jsonify({"error": f"No existe un empleado con ID {id}"}), 404

        # Verificar citas
        tiene_citas = Cita.query.filter_by(empleado_id=id).first()
        if tiene_citas:
            return jsonify({
                "error": "No se puede eliminar el empleado porque tiene citas registradas. En su lugar, desactívelo.",
                "codigo": "EMPLEADO_CON_CITAS"
            }), 400

        # Verificar horarios
        tiene_horarios = Horario.query.filter_by(empleado_id=id).first()
        if tiene_horarios:
            return jsonify({
                "error": "No se puede eliminar el empleado porque tiene horarios registrados. Elimine los horarios primero.",
                "codigo": "EMPLEADO_CON_HORARIOS"
            }), 400

        # Verificar campañas
        if empleado.campanas_salud and len(empleado.campanas_salud) > 0:
            return jsonify({
                "error": "No se puede eliminar el empleado porque tiene campañas de salud asociadas. Desactívelo en su lugar.",
                "codigo": "EMPLEADO_CON_CAMPANAS"
            }), 400

        # Verificar estado activo
        if empleado.estado:
            return jsonify({
                "error": "Debes desactivar el empleado antes de eliminarlo.",
                "codigo": "EMPLEADO_ACTIVO"
            }), 400

        db.session.delete(empleado)
        db.session.commit()
        return jsonify({"message": "Empleado eliminado permanentemente."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error interno al eliminar empleado", "detalle": str(e)}), 500