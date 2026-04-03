from flask import Blueprint, jsonify, request
from app.database import db
from app.models import Multimedia

multimedia_bp = Blueprint('multimedia', __name__)

@multimedia_bp.route('', methods=['GET'])
def get_multimedia():
    try:
        return jsonify([m.to_dict() for m in Multimedia.query.all()])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@multimedia_bp.route('', methods=['POST'])
def crear_multimedia():
    try:
        data = request.get_json()
        if not data.get('url'):
            return jsonify({"error": "URL requerida"}), 400
        tipo = data.get('tipo')
        if tipo not in ['categoria', 'comprobante', 'otro']:
            return jsonify({"error": "Tipo debe ser: 'categoria', 'comprobante' u 'otro'"}), 400
        if tipo == 'categoria' and not data.get('categoria_id'):
            return jsonify({"error": "Para tipo 'categoria' se requiere categoria_id"}), 400
        if tipo == 'comprobante' and not data.get('pedido_id'):
            return jsonify({"error": "Para tipo 'comprobante' se requiere pedido_id"}), 400

        if tipo == 'categoria':
            existente = Multimedia.query.filter_by(tipo='categoria', categoria_id=data['categoria_id']).first()
            if existente:
                existente.url = data['url']
                db.session.commit()
                return jsonify({"success": True, "message": "Imagen actualizada", "multimedia": existente.to_dict()})

        if tipo == 'comprobante':
            if Multimedia.query.filter_by(tipo='comprobante', pedido_id=data['pedido_id']).first():
                return jsonify({"error": "Este pedido ya tiene un comprobante"}), 400

        multimedia = Multimedia(url=data['url'], tipo=tipo, categoria_id=data.get('categoria_id'), pedido_id=data.get('pedido_id'))
        db.session.add(multimedia)
        db.session.commit()
        return jsonify({"success": True, "multimedia": multimedia.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@multimedia_bp.route('/<int:id>', methods=['PUT'])
def actualizar_multimedia(id):
    try:
        multimedia = Multimedia.query.get(id)
        if not multimedia:
            return jsonify({"error": "Elemento multimedia no encontrado"}), 404
        data = request.get_json()
        if 'url' in data: multimedia.url = data['url']
        if 'tipo' in data:
            if data['tipo'] not in ['categoria', 'comprobante', 'otro']:
                return jsonify({"error": "Tipo inválido"}), 400
            multimedia.tipo = data['tipo']
        if multimedia.tipo == 'categoria':
            if 'categoria_id' in data: multimedia.categoria_id = data['categoria_id']
            multimedia.pedido_id = None
        elif multimedia.tipo == 'comprobante':
            if 'pedido_id' in data: multimedia.pedido_id = data['pedido_id']
            multimedia.categoria_id = None
        else:
            multimedia.categoria_id = None
            multimedia.pedido_id = None
        db.session.commit()
        return jsonify({"success": True, "multimedia": multimedia.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@multimedia_bp.route('/<int:id>', methods=['DELETE'])
def eliminar_multimedia(id):
    try:
        multimedia = Multimedia.query.get(id)
        if not multimedia:
            return jsonify({"error": "Elemento multimedia no encontrado"}), 404
        db.session.delete(multimedia)
        db.session.commit()
        return jsonify({"success": True, "message": f"Multimedia {id} eliminado"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@multimedia_bp.route('/categoria/<int:categoria_id>', methods=['GET'])
def obtener_imagen_categoria(categoria_id):
    try:
        imagen = Multimedia.query.filter_by(tipo='categoria', categoria_id=categoria_id).first()
        return jsonify(imagen.to_dict() if imagen else {"imagen": None})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@multimedia_bp.route('/comprobante/pedido/<int:pedido_id>', methods=['GET'])
def obtener_comprobante_pedido(pedido_id):
    try:
        comprobante = Multimedia.query.filter_by(tipo='comprobante', pedido_id=pedido_id).first()
        return jsonify(comprobante.to_dict() if comprobante else {"comprobante": None})
    except Exception as e:
        return jsonify({"error": str(e)}), 500