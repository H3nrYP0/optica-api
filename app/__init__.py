"""
Fábrica de la aplicación Flask.
- Configura CORS
- Inicializa BD
- Inicializa autenticación (JWT callbacks)
- Registra blueprints
- Middleware before_request: solo carga usuario desde token
- Manejadores de errores globales
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS
    CORS(app,
        origins=[
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost:5500",
            os.getenv('FRONTEND_URL', '*')
        ],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Cache-Control"],
        supports_credentials=True
    )

    # Base de datos
    from app.database import init_db, db
    init_db(app)

    # Autenticación (JWT callbacks)
    from app.auth import init_auth
    init_auth(app)

    # Blueprints
    from app.routes import main_bp
    from app.auth.routes import auth_bp
    from app.routes.verificar_comprobante import comprobante_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(comprobante_bp)
    # Middleware: solo carga de usuario
    from app.middleware import cargar_usuario_desde_token

    @app.before_request
    def before_request():
        cargar_usuario_desde_token()
        # No hay más lógica de autorización aquí. Eso se hace en decoradores.

    # Manejadores de error
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": "Recurso no encontrado",
            "message": "La ruta solicitada no existe"
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": "Método no permitido",
            "message": "El método HTTP no está permitido para esta ruta"
        }), 405

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "success": False,
            "error": "Error interno del servidor",
            "message": "Ocurrió un error inesperado. Intenta de nuevo más tarde"
        }), 500

    with app.app_context():
        try:
            db.create_all()
            print("✅ Base de datos conectada y estructura verificada")
        except Exception as e:
            print(f"⚠️ Error al conectar con la base de datos: {e}")

    return app