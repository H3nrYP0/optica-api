import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. Configuración CORS
    CORS(app,
        origins=[
            "http://localhost:5173",
            "http://localhost:3000",
            os.getenv('FRONTEND_URL', '*')
        ],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Cache-Control"],
        supports_credentials=True
    )

    # 2. Base de Datos
    from app.database import init_db, db
    init_db(app)

    # 3. Autenticación (JWT)
    from app.auth import init_auth
    init_auth(app)

    # 4. Registro de Blueprints
    from app.routes import main_bp
    from app.auth.routes import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # 5. Middleware Global de Autenticación
    @app.before_request
    def verificar_autenticacion():
        if request.method == 'OPTIONS':
            return None

        # ================================================================
        # RUTAS PÚBLICAS — accesibles sin token (landing page + auth)
        # Formato: 'blueprint.nombre_funcion'
        # ================================================================
        RUTAS_PUBLICAS = {
            # Auth
            'auth.login',
            'auth.register',
            'auth.verify_register',
            'auth.forgot_password',
            'auth.reset_password',

            # Clientes (registro público desde landing)
            'main.get_clientes_publico',
            'main.create_cliente_publico',

            # Catálogo público (landing page)
            'main.get_productos',
            'main.get_categorias',
            'main.get_marcas',
            'main.get_servicios',

            # Imágenes públicas
            'main.get_imagenes',
            'main.get_imagen',
            'main.get_imagenes_por_producto',
            'main.get_imagen_producto',          # alias si existe

            # Multimedia pública (imágenes de categorías)
            'main.obtener_comprobante_pedido',    # usado en landing para ver estado pedido

            # Estados de cita (necesario para agendar cita desde landing)
            'main.get_estados_cita',

            # Disponibilidad (agendar cita desde landing)
            'main.verificar_disponibilidad',
            'main.verificar_disponibilidad_multiple',

            # Utilidades
            'static',
            'main.home',
            'main.get_all_endpoints',
        }

        # Permitir acceso si es pública o si la ruta no existe (Flask maneja el 404)
        if not request.endpoint or request.endpoint in RUTAS_PUBLICAS:
            return None

        # Verificación obligatoria de JWT para todo lo demás
        from flask_jwt_extended import verify_jwt_in_request
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({
                "success": False,
                "error": "Token requerido",
                "message": "Debes iniciar sesión para acceder a este recurso"
            }), 401

    # 6. Verificación de DB al arrancar
    with app.app_context():
        try:
            db.create_all()
            print("✅ Estructura de base de datos verificada.")
        except Exception as e:
            print(f"❌ Error al conectar con la base de datos: {e}")

    return app