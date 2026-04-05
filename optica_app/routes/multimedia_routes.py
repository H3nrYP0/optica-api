from flask import Blueprint, jsonify, request
from optica_app.database import db
from optica_app.models import Multimedia, Pedido # Importamos Pedido para validar

multimedia_bp = Blueprint('multimedia', __name__)

@multimedia_bp.route('', methods=['POST'])
def crear_multimedia():
    try:
        data = request.get_json()
        url = data.get('url')
        tipo = data.get('tipo')

        if not url or not tipo:
            return jsonify({"error": "URL y Tipo son requeridos"}), 400
        
        if tipo not in ['categoria', 'comprobante', 'otro']:
            return jsonify({"error": "Tipo inválido"}), 400

        # BLINDAJE: Validar existencia del Pedido si es comprobante
        if tipo == 'comprobante':
            pedido_id = data.get('pedido_id')
            if not pedido_id or not Pedido.query.get(pedido_id):
                return jsonify({"error": "Pedido ID inválido o no existe"}), 404
            
            # Evitar duplicados de comprobante por pedido
            if Multimedia.query.filter_by(tipo='comprobante', pedido_id=pedido_id).first():
                return jsonify({"error": "Este pedido ya tiene un comprobante registrado"}), 400

        # BLINDAJE: Lógica de actualización para categorías (1 imagen por categoría)
        if tipo == 'categoria':
            cat_id = data.get('categoria_id')
            if not cat_id:
                return jsonify({"error": "categoria_id es requerido para este tipo"}), 400
            
            existente = Multimedia.query.filter_by(tipo='categoria', categoria_id=cat_id).first()
            if existente:
                existente.url = url
                db.session.commit()
                return jsonify({"message": "Imagen de categoría actualizada", "multimedia": existente.to_dict()})

        nueva_multimedia = Multimedia(
            url=url, 
            tipo=tipo, 
            categoria_id=data.get('categoria_id'), 
            pedido_id=data.get('pedido_id')
        )
        db.session.add(nueva_multimedia)
        db.session.commit()
        return jsonify(nueva_multimedia.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error de servidor: {str(e)}"}), 500

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