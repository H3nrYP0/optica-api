from flask import Blueprint, jsonify
from app.models import Producto, Cliente, Venta # Importación limpia

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    # Esta es la ruta que evita el 404 en la URL principal
    return jsonify({
        "message": "API Óptica - Sistema V4",
        "status": "Online",
        "version": "3.1"
    }), 200