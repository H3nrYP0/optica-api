import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config

def create_app():
    # ============================================================
    # 1. CREAR LA APLICACIÓN FLASK
    # ============================================================
    app = Flask(__name__)
    app.config.from_object(Config)

    # ============================================================
    # 2. CONFIGURACIÓN CORS
    # ============================================================
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

    # ============================================================
    # 3. CONFIGURACIÓN DE BASE DE DATOS
    # ============================================================
    from app.database import init_db, db
    init_db(app)

    # ============================================================
    # 4. CONFIGURACIÓN DE AUTENTICACIÓN (JWT)
    # ============================================================
    from app.auth import init_auth
    init_auth(app)

    # ============================================================
    # 5. REGISTRO DE BLUEPRINTS
    # ============================================================
    from app.routes import main_bp
    from app.auth.routes import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # ============================================================
    # 6. MIDDLEWARE GLOBAL
    # ============================================================
    RUTAS_PUBLICAS = {
        'auth.login',
        'auth.register',
        'auth.verify_register',
        'auth.forgot_password',
        'auth.reset_password',
        'static',
        'get_clientes_publico',
        'create_cliente_publico',
        'update_cliente_publico',
        'delete_cliente_publico',
    }

    @app.before_request
    def verificar_autenticacion():
        # ✅ FIX CORS: las peticiones OPTIONS (preflight) SIEMPRE deben pasar
        # sin verificar token — si las bloqueamos, el navegador rechaza la conexión
        if request.method == 'OPTIONS':
            return None

        # Mantén esto en None mientras desarrollas.
        # Cuando actives la autenticación, elimina el return None de abajo
        # y descomenta el bloque original.
        return None

        # ========== ACTIVAR EN PRODUCCIÓN ==========
        # if request.endpoint in RUTAS_PUBLICAS:
        #     return None
        #
        # from flask_jwt_extended import verify_jwt_in_request
        # try:
        #     verify_jwt_in_request()
        # except Exception:
        #     return jsonify({
        #         "success": False,
        #         "error": "Token requerido o inválido",
        #         "message": "Debes iniciar sesión para acceder a este recurso"
        #     }), 401
        # ============================================

    # ============================================================
    # 7. VERIFICAR BASE DE DATOS AL ARRANCAR
    # ============================================================
    with app.app_context():
        try:
            db.create_all()
            print("✅ Estructura de base de datos verificada.")
            from app.Models.models import Empleado
            count = Empleado.query.count()
            print(f"✅ Conexión exitosa. Empleados registrados: {count}")
        except Exception as e:
            print(f"❌ Error al verificar la base de datos: {e}")

    return app